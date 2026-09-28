# Kshitiz Neupane — Portfolio

A React portfolio focused on machine learning and data science, with a piano-inspired navy and ivory design. The homepage places Kshitiz’s introduction and sketch portrait in a dark panel above a decorative keyboard. The other pages use subtle staff lines, key-like filters, and restrained gold accents. Work includes category filters and seven illustrated projects, each with a dedicated page containing an explanation, tools, results, and selected images. Research introduces the coauthored Filter-then-Verify preprint and ongoing WMSV work. Every figure can be opened at full size.

Scientific visuals come from saved local experiment and notebook outputs. Application work uses a local screenshot or a clearly captioned architecture diagram. See `docs/PROJECT-VISUALS.md` for provenance. Public assets are explicitly selected by the build.

Home, Work, About, Research, and Now are separate accessible hash routes. Browser history, keyboard navigation, and repository-subpath hosting are supported.

## Edit in one place

Edit **`content/profile.json`**. Both the website and résumé use this file.

| What to update | JSON field |
| --- | --- |
| Name, email, links, bio, introduction | `profile` |
| Current projects and research focus | `now` |
| The displayed last-update date | `updated` (`YYYY-MM-DD`) |
| Research interests and topics | `research` |
| School, graduation, GPA, coursework | `education` |
| Roles, dates, résumé bullets | `experience` |
| Projects, technologies, links, results | `projects` |
| Résumé skills | `skills` |

To add a project, copy an existing project object, assign a unique lowercase `id`, and edit its fields. Use `featured: true` for the main work list and `false` for “More explorations.” Use `resume: true` to include it in the PDF, supplying `resume_title`, `resume_stack`, and `bullets`. Set `url` to an empty string when there is no public repository. Array order controls display order. Each project also needs `group`, `question`, `details`, `highlights`, `image`, `image_alt`, and `caption`. Add optional gallery entries with `image`, `alt`, and `caption`; put approved visual assets in `assets/projects/`. JSON requires double quotes and no trailing commas.

For a routine update: edit `now` or `projects`, change `updated`, preview, and commit. Dates are deliberate content dates; the site does not falsely label every automated build as a content update.

## Preview locally

Requires Node.js 20 or newer and Python 3.10 or newer. From the portfolio folder:

```bash
npm ci
npm run dev
```

Open <http://localhost:4173>. After editing content or JSX, run `npm run build:preview` and refresh your browser. If the server is already running, leave it running. The JavaScript bundle uses a content hash and the stylesheet has a versioned URL so a refreshed page loads the matching assets.

The build bundles React locally with esbuild and updates the generated LaTeX source while retaining the existing PDF. Visitors do not depend on a CDN or a separate content fetch. To update the PDF too, install a TeX Live distribution with `pdflatex`, `geometry`, and `hyperref`, then run:

```bash
python3 scripts/build.py --resume
```

On Ubuntu/Debian, `sudo apt-get install texlive-latex-recommended` supplies the compiler and required packages. The build checks the résumé layout, content values, URLs, and generated assets. Browser tests verify that page changes remove the previous page from the document. If résumé content outgrows one page, shorten bullets or deselect a project.

## Hosting on GitHub Pages

This repository publishes the portfolio with GitHub Actions to `https://kshitiz-tech.github.io/`. The custom domain is `kshitiz-tech.com`; its DNS is managed in Cloudflare. Each push to `main` runs the content tests, builds the site, and deploys the public files in `dist`.

GitHub Pages uses the custom workflow in `.github/workflows/deploy.yml`. To update the portfolio, edit `content/profile.json` or the site source and push to `main`. The workflow installs the locked npm dependencies, runs content checks, builds React, and publishes the resulting files. The header résumé menu offers five PDFs from `assets/`; edit the `resumes` list in `content/profile.json` to change their labels or descriptions. The generated PDF in `assets/Kshitiz-Neupane-Resume.pdf` remains available; regenerate it locally with `python3 scripts/build.py --resume` when résumé content changes.

This follows GitHub's [custom Pages workflow](https://docs.github.com/en/pages/getting-started-with-github-pages/using-custom-workflows-with-github-pages) and [publishing-source setup](https://docs.github.com/en/pages/getting-started-with-github-pages/configuring-a-publishing-source-for-your-github-pages-site).

## Other static hosts

```bash
python3 scripts/build.py --resume --output dist
```

Publish the **contents of `dist/`** to your static host. It contains HTML, CSS, the bundled React JavaScript, the favicon, and the résumé. Hash routes such as `/#research` work without server-side routing rules, and asset paths also work under a repository subpath. No backend service or secrets are required. Publish the generated output rather than the source folder.

Generate a source ZIP and a separate ready-to-host ZIP:

```bash
npm run build
python3 scripts/package.py
```

The ZIPs are written to `/tmp/portfolio-deliverables/` by default. Use `--output /your/folder` to choose another location. The source ZIP includes GitHub Actions and the content/template files; the hosting ZIP includes only the website files.

## Validation and structure

```bash
npm test
npm run build
npx playwright install chromium
npm run test:browser
```

- `content/profile.json`: editable website and résumé content.
- `src/App.jsx`: Home, Work, About, Research, and Now React components and navigation.
- `templates/index.html`, `styles.css`: HTML shell and palette.
- `scripts/build-web.mjs`: bundles React with a content-hashed filename.
- `templates/resume.tex`: the reference-style, single-column résumé layout.
- `scripts/build.py`: content validation, React build integration, and PDF generation.
- `resume/Kshitiz-Neupane-Resume.tex`: generated LaTeX; edit the template/content instead.
- `assets/Kshitiz-Neupane-Resume.pdf`: compiled résumé for local preview/download.
- `.github/workflows/deploy.yml`: automatic build, validation, and Pages deployment.
- `docs/RESUME-NOTES.md`: source selection, factual support, and editorial assumptions.

The browser tests use Google Chrome when installed at `/usr/bin/google-chrome`, or Playwright's Chromium otherwise. Set `CHROME_BIN` to use another Chrome location. Tests run the built site on port 4180 and check all page-to-page transitions, DOM removal, history, refresh, keyboard access, downloads, and hosting under a repository subpath. The React routing follows [conditional component rendering](https://react.dev/learn/conditional-rendering).
