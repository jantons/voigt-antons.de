# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this repo is

Personal academic website for Prof. Dr.-Ing. Jan-Niklas Voigt-Antons, built on the [Academic Pages](https://academicpages.github.io/) Jekyll template. Deployed to [voigt-antons.de](https://voigt-antons.de) via GitHub Pages.

## Commands

### Local development
```bash
bundle install          # Install Ruby gems (delete Gemfile.lock and retry if it fails)
bundle exec jekyll serve -l -H localhost   # Serve at localhost:4000 with live reload
```

### JavaScript build
```bash
npm install             # Install Node dependencies
npm run build:js        # Bundle and minify JS into assets/js/main.min.js
npm run watch:js        # Rebuild JS on file changes
```

### Docker (alternative)
```bash
docker build -t jekyll-site .
docker run -p 4000:4000 --rm -v $(pwd):/usr/src/app jekyll-site
```

## Architecture

### Content model
Content lives in Jekyll collections and is authored as Markdown with YAML front matter:

| Collection | Directory | URL pattern |
|---|---|---|
| Publications | `_publications/` | `/publication/YYYY-MM-DD-<ID>/` |
| Talks | `_talks/` | `/talk/YYYY-MM-DD-<ID>/` |
| Teaching | `_teaching/` | `/teaching/<slug>/` |
| Portfolio | `_portfolio/` | `/portfolio/<slug>/` |
| Pages | `_pages/` | configured per file |

**Publication filenames** follow the pattern `YYYY-MM-DD-<TypeCode><Number>.md` where type codes are: `C` (conference), `J` (journal), `BC` (book chapter), `OC` (other conference). The front matter fields are: `title`, `authors`, `category` (matches `publication_category` keys in `_config.yml`), `venue`, `date`, `paperurl`, `citation`, `excerpt`.

### Data-driven sections
Several pages render from `_data/` YAML files rather than collections:
- `_data/highlights.yml` — research lines shown on the home page
- `_data/projects.yml` — funded research projects (Projects & Transfer page)
- `_data/navigation.yml` — top navigation menu
- `_data/courses.yml` — teaching page course list
- `_data/service.yml` — service & leadership entries

### Layouts and includes
- `_layouts/single.html` — default for pages and publications
- `_layouts/talk.html` — for talks
- `_layouts/archive.html` — list views (publications, blog, etc.)
- `_includes/head/custom.html` — custom `<head>` content: favicons, MathJax, Schema.org JSON-LD for the homepage
- `_includes/author-profile.html` — left sidebar with author info

### Styling
SCSS source lives in `_sass/`. Key files: `_variables.scss` (colors, breakpoints, typography), `_page.scss`, `_sidebar.scss`, `_masthead.scss`. The section layout pattern used across pages is `.section-block` with modifier `--white` or `--light` for alternating backgrounds (defined in `_sass/_page.scss` or inline).

### JS pipeline
Source files (`assets/js/_main.js`, `assets/js/collapse.js`, `assets/js/plugins/`) are bundled via `npm run build:js` (uglify-js) into `assets/js/main.min.js`. The source files are excluded from the Jekyll build; only `main.min.js` is served.

### SEO / structured data
The canonical Schema.org `Person` JSON-LD is in `_includes/head/custom.html` (injected only on the homepage). The `social:` block in `_config.yml` is intentionally left empty to prevent duplicate schema generation from the theme.

## Key configuration (`_config.yml`)
- `publication_category` — defines the publication type taxonomy (`books`, `bookchapters`, `manuscripts`, `conferences`, `standardizations`)
- `analytics.provider` must be boolean `false` (not the string `"false"`) to disable analytics
- `repository` should stay as `jantons/voigt-antons.de`
