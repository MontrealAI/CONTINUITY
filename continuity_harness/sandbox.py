"""Linux x86-64 syscall confinement for a pipe-only candidate process.

This stacks a seccomp filter after imports and descriptor closure.  It changes
no user account, credential, file mode or host access policy.  The trusted host
and controller are outside the threat model.  Unsupported hosts fail closed.
"""

import ctypes
import errno
import os
import platform
import socket
import sys


class SockFilter(ctypes.Structure):
    _fields_ = [("code", ctypes.c_ushort), ("jt", ctypes.c_ubyte),
                ("jf", ctypes.c_ubyte), ("k", ctypes.c_uint)]


class SockFprog(ctypes.Structure):
    _fields_ = [("length", ctypes.c_ushort), ("filters", ctypes.POINTER(SockFilter))]


# Linux x86-64 UAPI syscall numbers.  There is deliberately no open/openat,
# stat-by-path, exec, clone/fork, ptrace, process_vm_readv, socket or connect.
ALLOWED = (0, 1, 3, 5, 8, 9, 10, 11, 12, 13, 14, 15, 16, 19, 20, 24,
           25, 28, 39, 60, 96, 99, 102, 104, 107, 108, 110, 186, 202,
           204, 228, 231, 318)


def activate(authority_probe, workspace_probe):
    """Return observed confinement, or raise OSError before candidate actions."""
    if sys.platform != "linux" or platform.machine() != "x86_64":
        raise OSError(errno.ENOSYS, "SECCOMP_PLATFORM_UNSUPPORTED")
    libc = ctypes.CDLL(None, use_errno=True)
    # Create the program before closing descriptors and installing restrictions.
    instructions = [SockFilter(0x20, 0, 0, 4),
                    SockFilter(0x15, 1, 0, 0xC000003E),
                    SockFilter(0x06, 0, 0, 0x80000000),
                    SockFilter(0x20, 0, 0, 0)]
    for nr in ALLOWED:
        instructions.extend([SockFilter(0x15, 0, 1, nr),
                             SockFilter(0x06, 0, 0, 0x7FFF0000)])
    instructions.append(SockFilter(0x06, 0, 0, 0x00050000 | errno.EPERM))
    array = (SockFilter * len(instructions))(*instructions)
    program = SockFprog(len(array), array)
    os.closerange(3, 65536)
    if libc.prctl(38, 1, 0, 0, 0) != 0:
        raise OSError(ctypes.get_errno(), "NO_NEW_PRIVILEGES_UNAVAILABLE")
    if libc.prctl(22, 2, ctypes.byref(program), 0, 0) != 0:
        raise OSError(ctypes.get_errno(), "SECCOMP_UNAVAILABLE")
    probes = {}
    for label, path in (("authority_open_denied", authority_probe),
                        ("workspace_open_denied", workspace_probe)):
        try:
            fd = os.open(path, os.O_RDONLY)
            os.close(fd)
            probes[label] = False
        except OSError as error:
            probes[label] = error.errno == errno.EPERM
    try:
        connection = socket.socket()
        connection.close()
        probes["network_denied"] = False
    except OSError as error:
        probes["network_denied"] = error.errno == errno.EPERM
    try:
        child = os.fork()
        if child == 0:
            os._exit(99)
        probes["spawn_denied"] = False
    except OSError as error:
        probes["spawn_denied"] = error.errno == errno.EPERM
    ctypes.set_errno(0)
    result = libc.syscall(310, os.getppid(), 0, 0, 0, 0, 0)
    probes["process_inspection_denied"] = result == -1 and ctypes.get_errno() == errno.EPERM
    if not all(probes.values()):
        raise OSError(errno.EPERM, "ISOLATION_PROBE_FAILED")
    return {"mechanism": "SECCOMP_BPF", "applied": True, "probe": probes}
