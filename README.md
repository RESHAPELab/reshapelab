# reshapelab.site

The RESHAPE Lab website. Static HTML generated from a handful of CSV files by
one Python script, served from GitHub Pages. No framework, no database, no
build toolchain — `python scripts/build_site.py` and you are done.

```
python scripts/build_site.py           # normal build (hits DBLP + Unpaywall)
python scripts/build_site.py --offline # rebuild from cache, no network
```

Everything under "generated files" below is committed. That is deliberate:
GitHub Pages serves the repo as-is, so the HTML has to be in it, and it means
crawlers and link previews see real content instead of an empty shell.

---

## Adding or changing things

### A new member

1. Add a row to `data/members.csv`.
2. Drop a square photo at `assets/people/<slug>.jpg`.
3. Run the build.

They get a card on `people.html` and their own page at `people/<slug>.html`
with their publications, projects, and current position.

| Column | Notes |
| --- | --- |
| `slug` | URL and filename key. Leave blank to derive it from the name. |
| `name` | As you want it displayed, accents and all. |
| `role` | Free text: `PhD student`, `Co-director`, `Visiting researcher`. |
| `group` | Which section they appear under: `faculty`, `postdoc`, `phd`, `ms`, `undergrad`, `collaborator`, `alumni`. |
| `order` | Optional integer for manual ordering inside a group. |
| `dblp_pid` | The part after `/pid/` in their DBLP URL, e.g. `70/3474`. |
| `aliases` | Semicolon-separated name variants DBLP uses. |
| `affiliation`, `started`, `ended`, `now`, `topic` | Shown on their page. |
| `homepage`, `scholar`, `github` | Optional links. |
| `pub_from`, `pub_to` | Optional year window — use it so an alumnus's later papers don't land in the lab list. |

**Changing someone's role** is one cell. Moving them to alumni is two: set
`group` to `alumni` and fill in `ended` and `now`.

Members without a `dblp_pid` still get credit: the script matches author names
from other members' records, folding accents, so `Marco Aurelio Gerosa` in DBLP
matches `Marco Aurélio Gerosa` in the CSV. Add an `aliases` entry for anything
folding cannot catch.

### A new project

1. Add a row to `data/projects.csv`.
2. Optionally write `data/projects/<slug>.md` for the long description.
3. Run the build.

The row alone produces a full project page. The Markdown file only supplies the
prose under "About". Funding columns (`funder`, `program`, `award_no`,
`award_url`, `amount`, `role`) do double duty: they render on the project page
*and* build `funding.html`, grouped by funder with subtotals. There is no
separate funding file to keep in sync.

`members` takes semicolon-separated member slugs. Anyone who co-authored one of
the project's papers is added automatically, so you only list people whose
involvement the papers do not already show.

### A new paper

Nothing to do. The monthly job re-reads every member's DBLP record and picks it
up.

**Alumni are filtered.** Their DBLP records hold a whole career, and harvesting
all of it would fill the list with work the lab had no part in. One rule decides:

> a paper counts if at least one author was in the lab when it appeared.

Current members are always in the lab. An alumnus is in the lab for years inside
`[started, ended + 1]` from `members.csv`.

| Situation | Result |
| --- | --- |
| A current member is an author | kept |
| An alumnus, and the year is inside their window | kept |
| Every author had left, or had not yet arrived | dropped |
| Dates unknown, another lab member is a co-author | kept |
| Dates unknown, they are there alone | dropped |

**Both bounds matter, and `started` matters most for visiting scholars.** Someone
who spent 2022 here has decades of publications either side of that visit; a rule
that only checked the departure year would let every earlier one through.

Years are enough — no months — and either bound helps on its own. A missing
`started` leaves the window open at the bottom, a missing `ended` open at the top,
and the build warns you which alumni are dated on one side only.

`dropped_pubs.md` is regenerated every build and lists everything the rule
removed, grouped by person, with each DBLP key. Nothing disappears quietly. To
rescue one, put its key in `data/include_pubs.txt`. Two things you may want to add by hand, in `data/pub_tags.csv`:

- `award` — DBLP does not record awards.
- `projects` — semicolon-separated project slugs, which puts the paper on those
  project pages and shows project chips under the paper.

