"""Preservation and navigation tests for the supplied bilingual collection."""
import importlib.util
import shutil
import hashlib
from unittest import mock
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location('verify_masterclass', ROOT / 'scripts/verify_masterclass.py')
VERIFY = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(VERIFY)
RESTORE_SPEC = importlib.util.spec_from_file_location(
    "restore_masterclass", ROOT / "scripts/restore_masterclass_archive.py")
RESTORE = importlib.util.module_from_spec(RESTORE_SPEC)
RESTORE_SPEC.loader.exec_module(RESTORE)


class MasterClassDocumentsTests(unittest.TestCase):
    def test_supplied_collection_matches_archive_and_manifests(self):
        result = VERIFY.verify(ROOT / 'docs/masterclass-101')
        self.assertEqual(result['files'], 164)
        self.assertEqual(result['source_checksums'], 163)
        self.assertEqual(result['reader_references'], 3)
        self.assertEqual(result['sources'], 40)
        self.assertGreaterEqual(result['dynamic_references'], 60)
        self.assertEqual(result['archive_sha256'], 'c07b3256e8f5f07a953b98b8299efeae0f21fb85e511614910b9b29cece461b2')

    def test_language_catalogues_and_current_status_are_separate_from_payload(self):
        for name in ('README.md', 'README.fr.md'):
            text = (ROOT / 'docs/masterclass-101' / name).read_text()
            for required in ('108', '73', '24', 'JSON', 'STATUS.md#', 'verify_masterclass.py --language'):
                self.assertIn(required, text)
        status = (ROOT / 'docs/masterclass-101/STATUS.md').read_text()
        for required in ('## English', '## Français', '56aa3e0', 'R1', 'R2', 'plaintext', 'texte clair', 'build_sources.py'):
            self.assertIn(required, status)

    def test_restore_recovers_exact_original_and_refuses_overwrite(self):
        wrapper = ROOT / 'docs/masterclass-101' / (RESTORE.ORIGINAL_NAME + '.xz')
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / 'restored.zip'
            self.assertEqual(RESTORE.restore(wrapper, output), RESTORE.ORIGINAL_SHA256)
            self.assertEqual(output.stat().st_size, RESTORE.ORIGINAL_BYTES)
            self.assertEqual(hashlib.sha256(output.read_bytes()).hexdigest(), RESTORE.ORIGINAL_SHA256)
            with self.assertRaises(FileExistsError):
                RESTORE.restore(wrapper, output)
            self.assertEqual(hashlib.sha256(output.read_bytes()).hexdigest(), RESTORE.ORIGINAL_SHA256)

    def test_restore_rejects_altered_wrapper_before_decompression(self):
        original = (ROOT / 'docs/masterclass-101' / (RESTORE.ORIGINAL_NAME + '.xz')).read_bytes()
        altered = bytes([original[0] ^ 1]) + original[1:]
        with tempfile.TemporaryDirectory() as directory:
            wrapper = Path(directory) / 'bad.xz'
            output = Path(directory) / 'output.zip'
            for data in (original[:-1], altered):
                with self.subTest(size=len(data)):
                    wrapper.write_bytes(data)
                    with mock.patch.object(RESTORE.lzma, 'decompress') as decompress:
                        with self.assertRaisesRegex(ValueError, 'Wrapper identity differs'):
                            RESTORE.restore(wrapper, output)
                        decompress.assert_not_called()
                    self.assertFalse(output.exists())

    def test_restore_rejects_wrong_decoded_original_without_writing_output(self):
        wrapper = ROOT / 'docs/masterclass-101' / (RESTORE.ORIGINAL_NAME + '.xz')
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / 'output.zip'
            with mock.patch.object(RESTORE.lzma, 'decompress', return_value=b'not the original archive'):
                with self.assertRaisesRegex(ValueError, 'Original ZIP identity differs'):
                    RESTORE.restore(wrapper, output)
            self.assertFalse(output.exists())

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
        source = ROOT / 'docs/masterclass-101'
        with tempfile.TemporaryDirectory() as directory:
            copy = Path(directory) / 'collection'
            shutil.copytree(source, copy)
            target = copy / 'edition-1/START_HERE.txt'
            original = target.read_bytes()
            target.write_bytes(original + b'changed')
            with self.assertRaisesRegex(ValueError, 'File identity differs'):
                VERIFY.verify(copy)
            target.unlink()
            with self.assertRaisesRegex(ValueError, 'inventory differs'):
                VERIFY.verify(copy)
            target.write_bytes(original)
            extra = copy / 'edition-1/unexpected.txt'
            extra.write_text('unexpected')
            with self.assertRaisesRegex(ValueError, 'inventory differs'):
                VERIFY.verify(copy)
            extra.unlink()
            archive = copy / 'CONTINUITY_OMEGA_MasterClass_101_Complete_Bilingual.zip.xz'
            with archive.open('ab') as stream:
                stream.write(b'changed')
            with self.assertRaisesRegex(ValueError, 'Wrapper identity differs'):
                VERIFY.verify(copy)


if __name__ == '__main__':
    unittest.main()
