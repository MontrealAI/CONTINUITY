"""Bilingual entry-point and relative-link regression checks."""
import importlib.util
import re
import unittest
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import unquote, urlsplit

ROOT = Path(__file__).resolve().parents[1]


class HTMLReferences(HTMLParser):
    def __init__(self):
        super().__init__()
        self.links = []
        self.ids = set()
        self.language = None

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if tag == 'html': self.language = a.get('lang')
        if a.get('id'): self.ids.add(a['id'])
        for key in ('href', 'src', 'data'):
            if a.get(key): self.links.append(a[key])


class BilingualRepositoryTests(unittest.TestCase):
    def test_main_readme_contains_both_complete_paths(self):
        text = (ROOT / 'README.md').read_text()
        en, fr = text.split('## Français', 1)
        self.assertIn('## English', en)
        for section in ('Start here', 'Run locally', 'Copy and publication boundary', 'Complete language paths'):
            self.assertIn(section, en)
        for section in ('Commencer', 'Exécution locale', 'Périmètre de la copie', 'Parcours linguistiques complets'):
            self.assertIn(section, fr)
        self.assertIn('--language en', en)
        self.assertIn('--language fr', fr)

    def test_guides_have_complete_language_pairs(self):
        for relative in ('README', 'docs/BILINGUAL_CLI', 'docs/RESEARCH_TOOLS',
                         'docs/continuity-omega/README', 'docs/continuity-omega/QUICKSTART',
                         'docs/continuity-omega/OUTPUTS', 'docs/continuity-omega/REAL_PILOT',
                         'docs/continuity-omega-paper/README', 'docs/continuity-omega-paper/EVIDENCE',
                         'docs/continuity-omega-paper/REVIEW', 'docs/continuity-omega-paper/SOURCE_MAP'):
            for suffix in ('.md', '.fr.md'):
                self.assertGreater(len((ROOT / (relative + suffix)).read_text()), 300)
        for relative in ('MIGRATION.md', 'BILINGUALITY.md', 'docs/continuity-omega-paper/TRANSLATION.md',
                         'docs/continuity-omega-paper/RELEASE_NOTES.md', 'docs/continuity-omega/READING_RELEASE.md'):
            text = (ROOT / relative).read_text()
            self.assertIn('## English', text)
            self.assertIn('## Français', text)

    def test_all_markdown_relative_file_links_resolve(self):
        # These byte-preserved source snapshots retain relative links from their
        # original pinned repository paths. They are archival records, not local
        # navigation pages; test_document_collection verifies their exact bytes.
        snapshots = ROOT / 'docs/collection/edition-2/05_Repository_Snapshot'
        for page in ROOT.rglob('*.md'):
            if '.git' in page.parts: continue
            if page.is_relative_to(snapshots): continue
            for href in re.findall(r'\]\(([^)]+)\)', page.read_text()):
                target = urlsplit(href)
                if target.scheme or target.netloc or not target.path: continue
                self.assertTrue((page.parent / unquote(target.path)).exists(), (str(page), href))

    def test_local_html_languages_and_links(self):
        pages = list((ROOT / 'docs/research').glob('*.html'))
        self.assertGreaterEqual(len(pages), 8)
        for page in pages:
            parser = HTMLReferences(); parser.feed(page.read_text())
            self.assertIn(parser.language, ('en', 'fr', 'fr-CA'), str(page))
            for href in parser.links:
                target = urlsplit(href)
                if target.scheme or target.netloc: continue
                destination = page.parent / unquote(target.path) if target.path else page
                self.assertTrue(destination.exists(), (str(page), href))
                if target.fragment and destination.suffix == '.html':
                    other = HTMLReferences(); other.feed(destination.read_text())
                    self.assertIn(unquote(target.fragment), other.ids, (str(page), href))

    def test_original_and_localized_identities(self):
        spec = importlib.util.spec_from_file_location('verify_copy', ROOT / 'scripts/verify_copy.py')
        module = importlib.util.module_from_spec(spec); spec.loader.exec_module(module)
        unchanged, localized = module.verify(ROOT)
        self.assertEqual(unchanged + localized, 78)
        self.assertLessEqual(localized, 4)


if __name__ == '__main__': unittest.main()
