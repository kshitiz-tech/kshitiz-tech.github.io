#!/usr/bin/env python3
"""Create separate source and hosting ZIPs, with an explicit file allowlist."""

from pathlib import Path
import argparse
import json
import zipfile
from build import project_assets

ROOT = Path(__file__).resolve().parents[1]
DIST = ROOT / "dist"
data = json.loads((ROOT / "content/profile.json").read_text())
if not (DIST / "index.html").is_file():
    raise SystemExit("Run npm run build before packaging the site.")
PUBLIC = sorted(str(path.relative_to(DIST)) for path in DIST.rglob("*") if path.is_file())
SOURCE = [
    "README.md", ".gitignore", ".nojekyll", "content/profile.json", "templates/index.html", "templates/static.html", "templates/resume.tex",
    "scripts/build.py", "scripts/package.py", "tests/test_build.py", ".github/workflows/deploy.yml",
    "resume/Kshitiz-Neupane-Resume.tex", "docs/RESUME-NOTES.md", "docs/PROJECT-VISUALS.md",
    "package.json", "package-lock.json", "src/App.jsx", "scripts/build-web.mjs",
    "playwright.config.js", "tests/browser/navigation.spec.js", "styles.css", "index.html",
    "assets/Kshitiz-Neupane-Resume.pdf", "assets/favicon.svg", "assets/avatar_sketch_under_1mb.jpg",
    *(resume["file"] for resume in data["resumes"]),
    *project_assets(data),
]

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=Path("/tmp/portfolio-deliverables"))
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=True)
    for name, files, base in [("portfolio-source.zip", SOURCE, ROOT), ("portfolio-site.zip", PUBLIC, DIST)]:
        with zipfile.ZipFile(args.output / name, "w", zipfile.ZIP_DEFLATED) as archive:
            for filename in files:
                archive.write(base / filename, filename)
        print(args.output / name)
