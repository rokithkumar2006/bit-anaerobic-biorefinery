import re
import subprocess
import unittest
from html.parser import HTMLParser
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
HTML_FILE = ROOT / "index.html"

class InlineScriptParser(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=False)
        self.scripts = []
        self._inside_inline_script = False
        self._current = []

    def handle_starttag(self, tag, attrs):
        if tag.lower() == "script":
            attrs = dict(attrs)
            self._inside_inline_script = not bool(attrs.get("src"))
            self._current = []

    def handle_data(self, data):
        if self._inside_inline_script:
            self._current.append(data)

    def handle_endtag(self, tag):
        if tag.lower() == "script":
            if self._inside_inline_script:
                self.scripts.append("".join(self._current))
            self._inside_inline_script = False
            self._current = []

class FrontendStaticTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.html = HTML_FILE.read_text(encoding="utf-8")
        cls.parser = InlineScriptParser()
        cls.parser.feed(cls.html)

    def test_required_workspace_pages_are_navigable(self):
        ids = set(re.findall(r"""\bid=["']([^"']+)["']""", self.html))
        nav_targets = set(re.findall(r"""data-page=["']([^"']+)["']""", self.html))
        for page in ["overview", "waste", "data", "stpdata", "workflow", "opensource",
                     "digester", "prediction", "optimization", "scenarios", "circular", "quality"]:
            with self.subTest(page=page):
                self.assertIn(page, ids, "Missing page section id")
                self.assertIn(page, nav_targets, "Missing navigation target")

    def test_key_automation_and_data_controls_exist(self):
        ids = set(re.findall(r"""\bid=["']([^"']+)["']""", self.html))
        for control_id in ["p5RunChecks", "p5ExportReport", "dataStpExcelFile",
                           "dataStpAppendBtn", "dataStpReplaceBtn", "dataStpExportBtn",
                           "downloadLocalBackupBtn", "restoreLocalBackupInput"]:
            with self.subTest(control=control_id):
                self.assertIn(control_id, ids)

    def test_inline_javascript_parses_with_node(self):
        self.assertGreater(len(self.parser.scripts), 0)
        for index, script in enumerate(self.parser.scripts, start=1):
            with self.subTest(inline_script=index):
                result = subprocess.run(["node", "--check"], input=script, text=True,
                                        capture_output=True, cwd=ROOT, check=False)
                self.assertEqual(result.returncode, 0,
                                 f"Inline script {index} failed syntax validation:\n{result.stderr}")

if __name__ == "__main__":
    unittest.main()
