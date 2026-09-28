#!/usr/bin/env python3
"""Create separate source and hosting ZIPs, with an explicit file allowlist."""

from pathlib import Path
import argparse
import json
from urllib.parse import urlsplit
import zipfile
from build import PageLinks, project_assets

ROOT = Path(__file__).resolve().parents[1]
# Include only the files referenced by the current generated page, including its hashed bundle.
page = PageLinks()
page.feed((ROOT / "index.html").read_text())
PUBLIC = ["index.html", ".nojekyll"] + sorted({
    urlsplit(link).path for link in page.links if not urlsplit(link).scheme and not link.startswith("#")
})
PUBLIC += ["assets/avatar_sketch_under_1mb.jpg", *project_assets(json.loads((ROOT / "content/profile.json").read_text()))]
SOURCE = PUBLIC + [
    "README.md", ".gitignore", "content/profile.json", "templates/index.html", "templates/resume.tex",
    "scripts/build.py", "scripts/package.py", "tests/test_build.py", ".github/workflows/deploy.yml",
    "resume/Kshitiz-Neupane-Resume.tex", "docs/RESUME-NOTES.md", "docs/PROJECT-VISUALS.md",
    "package.json", "package-lock.json", "src/App.jsx", "scripts/build-web.mjs",
    "playwright.config.js", "tests/browser/navigation.spec.js",
]

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=Path("/tmp/portfolio-deliverables"))
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=True)
    for name, files in [("portfolio-source.zip", SOURCE), ("portfolio-site.zip", PUBLIC)]:
        with zipfile.ZipFile(args.output / name, "w", zipfile.ZIP_DEFLATED) as archive:
            for filename in files:
                archive.write(ROOT / filename, filename)
        print(args.output / name)
