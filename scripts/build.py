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
SITE_URL = "https://kshitiz-tech.com"


def safe_json(value):
    return json.dumps(value, ensure_ascii=False).replace("<", "\\u003c").replace(">", "\\u003e").replace("&", "\\u0026")


def validate_content(data):
    date.fromisoformat(data["updated"])
    for field in ("name", "email", "phone", "location", "github", "linkedin", "bio"):
        if not data["profile"][field]:
            raise ValueError(f"profile.{field} must not be empty")
    if not re.fullmatch(r"[^\s<>@]+@[^\s<>@]+\.[^\s<>@]+", data["profile"]["email"]):
        raise ValueError("profile.email must be a valid email address")
    resumes = data["resumes"]
    if len(resumes) != 5 or len({resume["file"] for resume in resumes}) != 5:
        raise ValueError("Provide five distinct résumé PDFs")
    for resume in resumes:
        path = Path(resume["file"])
        if not resume["label"] or not resume["description"] or path.parent != Path("assets") or path.suffix.lower() != ".pdf" or not (ROOT / path).is_file():
            raise ValueError(f"Invalid or missing résumé PDF: {resume['file']}")
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
    person = {
        "@type": "Person", "@id": f"{SITE_URL}/#person",
        "name": data["profile"]["name"],
        "description": data["profile"]["intro"],
        "image": f"{SITE_URL}/assets/avatar_sketch_under_1mb.jpg",
        "url": f"{SITE_URL}/",
        "sameAs": [data["profile"]["github"], data["profile"]["linkedin"]],
        "alumniOf": {"@type": "CollegeOrUniversity", "name": data["education"]["institution"]},
    }
    structured_data = {"@context": "https://schema.org", "@graph": [
        {"@type": "WebSite", "name": f"{data['profile']['name']} | Machine Learning & Data Science", "url": f"{SITE_URL}/", "author": {"@id": person["@id"]}},
        person,
    ]}
    return Template((ROOT / "templates/index.html").read_text()).substitute(
        name=escape(data["profile"]["name"], quote=True),
        description=escape(f"{data['profile']['name']} — {data['profile']['intro']}", quote=True),
        title=escape(f"{data['profile']['name']} | Machine Learning & Data Science", quote=True),
        structured_data=safe_json(structured_data),
        stylesheet="styles.css?v=" + hashlib.sha256((ROOT / "styles.css").read_bytes()).hexdigest()[:12],
        script=escape(script, quote=True),
    )


def render_static_page(data, *, title, description, canonical, image, content, prefix, structured_data):
    profile = data["profile"]
    resume_options = "".join(
        f'<a href="{prefix}/{escape(resume["file"], quote=True)}" download>'
        f'<span><strong>{escape(resume["label"])}</strong><small>{escape(resume["description"])}</small></span>'
        '<span aria-hidden="true">↓</span></a>'
        for resume in data["resumes"]
    )
    return Template((ROOT / "templates/static.html").read_text()).substitute(
        title=escape(title, quote=True),
        description=escape(description, quote=True),
        canonical=escape(canonical, quote=True),
        image=escape(image, quote=True),
        structured_data=safe_json(structured_data),
        prefix=prefix,
        stylesheet="styles.css?v=" + hashlib.sha256((ROOT / "styles.css").read_bytes()).hexdigest()[:12],
        content=content,
        name=escape(profile["name"], quote=True),
        year=data["updated"][:4],
        github=escape(profile["github"], quote=True),
        linkedin=escape(profile["linkedin"], quote=True),
        email=escape(profile["email"], quote=True),
        resume_options=resume_options,
    )


