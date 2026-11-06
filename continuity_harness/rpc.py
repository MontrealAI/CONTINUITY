"""Bounded, observable subprocess RPC; no sleep-based synchronization."""

import os
from pathlib import Path
import selectors
import subprocess
import sys
import time

from .schema import canonical, strict_loads, HarnessError, MAX_JSON_BYTES


class ProcessChannel:
    def __init__(self, command, cwd, stderr_path, timeout_ms=10000):
        self.stderr_file = open(stderr_path, "ab", buffering=0)
        env = {k: v for k, v in os.environ.items() if k in ("PATH", "LANG", "LC_ALL", "SYSTEMROOT")}
        env.update({"PYTHONUNBUFFERED": "1", "PYTHONDONTWRITEBYTECODE": "1"})
        self.process = subprocess.Popen(command, cwd=cwd, stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                                        stderr=self.stderr_file, env=env, close_fds=True, bufsize=0)
        self.selector = selectors.DefaultSelector()
        self.selector.register(self.process.stdout, selectors.EVENT_READ)
        os.set_blocking(self.process.stdin.fileno(), False)
        self.buffer = bytearray()
        self.timeout_ms = timeout_ms

    def send(self, value):
        raw = canonical(value) + b"\n"
        deadline = time.monotonic_ns() + self.timeout_ms * 1_000_000
        writer = selectors.DefaultSelector()
        writer.register(self.process.stdin, selectors.EVENT_WRITE)
        try:
            position = 0
            while position < len(raw):
                remaining = deadline - time.monotonic_ns()
                if remaining <= 0 or not writer.select(remaining / 1_000_000_000):
                    raise HarnessError("PROCESS_WRITE_TIMEOUT", str(self.process.pid))
                try:
                    written = os.write(self.process.stdin.fileno(), raw[position:position + 65536])
                except BlockingIOError:
                    continue
                if written <= 0:
                    raise HarnessError("PROCESS_PIPE_CLOSED", str(self.process.pid))
                position += written
        except (BrokenPipeError, OSError) as error:
            raise HarnessError("PROCESS_PIPE_CLOSED", str(self.process.pid)) from error
        finally:
            writer.close()

    def receive(self):
        deadline = time.monotonic_ns() + self.timeout_ms * 1_000_000
        while b"\n" not in self.buffer:
            remaining = deadline - time.monotonic_ns()
            if remaining <= 0:
                raise HarnessError("PROCESS_TIMEOUT", str(self.process.pid))
            if not self.selector.select(remaining / 1_000_000_000):
                raise HarnessError("PROCESS_TIMEOUT", str(self.process.pid))
            chunk = os.read(self.process.stdout.fileno(), 65536)
            if not chunk:
                raise HarnessError("PROCESS_EXITED", f"pid={self.process.pid};exit={self.process.poll()}")
            self.buffer.extend(chunk)
            if len(self.buffer) > MAX_JSON_BYTES:
                raise HarnessError("JSON_TOO_LARGE", "process response")
        line, _, rest = self.buffer.partition(b"\n")
        self.buffer = bytearray(rest)
        value = strict_loads(bytes(line))
        if type(value) is not dict:
            raise HarnessError("RPC_FRAME_INVALID", "JSON object required")
        return value

    def kill(self):
        if self.process.poll() is None:
            self.process.kill()
        self.process.wait(timeout=5)

    def close(self):
        try:
            if self.process.stdin:
                self.process.stdin.close()
            if self.process.poll() is None:
                try:
                    self.process.wait(timeout=2)
                except subprocess.TimeoutExpired:
                    self.kill()
        finally:
            self.selector.close()
            if self.process.stdout:
                self.process.stdout.close()
            self.stderr_file.close()


class ServiceClient(ProcessChannel):
    def __init__(self, root, db, artifacts, stderr_path):
        super().__init__([sys.executable, "-m", "continuity_harness.service", "--db", str(db),
                          "--artifacts", str(artifacts)], root, stderr_path)
        self.counter = 0

    def start_request(self, op, args, hooks=None):
        self.counter += 1
        rid = f"request-{self.counter}"
        message = {"id": rid, "op": op, "args": args}
        if hooks:
            message["hooks"] = hooks
        self.send(message)
        return rid

    def call(self, op, args=None, hooks=None, on_hook=None):
        rid = self.start_request(op, args or {}, hooks)
        while True:
            result = self.receive()
            if result.get("id") != rid:
                raise HarnessError("RPC_ID_MISMATCH", rid)
            if result.get("event") == "hook":
                if on_hook:
                    on_hook(result)
                self.send({"continue": True})
                continue
            return result
