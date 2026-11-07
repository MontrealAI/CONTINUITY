#!/usr/bin/env python3
"""Verify preserved MasterClass edition 1.0 bytes and reader links without executing documents."""
import argparse
import hashlib
import json
import io
import lzma
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
    if manifest['schema_version'] != 1 or manifest['edition'] != '1.0':
        raise ValueError('Unsupported edition / Édition non prise en charge')
    payload = safe_path(collection, manifest['payload_directory'])
    files = manifest['files']
    if manifest['file_count'] != 164 or len(files) != 164:
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
    for line in (payload / 'SHA256SUMS.txt').read_text(encoding='utf-8').splitlines():
        expected_hash, name = line.split('  ', 1)
        if name in source_checksums or not re.fullmatch(r'[a-f0-9]{64}', expected_hash):
            raise ValueError('Invalid source checksums / Empreintes sources invalides')
        source_checksums[name] = expected_hash
        if digest(safe_path(payload, name).read_bytes()) != expected_hash:
            raise ValueError('Source checksum differs / Empreinte source différente: ' + name)
    if set(source_checksums) != set(files) - {'SHA256SUMS.txt'}:
        raise ValueError('Source checksum coverage differs / Couverture des empreintes différente')

    source = manifest['source_archive']
    archive = safe_path(collection, source['path'])
    stored = archive.read_bytes()
    wrapper = source['stored_wrapper']
    if wrapper['format'] != 'xz' or len(stored) != wrapper['bytes'] or digest(stored) != wrapper['sha256']:
        raise ValueError('Wrapper identity differs / Identité de l’enveloppe différente')
    data = lzma.decompress(stored)
    if len(data) != source['bytes'] or digest(data) != source['sha256']:
        raise ValueError('Archive identity differs / Identité de l’archive différente')
    if source['root'] != 'CONTINUITY_OMEGA_MasterClass_101/':
        raise ValueError('Archive root differs / Racine de l’archive différente')
    with zipfile.ZipFile(io.BytesIO(data)) as zipped:
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

    index = json.loads((payload / 'PACKAGE_INDEX.json').read_text(encoding='utf-8'))
    if index['edition'] != '1.0' or set(index['languages']) != {'en', 'fr'}:
        raise ValueError('Course edition/languages differ / Édition ou langues différentes')
    indexed = {item['path']: item['bytes'] for item in index['files']}
    if len(indexed) != len(index['files']) or set(indexed) != set(files) - {'PACKAGE_INDEX.json', 'SHA256SUMS.txt'}:
        raise ValueError('Index coverage differs / Couverture de l’index différente')
    for name, size in indexed.items():
        if safe_path(payload, name).stat().st_size != size:
            raise ValueError('Indexed size differs / Taille indexée différente: ' + name)
    if {x['lang'] for x in index['complete_courses']} != {'en', 'fr'}:
        raise ValueError('Missing complete course / Cours complet absent')
    for item in index['complete_courses']:
        if not safe_path(payload, item['path']).is_file() or item['pages'] != 73:
            raise ValueError('Invalid complete course / Cours complet invalide')
    sources = json.loads((payload / 'SOURCE_REGISTER.json').read_text(encoding='utf-8'))
    for key, record in sources.items():
        if digest(safe_path(payload, record['archive_path']).read_bytes()) != record['sha256']:
            raise ValueError('Source identity differs / Identité source différente: ' + key)
    spec = json.loads((payload / '04_Editable_Sources/course_spec.json').read_text(encoding='utf-8'))
    if sum(x['minutes'] for x in spec['schedule']) != 180:
        raise ValueError('Schedule differs / Horaire différent')
    lessons = {f'L{x}' for x in range(1, 9)}
    if {x['id'] for x in spec['schedule']} != lessons | {'O', 'B'}:
        raise ValueError('Lesson coverage differs / Couverture des leçons différente')
    for kind in ('learner', 'workbook', 'facilitator', 'quick_reference'):
        documents = [json.loads((payload / f'04_Editable_Sources/{kind}_{lang}.json').read_text(encoding='utf-8')) for lang in ('en', 'fr')]
        if [p['id'] for p in documents[0]['pages']] != [p['id'] for p in documents[1]['pages']]:
            raise ValueError('Bilingual page identity differs / Identité bilingue différente')
        if kind == 'learner' and not lessons <= {p['lesson'] for p in documents[0]['pages']}:
            raise ValueError('Missing learning lesson / Leçon absente')
    quiz = json.loads((payload / '04_Editable_Sources/quiz.json').read_text(encoding='utf-8'))
    if {q['id'] for q in quiz} != {f'Q{x:02}' for x in range(1, 13)} or len(quiz) != 12:
        raise ValueError('Quiz coverage differs / Questionnaire incomplet')
    for question in quiz:
        for lang in ('en', 'fr'):
            if not question['question'][lang] or not question['explanation'][lang] or not 0 <= question['correct_index'] < len(question['options'][lang]):
                raise ValueError('Invalid quiz answer / Réponse invalide')
    slides = json.loads((payload / '04_Editable_Sources/slides.json').read_text(encoding='utf-8'))
    if len(slides) != 24:
        raise ValueError('Slide count differs / Nombre de diapositives différent')
    case = spec['case']
    costs = sum(row['cost'] for row in case['cost_rows'])
    before = sum(row['cost'] for row in case['cost_rows'] if row['paid'] == 'before acceptance')
    funded = case['funded_extension']
    if not (costs == case['complete_modeled_cost'] == 5000
            and before == case['preacceptance_outflows'] == 4700
            and case['service_fee'] - costs == case['projected_contribution'] == 600
            and before - case['starting_uncommitted_cash'] == case['initial_funding_gap'] == 3500
            and funded['buyer_advance_received'] + funded['balance_received_after_acceptance'] == case['service_fee'] == 5600
            and case['starting_uncommitted_cash'] + case['service_fee'] - costs == funded['ending_cash_after_all_costs'] == 1800
            and case['starting_record'] + case['approved_amendment'] == case['available_capacity'] == 10000
            and case['total_alternate_capacity'] - case['protected_existing_work'] == case['available_capacity']):
        raise ValueError('Teaching arithmetic differs / Arithmétique pédagogique différente')

    reader = payload / 'START_HERE.html'
    parser = References()
    parser.feed(reader.read_text(encoding='utf-8'))
    check_links(reader, payload, parser.links)
    embedded = re.search(r'<script type="application/json" id="course-data">(.*?)</script>', reader.read_text(encoding='utf-8'), re.S)
    if not embedded:
        raise ValueError('Missing reader data / Données du lecteur absentes')
    course = json.loads(embedded.group(1))
    dynamic_links = []
    for lang in ('en', 'fr'):
        for formats in course['files'][lang].values():
            dynamic_links.extend(formats.values())
        for kind in ('learner', 'workbook', 'facilitator', 'quick_reference'):
            expected = json.loads((payload / f'04_Editable_Sources/{kind}_{lang}.json').read_text(encoding='utf-8'))
            if course[kind][lang] != expected:
                raise ValueError('Embedded course differs / Contenu intégré différent')
    for source in course['sources'].values():
        if source.get('archive_path'):
            dynamic_links.append(source['archive_path'])
        elif source.get('local_path', '').startswith('continuity_masterclass/research/'):
            dynamic_links.append('05_Source_Evidence/' + source['local_path'][len('continuity_masterclass/research/'):])
    for lang in ('en', 'fr'):
        for kind in ('learner', 'workbook', 'facilitator', 'quick_reference'):
            for page in course[kind][lang]['pages']:
                for block in page['blocks']:
                    if block['type'] == 'figure':
                        dynamic_links.append(f"06_Visuals/{block['name']}_{lang}.svg")
    check_links(reader, payload, dynamic_links)

    for page in (payload / '04_Editable_Sources').glob('*.md'):
        check_links(page, payload, re.findall(r'\]\(([^)]+)\)', page.read_text(encoding='utf-8')))
    return {'files': len(files), 'source_checksums': len(source_checksums),
            'reader_references': len(parser.links), 'archive_sha256': digest(data), 'sources': len(sources), 'dynamic_references': len(dynamic_links)}


def main():
    parser = argparse.ArgumentParser(description='Verify preserved MasterClass / Vérifier la masterclass conservée')
    parser.add_argument('--language', choices=('en', 'fr'), default='en',
                        help='Summary language / Langue du résumé')
    args = parser.parse_args()
    try:
        result = verify(Path(__file__).resolve().parents[1] / 'docs/masterclass-101')
    except (ValueError, OSError, KeyError, TypeError, lzma.LZMAError, zipfile.BadZipFile) as error:
        parser.exit(1, 'MasterClass verification failed / Échec de vérification: ' + str(error) + '\n')
    print((f"Masterclass vérifiée : {result['files']} fichiers inchangés, "
           f"{result['source_checksums']} empreintes sources, {result['reader_references']} références HTML et {result['dynamic_references']} références dynamiques."
           if args.language == 'fr' else
           f"MasterClass verified: {result['files']} unchanged files, "
           f"{result['source_checksums']} source checksums, {result['reader_references']} HTML and {result['dynamic_references']} dynamic references."))


if __name__ == '__main__':
    main()
