"""Preservation and navigation tests for the supplied bilingual collection."""
import importlib.util
import shutil
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location('verify_collection', ROOT / 'scripts/verify_collection.py')
VERIFY = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(VERIFY)


class DocumentCollectionTests(unittest.TestCase):
    def test_supplied_collection_matches_archive_and_manifests(self):
        result = VERIFY.verify(ROOT / 'docs/collection')
        self.assertEqual(result['files'], 106)
        self.assertEqual(result['source_checksums'], 105)
        self.assertEqual(result['reader_references'], 100)
        self.assertEqual(result['archive_sha256'], '52272efc6e986bb052be29d22d2ed945e9cd80aec7d30837b7d42fe6d3ec2f58')

    def test_language_catalogues_and_current_status_are_separate_from_payload(self):
        for name in ('README.md', 'README.fr.md'):
            text = (ROOT / 'docs/collection' / name).read_text()
            for volume in ('01_', '02_', '03_', '04_', '05_'):
                self.assertIn(volume, text)
            self.assertIn('STATUS.md#', text)
            self.assertIn('verify_collection.py --language', text)
        status = (ROOT / 'docs/collection/STATUS.md').read_text()
        for required in ('## English', '## Français', '396227d8', '56aa3e0', 'pull/3', 'pull/4',
                         '../economy/REVIEW_REPAIR.md', '../economy/REVIEW_REPAIR.fr.md'):
            self.assertIn(required, status)

    def test_unsafe_paths_and_symlinks_are_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            for value in ('../x', '/tmp/x', 'a/../../x', 'a\\b', './x', 'a//b', ''):
                with self.subTest(value=value), self.assertRaises(ValueError):
                    VERIFY.safe_path(root, value)
            (root / 'alias').symlink_to(root, target_is_directory=True)
            with self.assertRaises(ValueError):
                VERIFY.safe_path(root, 'alias/x')

    def test_missing_link_and_anchor_are_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            page = root / 'index.html'
            page.write_text('<div id="known"></div>')
            VERIFY.check_links(page, root, ['#known', 'https://example.org/'])
            for value in ('missing.pdf', '#unknown', '../outside'):
                with self.subTest(value=value), self.assertRaises(ValueError):
                    VERIFY.check_links(page, root, [value])

    def test_changed_missing_added_payload_and_archive_are_rejected(self):
        source = ROOT / 'docs/collection'
        with tempfile.TemporaryDirectory() as directory:
            copy = Path(directory) / 'collection'
            shutil.copytree(source, copy)
            target = copy / 'edition-2/START_HERE.txt'
            original = target.read_bytes()
            target.write_bytes(original + b'changed')
            with self.assertRaisesRegex(ValueError, 'File identity differs'):
                VERIFY.verify(copy)
            target.unlink()
            with self.assertRaisesRegex(ValueError, 'inventory differs'):
                VERIFY.verify(copy)
            target.write_bytes(original)
            extra = copy / 'edition-2/unexpected.txt'
            extra.write_text('unexpected')
            with self.assertRaisesRegex(ValueError, 'inventory differs'):
                VERIFY.verify(copy)
            extra.unlink()
            archive = copy / 'CONTINUITY_OMEGA_Complete_Bilingual_Collection.zip'
            with archive.open('ab') as stream:
                stream.write(b'changed')
            with self.assertRaisesRegex(ValueError, 'Archive identity differs'):
                VERIFY.verify(copy)


if __name__ == '__main__':
    unittest.main()
