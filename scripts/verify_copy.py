#!/usr/bin/env python3
"""Verify original identities and documented localization overlays. / Vérifier la provenance."""
import hashlib
import json
from pathlib import Path


def verify(root):
    manifest = json.loads((root / 'PROVENANCE.json').read_text())
    overlay = json.loads((root / 'LOCALIZATION.json').read_text())['files']
    if not set(overlay) <= set(manifest['files']):
        raise ValueError('Unknown overlay / Adaptation inconnue')
    for name, original in manifest['files'].items():
        expected = original
        if name in overlay:
            record = overlay[name]
            if not name.startswith('docs/research/') or not name.endswith('.html'):
                raise ValueError('Only website HTML may be adapted / Seul le HTML du site peut être adapté')
            if record['original_sha256'] != original['sha256']:
                raise ValueError('Historical identity changed / Identité historique modifiée')
            expected = record['current']
        path = root / name
        if not path.is_file() or path.is_symlink():
            raise ValueError('Missing regular file / Fichier ordinaire absent: ' + name)
        data = path.read_bytes()
        actual = {'bytes': len(data), 'sha256': hashlib.sha256(data).hexdigest(),
                  'git_blob': hashlib.sha1(b'blob ' + str(len(data)).encode() + b'\0' + data).hexdigest()}
        if actual != expected:
            raise ValueError('Identity mismatch / Empreinte différente: ' + name)
    return len(manifest['files']) - len(overlay), len(overlay)


if __name__ == '__main__':
    try:
        original, localized = verify(Path(__file__).resolve().parents[1])
    except (ValueError, OSError, KeyError) as error:
        raise SystemExit('Copy verification failed / Échec de vérification: ' + str(error))
    print(f'Verified {original} unchanged files and {localized} documented website adaptations. / '
          f'{original} fichiers inchangés et {localized} adaptations web documentées vérifiés.')
