"""Checks for content edits, escaping, broken navigation, and deployment boundaries."""

import copy
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("portfolio_build", ROOT / "scripts/build.py")
builder = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(builder)


class BuildTests(unittest.TestCase):
    def setUp(self):
        self.data = json.loads((ROOT / "content/profile.json").read_text())

    def test_content_changes_reach_both_formats_and_are_escaped(self):
        self.data["profile"]["name"] = "A & B <Example>"
        html = builder.render_site(self.data)
        latex = builder.render_resume(self.data)
        self.assertIn("A &amp; B &lt;Example&gt;", html)
        self.assertIn(r"A \& B <Example>", latex)
        self.data["profile"]["intro"] = '<script>alert("bad")</script>'
        self.assertNotIn('<script>alert("bad")</script>', builder.render_site(self.data))

    def test_unsafe_urls_are_rejected(self):
        for url in ["javascript:alert(1)", "//example.com", "https://example.com/a b"]:
            self.data["projects"][0]["url"] = url
            with self.assertRaises(ValueError):
                builder.validate_content(self.data)

    def test_duplicate_project_ids_are_rejected(self):
        self.data["projects"].append(copy.deepcopy(self.data["projects"][0]))
        with self.assertRaises(ValueError):
            builder.validate_content(self.data)

    def test_projects_can_have_no_public_repository(self):
        self.data["projects"][0]["url"] = ""
        builder.validate_content(self.data)

    def test_resume_selection_changes_independently_of_website(self):
        self.data["projects"][0]["resume"] = False
        self.assertNotIn("ShiftGuard", builder.render_resume(self.data))
        self.assertTrue(self.data["projects"][0]["featured"])

    def test_shell_cannot_display_inactive_pages_before_react_loads(self):
        html = builder.render_site(self.data)
        self.assertIn('<div id="app"></div>', html)
        self.assertNotIn("<section", html)
        self.assertNotIn("data-panel", html)
        self.assertNotIn("portfolio.js", html)

    def test_broken_anchors_and_missing_assets_are_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            for html in ['<a href="#missing">Broken</a>', '<img src="missing.png">', '<p id="same"></p><p id="same"></p>']:
                with self.assertRaises(ValueError):
                    builder.validate_site(html, Path(tmp))

    def test_standalone_build_contains_only_public_files(self):
        with tempfile.TemporaryDirectory() as tmp:
            output = Path(tmp)
            builder.build(output)
            files = {str(p.relative_to(output)) for p in output.rglob("*") if p.is_file()}
            bundles = {name for name in files if name.startswith("assets/app-") and name.endswith(".js")}
            self.assertEqual(len(bundles), 1)
            self.assertEqual(files - bundles, {"index.html", "styles.css", ".nojekyll", "assets/favicon.svg", "assets/avatar_sketch_under_1mb.jpg", "assets/Kshitiz-Neupane-Resume.pdf", *builder.project_assets(self.data)})
            self.assertIn(next(iter(bundles)), (output / "index.html").read_text())
            self.assertNotIn("/home/", (output / "index.html").read_text())


if __name__ == "__main__":
    unittest.main()