def render_project_page(data, project, next_project):
    h = lambda value: escape(str(value), quote=True)
    prefix = "../.."
    canonical = f"{SITE_URL}/projects/{project['id']}/"
    visuals = [{"image": project["image"], "alt": project["image_alt"], "caption": project["caption"]}, *project.get("gallery", [])]
    repository = f'<a class="project-link" href="{h(project["url"])}">View repository ↗</a>' if project.get("url") else ""
    paragraphs = "".join(f"<p>{h(paragraph)}</p>" for paragraph in project["details"])
    highlights = "".join(f"<li>{h(item)}</li>" for item in project["highlights"])
    tags = "".join(f"<li>{h(item)}</li>" for item in project["stack"])
    gallery = "".join(
        f'<figure class="{"wide" if index == 0 else ""}"><a href="{prefix}/{h(visual["image"])}" aria-label="Open full-size image: {h(visual["caption"])}"><img src="{prefix}/{h(visual["image"])}" alt="{h(visual["alt"])}" width="1000" height="650" loading="lazy"></a><figcaption>{h(visual["caption"])}</figcaption></figure>'
        for index, visual in enumerate(visuals)
    )
    gallery_section = f'<section class="project-page-gallery" aria-labelledby="gallery-title"><div class="gallery-heading"><p class="eyebrow">Project visuals</p><h2 id="gallery-title">Results and interface</h2><p>Open any image to see it at full size.</p></div><div class="detail-gallery">{gallery}</div></section>' if len(visuals) > 1 else ""
    content = f'''<article class="project-page wrap" aria-labelledby="project-page-title">
      <a class="back-link" href="{prefix}/#work">← Back to work</a>
      <header class="project-page-header"><div><p class="project-category">{h(project["category"])}</p><h1 class="page-title" id="project-page-title">{h(project["name"])}</h1><p class="project-page-question">{h(project["question"])}</p></div><div class="project-page-summary"><p>{h(project["description"])}</p>{repository}</div></header>
      <figure class="project-page-lead"><a href="{prefix}/{h(project["image"])}"><img src="{prefix}/{h(project["image"])}" alt="{h(project["image_alt"])}" width="1400" height="900"></a><figcaption>{h(project["caption"])}</figcaption></figure>
      <div class="project-page-content"><section aria-labelledby="about-project"><p class="eyebrow">About the project</p><h2 id="about-project">What it is</h2>{paragraphs}</section><aside><p class="eyebrow">What it includes</p><ul>{highlights}</ul><p class="eyebrow tools-label">Tools</p><ul class="tags" aria-label="Technologies">{tags}</ul></aside></div>
      {gallery_section}
      <nav class="project-next" aria-label="Project navigation"><span>Next project</span><a href="../{h(next_project["id"])}/">{h(next_project["name"])} ↗</a></nav>
    </article>'''
    structured_data = {"@context": "https://schema.org", "@type": "CreativeWork", "name": project["name"], "description": project["description"], "url": canonical, "image": f"{SITE_URL}/{project['image']}", "creator": {"@type": "Person", "name": data["profile"]["name"], "url": f"{SITE_URL}/"}}
    if project.get("url"):
        structured_data["sameAs"] = project["url"]
    return render_static_page(data, title=f"{project['name']} | {data['profile']['name']}", description=project["description"], canonical=canonical, image=f"{SITE_URL}/{project['image']}", content=content, prefix=prefix, structured_data=structured_data)


def render_research_page(data):
    h = lambda value: escape(str(value), quote=True)
    research = data["research"]
    paper = research["publication"]
    current = research["current"]
    content = f'''<section class="research-section wrap" aria-labelledby="research-title">
      <div class="research-heading"><p class="eyebrow">Research</p><h1 class="page-title" id="research-title">What I’m studying</h1></div>
      <div class="research-entries"><article class="research-entry"><p class="eyebrow">{h(paper["status"])}</p><h2>{h(paper["title"])}</h2><p class="paper-subtitle">{h(paper["subtitle"])}</p><p class="paper-authors">{h(paper["authors"])}</p><p>{h(paper["description"])}</p><div class="paper-links"><a href="{h(paper["url"])}">Read the paper ↗</a><a href="{h(paper["scholar_url"])}">Google Scholar ↗</a></div></article>
      <article class="research-entry"><p class="eyebrow">{h(current["status"])}</p><h2>{h(current["title"])}</h2><p>{h(current["description"])}</p></article>
      <div class="research-interest"><p class="eyebrow">Also interested in</p><h2>{h(research["title"])}</h2><p>{h(research["description"])}</p></div></div>
    </section>'''
    structured_data = {"@context": "https://schema.org", "@type": "CollectionPage", "name": f"Research | {data['profile']['name']}", "description": research["description"], "url": f"{SITE_URL}/research/", "about": [paper["title"], current["title"]], "author": {"@type": "Person", "name": data["profile"]["name"]}}
    return render_static_page(data, title=f"Research | {data['profile']['name']}", description=f"Research by {data['profile']['name']} on social engineering detection, measurement sensitivity, and reliable AI.", canonical=f"{SITE_URL}/research/", image=f"{SITE_URL}/assets/avatar_sketch_under_1mb.jpg", content=content, prefix="..", structured_data=structured_data)


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
    # Explicit public-file list keeps source notes and tooling out of the deployment.
    (output / PUBLIC_ASSETS[0]).write_bytes(pdf)
    for asset in ("styles.css", "assets/favicon.svg", "assets/avatar_sketch_under_1mb.jpg", *(resume["file"] for resume in data["resumes"]), *project_assets(data)):
        (output / asset).parent.mkdir(parents=True, exist_ok=True)
        if (ROOT / asset).resolve() != (output / asset).resolve():
            shutil.copy2(ROOT / asset, output / asset)
    validate_site(html, output)
    (output / "index.html").write_text(html)
    research_dir = output / "research"
    research_dir.mkdir(exist_ok=True)
    (research_dir / "index.html").write_text(render_research_page(data))
    for index, project in enumerate(data["projects"]):
        project_dir = output / "projects" / project["id"]
        project_dir.mkdir(parents=True, exist_ok=True)
        next_project = data["projects"][(index + 1) % len(data["projects"])]
        (project_dir / "index.html").write_text(render_project_page(data, project, next_project))
    urls = [f"{SITE_URL}/", f"{SITE_URL}/research/", *(f"{SITE_URL}/projects/{project['id']}/" for project in data["projects"])]
    sitemap = '<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
    sitemap += "".join(f"  <url><loc>{escape(url)}</loc><lastmod>{data['updated']}</lastmod></url>\n" for url in urls)
    (output / "sitemap.xml").write_text(sitemap + "</urlset>\n")
    (output / "robots.txt").write_text(f"User-agent: *\nAllow: /\nSitemap: {SITE_URL}/sitemap.xml\n")
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
