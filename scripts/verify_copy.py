#!/usr/bin/env python3
"""Verify the initial copied-file inventory; not an operational qualification."""
import hashlib
import json
from pathlib import Path

root = Path(__file__).resolve().parents[1]
manifest = json.loads((root / 'PROVENANCE.json').read_text())
for name, expected in manifest['files'].items():
    path = root / name
    assert path.is_file() and not path.is_symlink(), name
    data = path.read_bytes()
    assert len(data) == expected['bytes'], name
    assert hashlib.sha256(data).hexdigest() == expected['sha256'], name
    assert hashlib.sha1(b'blob ' + str(len(data)).encode() + b'\0' + data).hexdigest() == expected['git_blob'], name
print(f"Verified {len(manifest['files'])} unchanged copied files.")
