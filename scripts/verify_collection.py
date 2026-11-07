#!/usr/bin/env python3
"""Verify preserved edition 2 bytes and reader links without executing documents."""
import argparse
import hashlib
import json
import re
import stat
import zipfile
from html.parser import HTMLParser
from pathlib import Path, PurePosixPath
from urllib.parse import unquote, urlsplit


class References(HTMLParser):
    def __init__(self):
        super().__init__()
        self.links = []
        self.ids = set()

    def handle_starttag(self, tag, attrs):
        attributes = dict(attrs)
        if attributes.get('id'):
            self.ids.add(attributes['id'])
        for key in ('href', 'src'):
            if attributes.get(key):
                self.links.append(attributes[key])


def safe_path(root, name):
    """Reject traversal, aliases and symlinks, including symlinked parents."""
    path = PurePosixPath(name)
    if not name or '\\' in name or path.is_absolute() or any(
            part in ('', '.', '..') for part in name.split('/')):
        raise ValueError('Unsafe path / Chemin dangereux: ' + name)
    result = root
    for part in path.parts:
        result = result / part
        if result.is_symlink():
            raise ValueError('Symlink / Lien symbolique: ' + name)
    if not result.resolve().is_relative_to(root.resolve()):
        raise ValueError('Escaping path / Chemin hors dossier: ' + name)
    return result


def digest(data):
    return hashlib.sha256(data).hexdigest()


def check_links(page, root, links):
    for href in links:
        parsed = urlsplit(href)
        if parsed.scheme or parsed.netloc:
            continue
        path = page.parent / unquote(parsed.path) if parsed.path else page
        if not path.resolve().is_relative_to(root.resolve()) or not path.exists():
            raise ValueError('Broken local link / Lien local absent: ' + str(page) + ': ' + href)
        if parsed.fragment and path.suffix == '.html':
            target = References()
            target.feed(path.read_text(encoding='utf-8'))
            if unquote(parsed.fragment) not in target.ids:
                raise ValueError('Missing anchor / Ancre absente: ' + href)


def verify(collection):
    collection = Path(collection)
    manifest = json.loads((collection / 'IMPORT_MANIFEST.json').read_text(encoding='utf-8'))
    if manifest['schema_version'] != 1 or manifest['edition'] != '2':
        raise ValueError('Unsupported edition / Édition non prise en charge')
    payload = safe_path(collection, manifest['payload_directory'])
    files = manifest['files']
    if manifest['file_count'] != 106 or len(files) != 106:
        raise ValueError('Incomplete inventory / Inventaire incomplet')
    actual = set()
    for path in payload.rglob('*'):
        if path.is_symlink():
            raise ValueError('Unexpected symlink / Lien symbolique inattendu')
        if path.is_file():
            actual.add(path.relative_to(payload).as_posix())
    if actual != set(files):
        raise ValueError('Payload inventory differs / Inventaire des fichiers différent')
    for name, expected in files.items():
        data = safe_path(payload, name).read_bytes()
        if len(data) != expected['bytes'] or digest(data) != expected['sha256']:
            raise ValueError('File identity differs / Identité du fichier différente: ' + name)

    source_checksums = {}
    for line in (payload / 'CHECKSUMS.sha256').read_text(encoding='utf-8').splitlines():
        expected_hash, name = line.split('  ', 1)
        if name in source_checksums or not re.fullmatch(r'[a-f0-9]{64}', expected_hash):
            raise ValueError('Invalid source checksums / Empreintes sources invalides')
        source_checksums[name] = expected_hash
        if digest(safe_path(payload, name).read_bytes()) != expected_hash:
            raise ValueError('Source checksum differs / Empreinte source différente: ' + name)
    if set(source_checksums) != set(files) - {'CHECKSUMS.sha256'}:
        raise ValueError('Source checksum coverage differs / Couverture des empreintes différente')

    source = manifest['source_archive']
    archive = safe_path(collection, source['path'])
    data = archive.read_bytes()
    if len(data) != source['bytes'] or digest(data) != source['sha256']:
        raise ValueError('Archive identity differs / Identité de l’archive différente')
    if source['root'] != 'CONTINUITY_OMEGA_Collection/':
        raise ValueError('Archive root differs / Racine de l’archive différente')
    with zipfile.ZipFile(archive) as zipped:
        entries = zipped.infolist()
        expected_names = {source['root'] + name for name in files}
        if len(entries) != len(expected_names) or {x.filename for x in entries} != expected_names:
            raise ValueError('Archive inventory differs / Inventaire de l’archive différent')
        for entry in entries:
            safe_path(collection, entry.filename)
            if entry.flag_bits & 1 or stat.S_ISLNK(entry.external_attr >> 16):
                raise ValueError('Unsafe archive member / Fichier archivé dangereux')
            name = entry.filename[len(source['root']):]
            if entry.file_size != files[name]['bytes'] or digest(zipped.read(entry)) != files[name]['sha256']:
                raise ValueError('Archive member differs / Fichier archivé différent: ' + name)

    index = json.loads((payload / 'COLLECTION_INDEX.json').read_text(encoding='utf-8'))
    if {(v['lang'], v['volume']) for v in index['volumes']} != {
            (lang, str(volume).zfill(2)) for lang in ('en', 'fr') for volume in range(1, 6)}:
        raise ValueError('Language/volume coverage differs / Couverture linguistique différente')
    for item in index['volumes']:
        for key in ('pdf', 'docx'):
            if not safe_path(payload, item[key]).is_file():
                raise ValueError('Missing indexed file / Fichier indexé absent')
    if {x['lang'] for x in index['complete_editions']} != {'en', 'fr'}:
        raise ValueError('Missing complete edition / Édition complète absente')
    for item in index['complete_editions']:
        if not safe_path(payload, item['path']).is_file():
            raise ValueError('Missing complete PDF / PDF complet absent')
    sources = json.loads((payload / 'SOURCE_REGISTER.json').read_text(encoding='utf-8'))
    for key in ('C1', 'C2', 'F1', 'F2', 'F3'):
        record = sources[key]
        if digest(safe_path(payload, record['archive_path']).read_bytes()) != record['sha256']:
            raise ValueError('Original paper differs / Article original différent: ' + key)

    reader = payload / 'START_HERE.html'
    parser = References()
    parser.feed(reader.read_text(encoding='utf-8'))
    check_links(reader, payload, parser.links)
    for page in (payload / '04_Editable_Sources').glob('*.md'):
        check_links(page, payload, re.findall(r'\]\(([^)]+)\)', page.read_text(encoding='utf-8')))
    return {'files': len(files), 'source_checksums': len(source_checksums),
            'reader_references': len(parser.links), 'archive_sha256': digest(data)}


def main():
    parser = argparse.ArgumentParser(description='Verify preserved collection / Vérifier la collection conservée')
    parser.add_argument('--language', choices=('en', 'fr'), default='en',
                        help='Summary language / Langue du résumé')
    args = parser.parse_args()
    try:
        result = verify(Path(__file__).resolve().parents[1] / 'docs/collection')
    except (ValueError, OSError, KeyError, TypeError, zipfile.BadZipFile) as error:
        parser.exit(1, 'Collection verification failed / Échec de vérification: ' + str(error) + '\n')
    print((f"Collection vérifiée : {result['files']} fichiers inchangés, "
           f"{result['source_checksums']} empreintes sources, {result['reader_references']} références du lecteur."
           if args.language == 'fr' else
           f"Collection verified: {result['files']} unchanged files, "
           f"{result['source_checksums']} source checksums, {result['reader_references']} reader references."))


if __name__ == '__main__':
    main()