To find a paper's DBLP key, look in `pub_index.csv` (regenerated every build,
listing every harvested paper) or read it off the DBLP record URL.

To hide a paper — a member's work from outside the lab, or a duplicate record —
add its key to `data/exclude_pubs.txt`.

### A full-text link for a paper

The build picks the first of these that exists:

1. `publications/<dblp-key-with-dashes>.pdf` — self-hosted manuscript
2. Unpaywall's best open-access location, found via the paper's DOI
3. An arXiv preprint, matched from DBLP's CoRR entries by title

`missing_pdfs.md` lists every paper with none of the three, and gives the exact
filename to use for each. That file is your to-do list.

### News, talks, presentations

Add a row to `data/news.csv`. Put project slugs in the `projects` column and the
item also appears under "News and presentations" on those project pages. For
anything longer than the one-line `summary`, write `data/news/<slug>.md`.

An optional `image` column takes a path relative to the site root (e.g.
`assets/news/20260601-launch.jpg`). When set, it shows as a small thumbnail on
every list the item appears on (home, `news.html`, project pages) and as a
full-width hero image at the top of the item's own page. Leave it blank for a
text-only item — nothing breaks either way.

`news.html` shows only the 5 most recent items by default, with a "View more"
button that reveals the rest. All items are present in the page's HTML either
way, so nothing is hidden from search engines — the button just toggles
visibility client-side.

---

## How it fits together

```
data/members.csv ──┬─→ dblp.org/pid/<pid>.xml ──→ dedupe by DBLP key
                   │                                    │
                   │        Unpaywall (by DOI) ──────────┤
                   │        arXiv (CoRR titles) ─────────┤
                   │        publications/*.pdf ──────────┤
                   │                                     ↓
                   ├────────────────────────→  publications.html  (?member= filter)
                   ├────────────────────────→  people.html, people/<slug>.html
                   │                                     ↑
data/pub_tags.csv ─┴──── project + award tags ───────────┤
                                                         │
data/projects.csv ──┬──→ projects.html, projects/<slug>.html
                    └──→ funding.html  (grouped, subtotalled)
data/news.csv ──────────→ news.html + each project's news section
```

Attribution is exact rather than guessed: because each paper is harvested from a
specific member's DBLP record, we know whose it is without matching names. Name
folding is the fallback for members who have no DBLP record of their own.

## Publication filtering

`publications.html` renders every paper server-side with a
`data-members="slug slug"` attribute, then a small script filters on the client.
Clicking a name on `people.html` goes to that person's own page, which lists
their papers as static HTML — so it works with JavaScript off and search engines
index it. `publications.html?member=<slug>` deep-links the filtered view.

## Generated files — do not edit by hand

`index.html`, `people.html`, `publications.html`, `projects.html`,
`funding.html`, `news.html`, `people/*.html`, `projects/*.html`, `sitemap.xml`,
`robots.txt`, `pub_index.csv`, `missing_pdfs.md`, `cache/*`.

Edits here are overwritten on the next build. Change `data/`, `assets/style.css`,
or the templates in `scripts/build_site.py` instead.

## Hosting (GitHub Pages)

Lives in `RESHAPELab/RESHAPELab.github.io` — the organization site repo, so it
serves from the domain root rather than a `/reponame/` subpath.

During the transition the workflow deploys from the `static-site` branch
(`DEPLOY_BRANCH` at the top of `.github/workflows/build.yml`), leaving `main`
and its Vercel deployment alone. After cutover, set it to `main`.

Set **Settings → Pages → Source** to **GitHub Actions**, not "Deploy from a
branch". `.github/workflows/build.yml` builds, commits the regenerated files, and
deploys in a single run.

This matters: commits pushed by a workflow using `GITHUB_TOKEN` do not trigger a
Pages build. With branch deploys, the monthly DBLP refresh would commit new HTML
that never went live. Deploying from inside the same run removes that dependency.

The workflow runs on every push to `main`, on the 1st of each month (with
`--refresh-dblp`), and on demand from the Actions tab. If the commit step fails
with a permissions error, set **Settings → Actions → General → Workflow
permissions** to **Read and write**.

Because this is an organization site, its custom domain is inherited by every
other Pages site in the org: any RESHAPELab repo with Pages enabled is served at
`www.reshapelab.site/<repo>/`. Keep Pages switched off on repos you do not want
published there — including the archived `reshapelab` Vue repo.

