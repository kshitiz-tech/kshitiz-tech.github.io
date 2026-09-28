#!/usr/bin/env python3
"""Bundle the React portfolio and generate the matching LaTeX resume."""

import argparse
from datetime import date
import hashlib
from html import escape
from html.parser import HTMLParser
import json
from pathlib import Path
import re
import shutil
from string import Template
import subprocess
import tempfile
from urllib.parse import urlsplit

ROOT = Path(__file__).resolve().parents[1]
RESUME_NAME = "Kshitiz-Neupane-Resume"
PUBLIC_ASSETS = (f"assets/{RESUME_NAME}.pdf", "assets/favicon.svg")


def validate_content(data):
    date.fromisoformat(data["updated"])
    for field in ("name", "email", "phone", "location", "github", "linkedin", "bio"):
        if not data["profile"][field]:
            raise ValueError(f"profile.{field} must not be empty")
    if not re.fullmatch(r"[^\s<>@]+@[^\s<>@]+\.[^\s<>@]+", data["profile"]["email"]):
        raise ValueError("profile.email must be a valid email address")
    ids = set()
    for project in data["projects"]:
        if not re.fullmatch(r"[a-z][a-z0-9-]*", project["id"]) or project["id"] in ids:
            raise ValueError(f"Invalid or duplicate project id: {project['id']}")
        ids.add(project["id"])
        for field in ("name", "category", "description", "stack"):
            if not project[field]:
                raise ValueError(f"{project['id']}.{field} must not be empty")
        if not isinstance(project["featured"], bool) or not isinstance(project["resume"], bool):
            raise ValueError("Project featured/resume flags must be true or false")
        if project["featured"] and not project["result"]:
            raise ValueError("Featured projects need a result")
        if project["resume"]:
            for field in ("resume_title", "resume_stack", "bullets"):
                if not project[field]:
                    raise ValueError(f"Resume project needs {field}")
    urls = [data["profile"][k] for k in ("github", "linkedin")]
    urls += [p.get("url", "") for p in data["projects"] + data["now"]]
    for url in filter(None, urls):
        parts = urlsplit(url)
        if parts.scheme != "https" or not parts.netloc or parts.username or re.search(r"[\s<>]", url):
            raise ValueError(f"Use a complete HTTPS URL: {url}")


def project_assets(data):
    assets = []
    for project in data["projects"]:
        visuals = [{"image": project["image"], "alt": project.get("image_alt"), "caption": project.get("caption")}, *project.get("gallery", [])]
        for visual in visuals:
            asset = visual["image"]
            path = Path(asset)
            if path.parent != Path("assets/projects") or path.suffix not in {".png", ".svg", ".webp"} or not (ROOT / path).is_file():
                raise ValueError(f"Invalid or missing project image: {asset}")
            if not visual.get("alt") or not visual.get("caption"):
                raise ValueError(f"Project image needs alternative text and caption: {asset}")
            assets.append(asset)
    return assets


def render_site(data, script="assets/app.js"):
    """The HTML shell contains no inactive pages; React owns the single main view."""
    return Template((ROOT / "templates/index.html").read_text()).substitute(
        name=escape(data["profile"]["name"], quote=True),
        description=escape(f"{data['profile']['name']} — {data['profile']['intro']}", quote=True),
        stylesheet="styles.css?v=" + hashlib.sha256((ROOT / "styles.css").read_bytes()).hexdigest()[:12],
        script=escape(script, quote=True),
    )


def bundle_react(output):
    if not shutil.which("node") or not (ROOT / "node_modules/esbuild").is_dir():
        raise ValueError("Install Node.js and run npm ci before building the React portfolio.")
    result = subprocess.run(
        ["node", str(ROOT / "scripts/build-web.mjs"), str(output)],
        cwd=ROOT, capture_output=True, text=True, check=False,
    )
    if result.returncode:
        raise ValueError("React build failed:\n" + result.stderr[-3500:])
    return json.loads(result.stdout)["script"]


def tex(value):
    mapping = {"\\": r"\textbackslash{}", "&": r"\&", "%": r"\%", "$": r"\$", "#": r"\#", "_": r"\_", "{": r"\{", "}": r"\}", "~": r"\textasciitilde{}", "^": r"\textasciicircum{}", "—": "---", "–": "--", "’": "'"}
    return "".join(mapping.get(c, c) for c in value)


def tex_bullets(items):
    return "\\begin{bullets}\n" + "\n".join("\\item " + tex(item) for item in items) + "\n\\end{bullets}\n"


