"""Execute real inline scripts with a small DOM harness, not a browser rendering audit."""
import json
import subprocess
import tempfile
import unittest
from html.parser import HTMLParser
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


class ScriptElements(HTMLParser):
    def __init__(self):
        super().__init__()
        self.elements = []
        self.scripts = []
        self.in_script = False

    def handle_starttag(self, tag, attrs):
        self.elements.append({'tag': tag, 'attrs': dict(attrs)})
        if tag == 'script':
            attributes = dict(attrs)
            self.in_script = attributes.get('type', '').lower() in ('', 'text/javascript', 'application/javascript') and 'src' not in attributes

    def handle_endtag(self, tag):
        if tag == 'script': self.in_script = False

    def handle_data(self, data):
        if self.in_script: self.scripts.append(data)


class WebsiteInteractionTests(unittest.TestCase):
    def test_actual_inline_scripts_in_both_languages(self):
        pages = {}
        for page in (ROOT / 'docs/research').glob('*.html'):
            parser = ScriptElements(); parser.feed(page.read_text())
            pages[page.name] = {'elements': parser.elements, 'script': '\n'.join(parser.scripts)}
        with tempfile.TemporaryDirectory() as directory:
            data = Path(directory) / 'elements.json'
            data.write_text(json.dumps(pages))
            result = subprocess.run(['node', str(ROOT / 'tests/website_interactions.js'), str(data)],
                                    capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn('1120', result.stdout)


if __name__ == '__main__': unittest.main()