Full walkthrough, including the DNS cutover from Vercel: **[WALKTHROUGH.md](WALKTHROUGH.md)**.

### Custom domain

Enter `www.reshapelab.site` under Settings → Pages → Custom domain, then tick
**Enforce HTTPS**. At your DNS provider:

| Type | Name | Value |
| --- | --- | --- |
| CNAME | `www` | `reshapelab.github.io` |
| A | `@` | `185.199.108.153`, `185.199.109.153`, `185.199.110.153`, `185.199.111.153` |
| AAAA | `@` | `2606:50c0:8000::153`, `2606:50c0:8001::153`, `2606:50c0:8002::153`, `2606:50c0:8003::153` |

The apex records are what make `reshapelab.site` redirect to the `www` version.
DNS can take up to 24 hours; the HTTPS certificate is issued after both names
resolve. Verify with `dig www.reshapelab.site +noall +answer`.

Without a custom domain the site serves from `https://reshapelab.github.io/`.
Every internal link is relative, so it works on either URL — but set `SITE_URL`
so `sitemap.xml` carries the right host:

    SITE_URL=https://reshapelab.github.io python scripts/build_site.py

## Flags

| Flag | Effect |
| --- | --- |
| `--offline` | Build from `cache/` only. No network. |
| `--refresh-dblp` | Ignore the DBLP cache and refetch every record. |
| `--no-oa` | Skip the Unpaywall check (much faster). |
| `--refresh-oa` | Re-query every DOI against Unpaywall. |
| `--deep` | Also search the arXiv API by title for unmatched papers (~3 s each). |

Editing CSVs in Excel is safe: it saves as Mac Roman or cp1252 rather than
UTF-8, and every reader here detects that and decodes it correctly, warning you
to re-save. Files this project writes are always UTF-8.

Every build ends with a warning list — missing photos, unknown member slugs in
`projects.csv`, DBLP keys in `pub_tags.csv` that match no paper. Read it; it is
usually a typo report.

## Design

The home page opens with a full-bleed masthead: the mark at 136px, the wordmark
as the `h1`, the expanded lab name, then the claim and a viewport-wide
contribution strip whose density tracks papers per year. The mark animates once
on load — wall, then the community cells, then the newcomer arriving through the
doorway — and holds still under `prefers-reduced-motion`.

Palette and type are inherited from igor.pro.br so the two sites read as
related: paper `#fafbfc`, ink `#1b1f24`, GitHub contribution greens, with
`--ink-green: #1d3329` for the logo outline. Space Grotesk for display, Source
Serif 4 for body, JetBrains Mono for metadata. Logo assets are in `assets/`:
full colour, reversed for dark backgrounds, single-colour via `currentColor`,
and a solid-fill favicon that survives 16 px.

## Setup checklist

- [ ] Fill in `dblp_pid` for every member who has a DBLP record
- [ ] Add photos to `assets/people/`
- [ ] Point the `CNAME` at the right domain and enable Pages on `main`
- [ ] Set `UNPAYWALL_EMAIL` in `scripts/build_site.py` if it should not be Igor's
- [ ] Run `python scripts/build_site.py` once locally and read the warnings

## Migrating the old Vue site (one-off)

Step-by-step walkthrough: **[WALKTHROUGH.md](WALKTHROUGH.md)**. In short:

`scripts/migrate_from_vue.py` imports the previous site's content. Clone the old
repo next to this one and run it once:

    git clone https://github.com/RESHAPELab/reshapelab ../reshapelab-old
    python scripts/migrate_from_vue.py ../reshapelab-old
    python scripts/build_site.py

It reads `public/members.json`, `funding.json`, `research_areas.json`,
`posts.json`, and `images/people/`, and writes `data/members.csv`,
`data/people/*.md`, `data/research.csv`, `data/projects.csv`, `data/news.csv`,
`data/news/*.md`, and downscaled square photos into `assets/people/`.

It never overwrites silently: existing files are copied to `*.pre-migration`
first, rows already in `members.csv` or `projects.csv` are merged rather than
replaced (projects match on award number, so existing slugs and URLs survive),
and every judgement call is printed at the end for review. Delete the script
once you are happy with the result.