def render_resume(data):
    values = {k: tex(v) for k, v in data["profile"].items() if isinstance(v, str)}
    values.update({k: tex(v) for k, v in data["education"].items()})
    values["education_location"] = tex(data["education"]["location"])
    values["research_title"] = tex(data["research"]["title"])
    experience = []
    for p in data["experience"]:
        experience.append(
            f'\\textbf{{{tex(p["role"])}}}\\hfill {tex(p["dates"])}\\\\\n'
            f'\\textit{{{tex(p["organization"])}}}\\hfill\\textit{{{tex(p["location"])}}}\n'
            + tex_bullets(p["bullets"])
        )
    projects = []
    for p in data["projects"]:
        if not p["resume"]:
            continue
        link = f'\\hfill\\href{{{tex(p["url"])}}}{{GitHub}}' if p.get("url") else ""
        projects.append(
            f'\\textbf{{{tex(p["resume_title"])}}}{link}\\\\\n'
            f'{{\\small\\textit{{{tex(p["resume_stack"])}}}}}\n' + tex_bullets(p["bullets"])
        )
    values["experience"] = "\n\\vspace{3pt}\n".join(experience)
    values["projects"] = "\n\\vspace{3pt}\n".join(projects)
    values["skills"] = "\\\\[2pt]\n".join(f'{{\\small\\textbf{{{tex(s["label"])}:}} {tex(s["items"])}}}' for s in data["skills"])
    return Template((ROOT / "templates/resume.tex").read_text()).substitute(values)


class PageLinks(HTMLParser):
    def __init__(self):
        super().__init__()
        self.ids, self.links = set(), []

    def handle_starttag(self, tag, attrs):
        values = dict(attrs)
        if "id" in values:
            if values["id"] in self.ids:
                raise ValueError(f"Duplicate HTML id: {values['id']}")
            self.ids.add(values["id"])
        for attr in ("href", "src"):
            if values.get(attr):
                self.links.append(values[attr])


def validate_site(html, output):
    parser = PageLinks()
    parser.feed(html)
    for link in parser.links:
        if link.startswith("#"):
            if link[1:] not in parser.ids:
                raise ValueError(f"Broken section link: {link}")
        elif not urlsplit(link).scheme and not (output / urlsplit(link).path).is_file():
            raise ValueError(f"Missing local asset: {link}")


def compile_resume(source):
    if not shutil.which("pdflatex"):
        raise ValueError("Install pdflatex (TeX Live), or omit --resume to use the existing PDF.")
    with tempfile.TemporaryDirectory(prefix="portfolio-resume-") as tmp:
        working = Path(tmp)
        (working / f"{RESUME_NAME}.tex").write_text(source)
        for _ in range(2):
            result = subprocess.run(
                ["pdflatex", "-no-shell-escape", "-interaction=nonstopmode", "-halt-on-error", f"{RESUME_NAME}.tex"],
                cwd=working, capture_output=True, text=True, check=False,
            )
            if result.returncode:
                raise ValueError("LaTeX compilation failed:\n" + result.stdout[-3500:])
        log = (working / f"{RESUME_NAME}.log").read_text()
        if not re.search(r"Output written on .*\(1 page,", log):
            raise ValueError("Resume exceeds one page. Shorten bullets or select fewer resume projects in content/profile.json.")
        if "Overfull \\hbox" in log or "Overfull \\vbox" in log:
            raise ValueError("Resume has overflowing text. Shorten the affected content before publishing.")
        return (working / f"{RESUME_NAME}.pdf").read_bytes()


def build(output, include_resume=False):
    data = json.loads((ROOT / "content/profile.json").read_text())
    validate_content(data)
    source = render_resume(data)
    pdf = compile_resume(source) if include_resume else (ROOT / PUBLIC_ASSETS[0]).read_bytes()
    output.mkdir(parents=True, exist_ok=True)
    (output / "assets").mkdir(exist_ok=True)
    html = render_site(data, bundle_react(output))
    # Explicit public-file list: source notes, original resumes, and tooling stay out of the deployment.
    (output / PUBLIC_ASSETS[0]).write_bytes(pdf)
    for asset in ("styles.css", "assets/favicon.svg", "assets/avatar_sketch_under_1mb.jpg", *project_assets(data)):
        (output / asset).parent.mkdir(parents=True, exist_ok=True)
        if (ROOT / asset).resolve() != (output / asset).resolve():
            shutil.copy2(ROOT / asset, output / asset)
    validate_site(html, output)
    (output / "index.html").write_text(html)
    (output / ".nojekyll").touch()
    (ROOT / "resume").mkdir(exist_ok=True)
    (ROOT / f"resume/{RESUME_NAME}.tex").write_text(source)
    print(f"Built React portfolio at {output}/index.html; checked bundled assets.")
    if include_resume:
        print("Compiled and checked the one-page resume PDF (no overflowing text).")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=ROOT, help="Output directory; use dist for publishing")
    parser.add_argument("--resume", action="store_true", help="Recompile the PDF with pdflatex")
    args = parser.parse_args()
    try:
        build(args.output.resolve(), args.resume)
    except (ValueError, KeyError, OSError) as exc:
        parser.exit(1, f"Build failed: {exc}\n")
