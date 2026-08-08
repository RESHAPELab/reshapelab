#!/usr/bin/env python3
"""
build_site.py — generate the RESHAPE Lab static site from the files in data/.

Everything on the site comes from four CSVs plus optional Markdown bodies:

    data/members.csv          roster; drives People, per-member pages, DBLP harvest
    data/projects.csv         projects + their funding; drives Projects and Funding
    data/news.csv             news items; drives News and per-project news
    data/pub_tags.csv         hand annotations on papers (awards, project links)
    data/projects/<slug>.md   optional long description for a project
    data/news/<slug>.md       optional long body for a news item
    data/exclude_pubs.txt     DBLP keys to drop from the publication list

Publications are harvested from DBLP, one author record per member PID, then
deduplicated by DBLP key. Because we know which PID a paper came from, the
paper-to-member link is exact — no author-name matching required.

Full-text link precedence, highest first:
    1. publications/<dblp-key-with-dashes>.pdf   self-hosted accepted manuscript
    2. Unpaywall best OA location                published version is open access
    3. arXiv preprint                            matched via DBLP's CoRR entries

Usage:
    python scripts/build_site.py                 # normal build (network)
    python scripts/build_site.py --offline       # build from cache/dblp only
    python scripts/build_site.py --refresh-dblp  # ignore the DBLP cache
    python scripts/build_site.py --no-oa         # skip the Unpaywall check
    python scripts/build_site.py --refresh-oa    # re-query every DOI
    python scripts/build_site.py --deep          # also search the arXiv API

Writes: index.html, people.html, publications.html, research.html,
funding.html, news.html, people/<slug>.html, projects/<slug>.html,
sitemap.xml, missing_pdfs.md, cache/oa_cache.json, cache/dblp/<pid>.xml

No dependencies beyond the Python standard library.
"""

import csv
import html
import io
import json
import os
import re
import sys
import time
import unicodedata
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from collections import defaultdict
from pathlib import Path

# ---------------------------------------------------------------- configuration

SITE_NAME = "RESHAPE Lab"
SITE_TAGLINE = "Research in Software: Human Aspects, Practices and Education"
SITE_URL = os.environ.get("SITE_URL", "https://www.reshapelab.site").rstrip("/")
# Override for a project-path deploy, e.g.
#   SITE_URL=https://reshapelab.github.io/reshapelab python scripts/build_site.py
INSTITUTION = "School of Informatics, Computing and Cyber Systems · Northern Arizona University"
UNPAYWALL_EMAIL = "igor.steinmacher@nau.edu"

# Alumni carry a whole career in their DBLP record, and harvesting all of it
# would fill the list with work the lab had no part in. Two rules together
# decide what counts as lab output:
#
# Rule 1 — time window:
#     a paper counts if at least one author was in the lab when it appeared.
#
# Current members are always in the lab. An alumnus is in the lab for years
# inside [started, ended + grace] from members.csv. Both bounds matter — a
# visiting scholar who spent 2022 here has decades of publications either side
# of that, and a rule that only checks the departure year lets all the earlier
# ones through.
#
# Rule 2 — faculty anchor (REQUIRE_FACULTY_AUTHOR):
#     the paper must have at least one faculty member (group == "faculty")
#     as an author. Work done by students or visitors independently, without
#     Igor or Marco as co-authors, is not lab output.
#
# When an alumnus has no dates at all we cannot judge, so we fall back to
# co-authorship: keep the paper if another lab member is on it, drop it if they
# are there alone.
#
# Escape hatches: `data/include_pubs.txt` force-keeps a DBLP key,
# `data/exclude_pubs.txt` force-drops one, and `pub_from`/`pub_to` in
# members.csv bound an individual's harvest before any of this runs.
ALUMNI_GRACE_YEARS = 1   # a paper can appear a year after someone leaves

# Attribution policy. A DBLP pid is an exact link: every paper in that record is
# provably theirs. Matching on author names instead is a guess, and Brazilian SE
# has enough shared surnames that the guess is sometimes wrong — crediting the
# lab with a stranger's paper is worse than crediting nobody.
#
# With this False, a member without a `dblp_pid` gets no papers: their page is
# empty and their name is not linked in author lists. The fix is their pid, not
# a looser rule. The build lists who is missing one.
ATTRIBUTE_BY_NAME = False

# The one judgement call in the alumni rule. Two former members who have both
# left co-author a paper — say two alumni now at the same new university.
#
#   False (default) : dropped. They left; this is their own career now.
#   True            : kept. Two lab people on a paper is enough, whenever.
#
# Only reachable when BOTH have dates showing they had left. If either lacks
# dates the paper is kept regardless, and a paper with any current member on it
# is always kept.
KEEP_IF_TWO_DEPARTED_ALUMNI = False

# Papers harvested from students, visitors, and other non-faculty members must
# have at least one faculty member (group == "faculty") as an author to appear
# on the lab list. This removes work done independently during someone's stay
# that was not part of the lab's research agenda.
#
# Force-keep individual exceptions via data/include_pubs.txt.
REQUIRE_FACULTY_AUTHOR = True
REPO_URL = "https://github.com/RESHAPELab/reshapelab"

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data"
PUB_DIR = ROOT / "publications"
PHOTO_DIR = ROOT / "assets" / "people"
CACHE = ROOT / "cache"
DBLP_CACHE = CACHE / "dblp"
OA_CACHE = CACHE / "oa_cache.json"

# Order that member groups appear on the People page. Anything not listed here
# is appended at the end, alphabetically by group name.
GROUP_ORDER = [
    ("faculty", "Faculty"),
    ("postdoc", "Postdoctoral researchers"),
    ("phd", "PhD students"),
    ("ms", "Master's students"),
    ("undergrad", "Undergraduate researchers"),
    ("collaborator", "Collaborators"),
    ("alumni", "Alumni"),
]

NAV = [
    ("index.html", "Home"),
    ("people.html", "People"),
    ("publications.html", "Publications"),
    ("research.html", "Research"),
    ("funding.html", "Funding"),
    ("news.html", "News"),
]

ARXIV_ID_RE = re.compile(r"(?:arxiv\.org/(?:abs|pdf)/|arXiv\.)(\d{4}\.\d{4,5})", re.I)
AUTHOR_SUFFIX_RE = re.compile(r"\s+\d{4}$")
DOI_RE = re.compile(r"doi\.org/(10\.[^\s\"]+)", re.I)

MARK_SVG = (
    '<svg viewBox="0 0 84 82" aria-hidden="true">'
    '<path d="M40,2 L73,21 L73,32" fill="none" stroke="#1d3329" stroke-width="4" '
    'stroke-linejoin="round" stroke-linecap="round"/>'
    '<path d="M73,48 L73,59 L40,78 L7,59 L7,21 L40,2" fill="none" stroke="#1d3329" '
    'stroke-width="4" stroke-linejoin="round" stroke-linecap="round"/>'
    '<rect x="26" y="25" width="11" height="11" rx="2" fill="#216e39"/>'
    '<rect x="26" y="42" width="11" height="11" rx="2" fill="#30a14e"/>'
    '<rect x="42" y="33" width="11" height="11" rx="2" fill="#30a14e"/>'
    '<rect x="67.5" y="34" width="11" height="11" rx="2" fill="#40c463"/>'
    "</svg>"
)

# Large masthead mark. Same geometry as assets/logo-mark.svg, with classes so
# the entrance can be choreographed: wall, community, then the arriving cell.
HERO_MARK_SVG = (
    '<svg class="mark" viewBox="0 0 84 82" role="img" '
    'aria-label="The RESHAPE Lab mark: an open hexagon with a cell entering through the gap">'
    '<path class="wall" d="M40,2 L73,21 L73,32" fill="none" stroke="#1d3329" '
    'stroke-width="4" stroke-linejoin="round" stroke-linecap="round"/>'
    '<path class="wall" d="M73,48 L73,59 L40,78 L7,59 L7,21 L40,2" fill="none" '
    'stroke="#1d3329" stroke-width="4" stroke-linejoin="round" stroke-linecap="round"/>'
    '<rect class="cell c1" x="26" y="25" width="11" height="11" rx="2" fill="#216e39"/>'
    '<rect class="cell c2" x="26" y="42" width="11" height="11" rx="2" fill="#30a14e"/>'
    '<rect class="cell c3" x="42" y="33" width="11" height="11" rx="2" fill="#30a14e"/>'
    '<rect class="newcomer" x="67.5" y="34" width="11" height="11" rx="2" fill="#40c463"/>'
    "</svg>"
)


# ---------------------------------------------------------------------- helpers


def esc(s) -> str:
    return html.escape(str(s or ""), quote=True)


def slugify(s: str) -> str:
    s = re.sub(r"[^a-z0-9]+", "-", (s or "").lower().strip())
    return s.strip("-")


def key_slug(key: str) -> str:
    """DBLP key -> safe filename: conf/icse/Smith16 -> conf-icse-Smith16."""
    return key.replace("/", "-")


def clean_author(name: str) -> str:
    return AUTHOR_SUFFIX_RE.sub("", (name or "").strip())


def norm_title(t: str) -> str:
    return re.sub(r"[^a-z0-9]+", "", (t or "").lower())


def fold(name: str) -> str:
    """Accent- and punctuation-insensitive key for matching people's names.

    DBLP writes 'Marco Aurelio Gerosa' where the roster says 'Marco Aurélio
    Gerosa'; without folding, the author would never match the member.
    """
    decomposed = unicodedata.normalize("NFKD", (name or "").lower())
    stripped = "".join(c for c in decomposed if not unicodedata.combining(c))
    return re.sub(r"[^a-z0-9]+", " ", stripped).strip()


def split_list(s: str):
    """Split a semicolon- or comma-separated cell into a clean list."""
    if not s:
        return []
    parts = re.split(r"[;,]", s)
    return [p.strip() for p in parts if p.strip()]



# Excel on macOS saves CSV as Mac Roman by default, and on Windows as cp1252.
# Either produces bytes that are not valid UTF-8 — a name like "João" becomes a
# lone 0x8b — and the plain reader dies on it. Rather than lecture the user
# about export settings, decode whatever they hand us.
CSV_ENCODINGS = ("utf-8-sig", "utf-8", "cp1252", "mac_roman", "latin-1")
_PLAUSIBLE = set("áàâãäçéêëíîïóôõöúûüñÁÀÂÃÄÇÉÊËÍÎÏÓÔÕÖÚÛÜÑ")
_IMPLAUSIBLE = set("‹›†‡•˘˝¸˛ˇ¤¦¨¯²³¹¼½¾×÷þýÿ")


def decode_bytes(raw):
    """Decode CSV bytes, guessing the encoding. Returns (text, encoding_name).

    UTF-8 wins outright when it fits. Otherwise several legacy encodings will
    all "work" but produce different letters, so we score each by how many
    plausible accented characters it yields versus how many typographic oddities
    — Portuguese names decode cleanly under the right one and turn to symbol
    soup under the wrong one.
    """
    best = None
    for enc in CSV_ENCODINGS:
        try:
            text = raw.decode(enc)
        except UnicodeDecodeError:
            continue
        if enc in ("utf-8-sig", "utf-8"):
            return text, enc
        score = sum(c in _PLAUSIBLE for c in text) - 2 * sum(c in _IMPLAUSIBLE for c in text)
        if best is None or score > best[0]:
            best = (score, text, enc)
    if best:
        return best[1], best[2]
    return raw.decode("utf-8", errors="replace"), "utf-8 (with replacements)"


def read_csv(path: Path):
    """Read a CSV, skipping blank lines and rows whose first cell starts with #."""
    if not path.exists():
        warn(f"{path.relative_to(ROOT)} not found — skipping")
        return []
    text, enc = decode_bytes(path.read_bytes())
    if not enc.startswith("utf-8"):
        warn(f"{path.relative_to(ROOT)} is {enc}, not UTF-8 (Excel does this) — "
             f"it was read correctly, but re-save it as UTF-8 to be safe")
    with io.StringIO(text, newline="") as fh:
        rows = []
        for row in csv.DictReader(fh):
            if not row:
                continue
            first = (list(row.values())[0] or "").strip()
            if not first or first.startswith("#"):
                continue
            rows.append({(k or "").strip(): (v or "").strip() for k, v in row.items()})
        return rows


WARNINGS: list[str] = []


def warn(msg: str) -> None:
    WARNINGS.append(msg)


def fetch(url: str, *, retries: int = 5, backoff: float = 5.0) -> bytes:
    """Fetch a URL with exponential backoff on connection errors.

    Retries on any OSError (including ECONNRESET) and HTTP 429/503.
    Waits backoff * 2^attempt seconds between tries, plus up to 2s of jitter.
    """
    import random
    req = urllib.request.Request(url, headers={"User-Agent": "reshapelab-site-builder/1.0"})
    last_exc: Exception = RuntimeError("no attempts made")
    for attempt in range(retries):
        if attempt:
            wait = backoff * (2 ** (attempt - 1)) + random.uniform(0, 2)
            print(f"  retrying in {wait:.0f}s (attempt {attempt + 1}/{retries}) …",
                  flush=True)
            time.sleep(wait)
        try:
            with urllib.request.urlopen(req, timeout=60) as r:
                if r.status in (429, 503):
                    last_exc = OSError(f"HTTP {r.status}")
                    continue
                return r.read()
        except urllib.error.HTTPError as exc:
            if exc.code in (429, 503):
                last_exc = exc
                continue
            raise
        except OSError as exc:
            last_exc = exc
            continue
    raise last_exc


def money(v: str) -> str:
    """'731000' or '$731K' -> 'USD 731K'. Pass through anything unparseable."""
    if not v:
        return ""
    raw = v.replace(",", "").replace("$", "").strip()
    m = re.fullmatch(r"(\d+(?:\.\d+)?)([KkMm]?)", raw)
    if not m:
        return v
    num, suffix = float(m.group(1)), m.group(2).upper()
    if not suffix:
        if num >= 1_000_000:
            num, suffix = num / 1_000_000, "M"
        elif num >= 1000:
            num, suffix = num / 1000, "K"
    txt = f"{num:.0f}" if num == int(num) else f"{num:.1f}"
    return f"USD {txt}{suffix}"


def money_value(v: str) -> float:
    """Numeric USD value for totals. 0 when unparseable."""
    if not v:
        return 0.0
    raw = v.replace(",", "").replace("$", "").strip()
    m = re.fullmatch(r"(\d+(?:\.\d+)?)([KkMm]?)", raw)
    if not m:
        return 0.0
    num = float(m.group(1))
    return num * {"": 1, "K": 1e3, "M": 1e6}[m.group(2).upper()]


# ------------------------------------------------------------- markdown (subset)


def md_inline(t: str) -> str:
    t = esc(t)
    t = re.sub(r"`([^`]+)`", r"<code>\1</code>", t)
    t = re.sub(r"\[([^\]]+)\]\(([^)]+)\)", r'<a href="\2">\1</a>', t)
    t = re.sub(r"\*\*([^*]+)\*\*", r"<strong>\1</strong>", t)
    t = re.sub(r"(?<!\*)\*([^*]+)\*(?!\*)", r"<em>\1</em>", t)
    return t


def md_to_html(text: str) -> str:
    """Paragraphs, ### headings, - bullets, links, bold, italic, inline code."""
    out, buf, in_ul = [], [], False

    def flush_p():
        if buf:
            out.append(f"<p>{md_inline(' '.join(buf))}</p>")
            buf.clear()

    def close_ul():
        nonlocal in_ul
        if in_ul:
            out.append("</ul>")
            in_ul = False

    for line in (text or "").splitlines():
        s = line.strip()
        if not s:
            flush_p()
            close_ul()
        elif s.startswith("### "):
            flush_p()
            close_ul()
            out.append(f"<h3>{md_inline(s[4:])}</h3>")
        elif s.startswith("## "):
            flush_p()
            close_ul()
            out.append(f"<h3>{md_inline(s[3:])}</h3>")
        elif s.startswith(("- ", "* ")):
            flush_p()
            if not in_ul:
                out.append('<ul class="clean">')
                in_ul = True
            out.append(f"<li>{md_inline(s[2:])}</li>")
        else:
            close_ul()
            buf.append(s)
    flush_p()
    close_ul()
    return "\n".join(out)


def read_body(path: Path) -> str:
    """Read a Markdown body file, stripping an optional '---' front-matter block."""
    if not path.exists():
        return ""
    text, _ = decode_bytes(path.read_bytes())
    if text.lstrip().startswith("---"):
        parts = text.lstrip().split("---", 2)
        if len(parts) >= 3:
            text = parts[2]
    return text.strip()


# --------------------------------------------------------------- page templates


def page(title, body, *, description="", nav_current="", depth=0, extra_head=""):
    up = "../" * depth
    nav = "\n      ".join(
        f'<a href="{up}{href}"'
        + (' aria-current="page"' if href == nav_current else "")
        + f">{label}</a>"
        for href, label in NAV
    )
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{esc(title)}</title>
<meta name="description" content="{esc(description or SITE_TAGLINE)}">
<meta property="og:title" content="{esc(title)}">
<meta property="og:description" content="{esc(description or SITE_TAGLINE)}">
<meta property="og:type" content="website">
<meta property="og:site_name" content="{esc(SITE_NAME)}">
<meta name="twitter:card" content="summary">
<link rel="icon" href="{up}assets/favicon.svg" type="image/svg+xml">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@500;700&family=Source+Serif+4:ital,wght@0,400;0,600;1,400&family=JetBrains+Mono:wght@400;500;600&display=swap" rel="stylesheet">
<link rel="stylesheet" href="{up}assets/style.css">
{extra_head}</head>
<body>
<a class="skip" href="#main">Skip to content</a>
<header class="site">
  <div class="row">
    <a class="brand" href="{up}index.html">{MARK_SVG}<span>RESHAPE<span class="lab">&nbsp;lab</span></span></a>
    <nav>
      {nav}
    </nav>
  </div>
</header>
<main id="main">
{body}
</main>
<footer>
  <div class="row">
    <span>&copy; {SITE_NAME} &middot; {esc(INSTITUTION)}</span>
    <a href="{REPO_URL}">source</a>
  </div>
</footer>
</body>
</html>
"""


def contrib_strip(pubs_by_year, columns=130):
    """A contribution-graph strip whose per-year density tracks papers per year.

    Deliberately sparse and irregular: a solid block of green reads as a
    decorative bar, while gaps make it read as the graph it is quoting.
    """
    if not pubs_by_year:
        return ""
    years = sorted(pubs_by_year)
    peak = max(len(v) for v in pubs_by_year.values()) or 1
    per_year = max(1, columns // len(years))
    columns = per_year * len(years)

    seed = 20260806
    def rnd():
        nonlocal seed
        seed = (seed * 1103515245 + 12345) & 0x7FFFFFFF
        return seed / 0x7FFFFFFF

    cells = []
    for col in range(columns):
        year = years[min(col // per_year, len(years) - 1)]
        density = len(pubs_by_year[year]) / peak
        for _ in range(7):
            r = rnd()
            if r > density * 0.92 + 0.06:
                cells.append("<span></span>")
                continue
            lvl = 1 + int(min(0.999, (density * 0.85 + rnd() * 0.5)) * 4)
            cells.append(f'<span class="l{min(lvl, 4)}"></span>')

    delayed = "".join(
        c.replace("<span", f'<span style="animation-delay:{i * 1.1:.0f}ms"', 1)
        for i, c in enumerate(cells)
    )
    return f'<div class="contrib" aria-hidden="true">{delayed}</div>'


# ------------------------------------------------------------------ data loading


def load_members():
    rows = read_csv(DATA / "members.csv")
    members, seen = [], set()
    for r in rows:
        name = r.get("name", "")
        if not name:
            continue
        slug = r.get("slug") or slugify(name)
        if slug in seen:
            warn(f"members.csv: duplicate slug '{slug}' — keeping the first")
            continue
        seen.add(slug)
        photo = None
        for ext in (".jpg", ".jpeg", ".png", ".webp"):
            if (PHOTO_DIR / f"{slug}{ext}").exists():
                photo = f"assets/people/{slug}{ext}"
                break
        if not photo:
            warn(f"no photo for '{slug}' — add assets/people/{slug}.jpg (initials shown)")
        members.append({
            "slug": slug,
            "name": name,
            "role": r.get("role", ""),
            "group": (r.get("group") or "collaborator").lower(),
            "order": int(r["order"]) if r.get("order", "").isdigit() else 500,
            "dblp_pid": r.get("dblp_pid", ""),
            "aliases": split_list(r.get("aliases", "")),
            "affiliation": r.get("affiliation", ""),
            "started": r.get("started", ""),
            "ended": r.get("ended", ""),
            "now": r.get("now", ""),
            "topic": r.get("topic", ""),
            "homepage": r.get("homepage", ""),
            "scholar": r.get("scholar", ""),
            "github": r.get("github", ""),
            "email": r.get("email", ""),
            "keywords": split_list(r.get("keywords", "")),
            "bio": read_body(DATA / "people" / f"{slug}.md"),
            "pub_from": r.get("pub_from", ""),
            "pub_to": r.get("pub_to", ""),
            "photo": photo,
            "pubs": [],
            "projects": [],
        })
    def sort_key(m):
        # alumni read best newest-first; everyone else alphabetically by surname
        if m["group"] == "alumni":
            year = m["ended"] or m["started"] or "0"
            return (m["order"], "".join(c for c in year if c.isdigit()).rjust(6, "0")[::-1])
        return (m["order"], m["name"].split()[-1].lower())

    members.sort(key=sort_key)
    alumni = [m for m in members if m["group"] == "alumni"]
    alumni.sort(key=lambda m: (m["ended"] or m["started"] or ""), reverse=True)
    others = [m for m in members if m["group"] != "alumni"]
    return others + alumni


def load_research():
    """Research areas shown on the home page and on research.html.

    Each area can list multiple project slugs (semicolon-separated) in the
    optional `projects` column. They are resolved to project objects in
    build_home() and build_research_areas() after projects are loaded.
    Falls back gracefully if research.csv is absent.
    """
    out = []
    for r in read_csv(DATA / "research.csv"):
        name = r.get("name", "")
        if not name:
            continue
        out.append({
            "slug": r.get("slug") or slugify(name),
            "name": name,
            "short": r.get("short", ""),
            "description": r.get("description", ""),
            "keywords": split_list(r.get("keywords", "")),
            "project_slugs": split_list(r.get("projects", "")),
            "projects": [],   # populated later once projects are loaded
        })
    return out


def load_projects():
    rows = read_csv(DATA / "projects.csv")
    projects = []
    for r in rows:
        title = r.get("title", "")
        if not title:
            continue
        slug = r.get("slug") or slugify(title)
        body_path = DATA / "projects" / f"{slug}.md"
        projects.append({
            "slug": slug,
            "title": title,
            "short": r.get("short", "") or title,
            "summary": r.get("summary", ""),
            "status": (r.get("status") or "active").lower(),
            "start": r.get("start", ""),
            "end": r.get("end", ""),
            "funder": r.get("funder", ""),
            "program": r.get("program", ""),
            "award_no": r.get("award_no", ""),
            "award_url": r.get("award_url", ""),
            "amount": r.get("amount", ""),
            "role": r.get("role", ""),
            "url": r.get("url", ""),
            "members": split_list(r.get("members", "")),
            "body": read_body(body_path),
            "has_body": body_path.exists(),
            "pubs": [],
            "news": [],
        })
    return projects


def load_news():
    rows = read_csv(DATA / "news.csv")
    items = []
    for r in rows:
        title = r.get("title", "")
        if not title:
            continue
        slug = r.get("slug") or slugify(title)[:60]
        items.append({
            "slug": slug,
            "date": r.get("date", ""),
            "title": title,
            "tag": r.get("tag", ""),
            "url": r.get("url", ""),
            "summary": r.get("summary", ""),
            "image": r.get("image", ""),   # optional path, e.g. assets/news/<slug>.jpg
            "projects": split_list(r.get("projects", "")),
            "body": read_body(DATA / "news" / f"{slug}.md"),
        })
    items.sort(key=lambda n: n["date"], reverse=True)
    return items


def load_pub_tags():
    tags = {}
    for r in read_csv(DATA / "pub_tags.csv"):
        key = r.get("dblp_key", "")
        if not key:
            continue
        tags[key] = {
            "award": r.get("award", ""),
            "projects": split_list(r.get("projects", "")),
            "note": r.get("note", ""),
        }
    return tags


# -------------------------------------------------------------- DBLP harvesting


def dblp_xml(pid: str, *, offline: bool, refresh: bool) -> ET.Element | None:
    """Fetch a DBLP author record, caching the XML under cache/dblp/."""
    cache_file = DBLP_CACHE / f"{pid.replace('/', '-')}.xml"
    if cache_file.exists() and (offline or not refresh):
        try:
            return ET.fromstring(cache_file.read_bytes())
        except ET.ParseError:
            warn(f"cached DBLP XML for {pid} is corrupt — refetching")
    if offline:
        warn(f"offline and no cache for DBLP pid {pid} — skipped")
        return None
    try:
        raw = fetch(f"https://dblp.org/pid/{pid}.xml")
    except Exception as exc:
        warn(f"DBLP fetch failed for {pid}: {exc}")
        if cache_file.exists():
            return ET.fromstring(cache_file.read_bytes())
        return None
    DBLP_CACHE.mkdir(parents=True, exist_ok=True)
    cache_file.write_bytes(raw)
    time.sleep(3.0)  # DBLP rate-limits burst requests; 3s keeps us well clear
    return ET.fromstring(raw)


def extract_doi(pub) -> str | None:
    for ee in pub.findall("ee"):
        m = DOI_RE.search(ee.text or "")
        if m:
            return m.group(1).rstrip(".")
    return None


def arxiv_pdf_url(s: str) -> str | None:
    m = ARXIV_ID_RE.search(s or "")
    return f"https://arxiv.org/pdf/{m.group(1)}" if m else None


def arxiv_api_lookup(title: str) -> str | None:
    q = urllib.parse.quote(f'ti:"{title}"')
    try:
        root = ET.fromstring(fetch(f"https://export.arxiv.org/api/query?search_query={q}&max_results=3"))
    except Exception:
        return None
    ns = {"a": "http://www.w3.org/2005/Atom"}
    want = norm_title(title)
    for entry in root.findall("a:entry", ns):
        if norm_title(entry.findtext("a:title", default="", namespaces=ns)) == want:
            pdf = arxiv_pdf_url(entry.findtext("a:id", default="", namespaces=ns))
            if pdf:
                return pdf
    return None


def unpaywall_lookup(doi: str) -> dict:
    url = f"https://api.unpaywall.org/v2/{urllib.parse.quote(doi)}?email={UNPAYWALL_EMAIL}"
    try:
        data = json.loads(fetch(url))
        loc = data.get("best_oa_location") or {}
        return {"is_oa": bool(data.get("is_oa")), "oa_url": loc.get("url_for_pdf") or loc.get("url")}
    except Exception:
        return {"is_oa": False, "oa_url": None, "error": True}


def harvest(members, *, offline, refresh_dblp):
    """Collect papers from every member's DBLP record. Returns (pubs, preprints)."""
    excluded = set()
    ex_file = DATA / "exclude_pubs.txt"
    if ex_file.exists():
        for line in ex_file.read_text(encoding="utf-8").splitlines():
            line = line.split("#")[0].strip()
            if line:
                excluded.add(line)

    pubs: dict[str, dict] = {}
    preprints: dict[str, str] = {}
    with_pid = [m for m in members if m["dblp_pid"]]
    if not with_pid:
        warn("no member has a dblp_pid — the publication list will be empty")

    for m in with_pid:
        root = dblp_xml(m["dblp_pid"], offline=offline, refresh=refresh_dblp)
        if root is None:
            continue
        y_from = int(m["pub_from"]) if m["pub_from"].isdigit() else None
        y_to = int(m["pub_to"]) if m["pub_to"].isdigit() else None

        for r in root.iter("r"):
            if not len(r):
                continue
            pub = r[0]

            # arXiv preprints live as separate "informal" CoRR entries
            if pub.get("publtype") == "informal":
                title = (pub.findtext("title") or "").strip().rstrip(".")
                for ee in pub.findall("ee"):
                    pdf = arxiv_pdf_url(ee.text or "")
                    if pdf:
                        preprints[norm_title(title)] = pdf
                        break
                continue

            if pub.tag not in ("article", "inproceedings"):
                continue
            key = pub.get("key", "")
            if not key or key in excluded:
                continue

            year_txt = (pub.findtext("year") or "").strip()
            year = int(year_txt) if year_txt.isdigit() else 0
            if y_from and year and year < y_from:
                continue
            if y_to and year and year > y_to:
                continue

            if key in pubs:
                pubs[key]["members"].add(m["slug"])
                continue

            vol, pages = pub.findtext("volume"), pub.findtext("pages")
            detail = ""
            if pub.tag == "article" and vol:
                detail = f" {vol}" + (f": {pages}" if pages else "")

            pubs[key] = {
                "key": key,
                "kind": "journal" if pub.tag == "article" else "conference",
                "year": year_txt or "????",
                "title": (pub.findtext("title") or "").strip().rstrip("."),
                "authors": [clean_author(a.text or "") for a in pub.findall("author")],
                "venue": (pub.findtext("journal") or pub.findtext("booktitle") or "").strip(),
                "detail": detail,
                "ee": pub.findtext("ee") or "",
                "doi": extract_doi(pub),
                "members": {m["slug"]},
            }
    return pubs, preprints


def attribute_by_name(pubs, members):
    """Credit papers to members by author name as well as by DBLP pid.

    A pid gives an exact link, but most students do not have a curated DBLP
    record. Folding names (accents, punctuation) catches the rest, and the
    `aliases` column in members.csv handles genuine spelling variants.
    """
    index = {}
    for m in members:
        for variant in [m["name"], *m["aliases"]]:
            key = fold(variant)
            if not key:
                continue
            if key in index and index[key] != m["slug"]:
                warn(f"members.csv: '{variant}' maps to both "
                     f"'{index[key]}' and '{m['slug']}' — add distinct aliases")
                continue
            index[key] = m["slug"]

    for p in pubs.values():
        for author in p["authors"]:
            slug = index.get(fold(author))
            if slug:
                p["members"].add(slug)


def in_lab_when(member, year):
    """Was this member in the lab in `year`? True / False / None for unknown.

    Current members are always in. Alumni are judged against whichever of
    `started` and `ended` is filled in; with neither, the answer is unknown and
    the caller falls back to co-authorship.
    """
    if member["group"] != "alumni":
        return True
    lo = int(member["started"]) if member["started"].isdigit() else None
    hi = (int(member["ended"]) + ALUMNI_GRACE_YEARS
          if member["ended"].isdigit() else None)
    if lo is None and hi is None:
        return None
    if not year:
        return None
    if lo is not None and year < lo:
        return False
    if hi is not None and year > hi:
        return False
    return True


def filter_pubs(pubs, members_by_slug):
    """Keep a paper only if it passes both lab-membership rules:

    1. At least one author was in the lab during the paper's year (time window).
    2. If REQUIRE_FACULTY_AUTHOR is True, at least one author must be faculty.

    Returns (dropped, needs_date) so the build can report them — silently
    discarding publications would be worse than keeping a few strays.
    Force-keep individual exceptions via data/include_pubs.txt.
    """
    forced = set()
    inc_file = DATA / "include_pubs.txt"
    if inc_file.exists():
        for line in inc_file.read_text(encoding="utf-8").splitlines():
            line = line.split("#")[0].strip()
            if line:
                forced.add(line)

    faculty_slugs = {
        m["slug"] for m in members_by_slug.values() if m["group"] == "faculty"
    }

    undated = set()
    dropped = []
    for key in list(pubs):
        p = pubs[key]
        if key in forced:
            continue
        labs = [members_by_slug[s] for s in p["members"] if s in members_by_slug]
        if not labs:
            continue

        year = int(p["year"]) if p["year"].isdigit() else 0
        verdicts = [in_lab_when(m, year) for m in labs]

        # Rule 1: time window
        if any(v is True for v in verdicts):
            pass  # someone was here — proceed to rule 2
        elif all(v is False for v in verdicts):
            if KEEP_IF_TWO_DEPARTED_ALUMNI and len(labs) >= 2:
                pass  # two lab names is enough, by policy — proceed to rule 2
            else:
                dropped.append((p, labs, "time"))
                del pubs[key]
                continue
        else:
            # at least one unknown: fall back to co-authorship
            undated.update(m["slug"] for m, v in zip(labs, verdicts) if v is None)
            if len(labs) < 2:
                dropped.append((p, labs, "time"))
                del pubs[key]
                continue

        # Rule 2: faculty anchor
        if REQUIRE_FACULTY_AUTHOR:
            if not any(s in faculty_slugs for s in p["members"]):
                dropped.append((p, labs, "faculty"))
                del pubs[key]
                continue

    # Only alumni who have a DBLP pid feed the harvest, so only they are worth
    # dating. Everyone else is credited by name off someone else's record.
    needs_date = sorted(
        m["name"] for m in members_by_slug.values()
        if m["group"] == "alumni" and m["dblp_pid"]
        and not (m["started"].isdigit() or m["ended"].isdigit())
    )
    if needs_date:
        warn(f"{len(needs_date)} alumni have a DBLP pid but neither `started` nor "
             f"`ended`, so papers they co-author with each other are kept by "
             f"default: {', '.join(needs_date)}")
    half = sorted(
        f'{m["name"]} (no {"started" if not m["started"].isdigit() else "ended"})'
        for m in members_by_slug.values()
        if m["group"] == "alumni" and m["dblp_pid"]
        and m["started"].isdigit() != m["ended"].isdigit()
    )
    if half:
        warn(f"{len(half)} alumni are dated on one side only — the open end is "
             f"unbounded: {', '.join(half)}")
    return dropped, needs_date


def build_dropped_report(dropped, needs_date):
    time_dropped = [(p, labs) for p, labs, reason in dropped if reason == "time"]
    faculty_dropped = [(p, labs) for p, labs, reason in dropped if reason == "faculty"]

    by_member_time = defaultdict(list)
    for p, labs in time_dropped:
        for m in labs:
            by_member_time[m["name"]].append(p)

    by_member_faculty = defaultdict(list)
    for p, labs in faculty_dropped:
        for m in labs:
            by_member_faculty[m["name"]].append(p)

    lines = [
        "# Publications left out of the list",
        "",
        f"`scripts/build_site.py` dropped {len(dropped)} paper(s) total:",
        f"- {len(time_dropped)} dropped because no author was in the lab at the time",
        f"- {len(faculty_dropped)} dropped because no faculty member (Igor / Marco) was an author",
        "",
        "If one of these belongs on the site, add its DBLP key to",
        "`data/include_pubs.txt` and it will be kept on the next build.",
        "",
    ]
    if needs_date:
        lines += [
            "## Alumni with no dates",
            "",
            "These alumni have a DBLP pid but neither `started` nor `ended` in",
            "`data/members.csv`, so the rule cannot tell lab-era collaboration from work",
            "they did together before or after their time here. Papers they co-author",
            "with each other are kept by default.",
            "",
            "Years are enough — no months — and either bound helps on its own. `started`",
            "matters most for visiting scholars, whose careers extend well before the",
            "visit. Alumni without a pid are unaffected either way.",
            "",
        ] + [f"- {n}" for n in needs_date] + [""]

    if time_dropped:
        lines += ["## Dropped: no author in lab at the time", ""]
        for name in sorted(by_member_time):
            papers = sorted(by_member_time[name], key=lambda p: p["year"], reverse=True)
            lines.append(f"### {name} ({len(papers)})")
            lines.append("")
            for p in papers:
                lines.append(f'- `{p["key"]}` — {p["year"]} — **{p["title"]}** — *{p["venue"]}*')
            lines.append("")

    if faculty_dropped:
        lines += ["## Dropped: no faculty author (Igor / Marco not on the paper)", ""]
        for name in sorted(by_member_faculty):
            papers = sorted(by_member_faculty[name], key=lambda p: p["year"], reverse=True)
            lines.append(f"### {name} ({len(papers)})")
            lines.append("")
            for p in papers:
                lines.append(f'- `{p["key"]}` — {p["year"]} — **{p["title"]}** — *{p["venue"]}*')
            lines.append("")

    write(ROOT / "dropped_pubs.md", "\n".join(lines))


def resolve_links(pubs, preprints, *, use_oa, refresh_oa, deep, offline):
    """Attach a full-text link to each paper. Returns the list needing a PDF."""
    oa_cache = {}
    if use_oa and OA_CACHE.exists() and not refresh_oa:
        try:
            oa_cache = json.loads(OA_CACHE.read_text())
        except Exception:
            oa_cache = {}

    missing = []
    for p in pubs.values():
        local = PUB_DIR / f"{key_slug(p['key'])}.pdf"
        oa = None
        if use_oa and p["doi"] and not local.exists():
            cached = oa_cache.get(p["doi"])
            if cached and not cached.get("error"):
                oa = cached
            elif not offline:
                oa = unpaywall_lookup(p["doi"])
                oa_cache[p["doi"]] = oa
                time.sleep(0.15)

        arxiv = preprints.get(norm_title(p["title"]))
        if arxiv is None and deep and not offline and not local.exists() and not (oa and oa.get("is_oa")):
            time.sleep(3)  # arXiv API etiquette
            arxiv = arxiv_api_lookup(p["title"])

        if local.exists():
            p["link"] = (f"publications/{local.name}", "PDF")
        elif oa and oa.get("is_oa"):
            p["link"] = (oa.get("oa_url") or f"https://doi.org/{p['doi']}", "open access")
        elif arxiv:
            p["link"] = (arxiv, "preprint PDF")
        else:
            p["link"] = None
            missing.append(p)

    if use_oa and not offline:
        CACHE.mkdir(parents=True, exist_ok=True)
        OA_CACHE.write_text(json.dumps(oa_cache, indent=0, sort_keys=True))
    return missing


# ------------------------------------------------------------------- rendering


def render_pub(p, members_by_slug, *, depth=0, show_tags=True, projects_by_slug=None):
    up = "../" * depth
    lab = {}
    for slug in p["members"]:
        m = members_by_slug.get(slug)
        if m:
            for variant in [m["name"], *m["aliases"]]:
                lab[fold(variant)] = m

    def author_html(a):
        m = lab.get(fold(a))
        if not m:
            return esc(a)
        return f'<a class="me" href="{up}people/{esc(m["slug"])}.html">{esc(a)}</a>'

    authors = " · ".join(author_html(a) for a in p["authors"])
    title = (
        f'<a href="{esc(p["ee"])}">{esc(p["title"])}</a>' if p["ee"] else esc(p["title"])
    )
    award = f'<span class="award">★ {esc(p["award"])}</span>' if p.get("award") else ""
    link = ""
    if p["link"]:
        href, label = p["link"]
        if not href.startswith("http"):
            href = up + href
        link = f' · <a class="paper-link" href="{esc(href)}">[{esc(label)}]</a>'

    tags = ""
    if show_tags and p.get("projects") and projects_by_slug:
        chips = [
            f'<a href="{up}projects/{esc(s)}.html">{esc(projects_by_slug[s]["short"])}</a>'
            for s in p["projects"] if s in projects_by_slug
        ]
        if chips:
            tags = f'\n  <div class="tags">{" ".join(chips)}</div>'

    return (
        f'<div class="pub" data-members="{esc(" ".join(sorted(p["members"])))}">\n'
        f'  <div class="meta"><span>{p["kind"]}</span>'
        f'<span class="venue">{esc(p["venue"])}{esc(p["detail"])}</span>{award}</div>\n'
        f'  <div class="title">{title}</div>\n'
        f'  <div class="authors">{authors}{link}</div>{tags}\n'
        f"</div>"
    )


def pubs_by_year_html(pubs, members_by_slug, projects_by_slug, *, depth=0):
    by_year = defaultdict(list)
    for p in pubs:
        by_year[p["year"]].append(p)
    out = []
    for year in sorted(by_year, reverse=True):
        out.append(f'<h3 class="year-h" id="y{esc(year)}">{esc(year)}</h3>')
        rows = sorted(by_year[year], key=lambda p: p["title"].lower())
        out.extend(
            render_pub(p, members_by_slug, depth=depth, projects_by_slug=projects_by_slug)
            for p in rows
        )
    return "\n".join(out)


def photo_html(m, *, depth=0, big=False):
    up = "../" * depth
    words = [w for w in m["name"].split() if w]
    initials = (words[0][0] + (words[-1][0] if len(words) > 1 else "")).upper()
    if m["photo"]:
        cls = "photo-lg" if big else "photo"
        return f'<img class="{cls}" src="{up}{esc(m["photo"])}" alt="{esc(m["name"])}" loading="lazy" width="600" height="600" decoding="async">'
    style = ' style="width:168px;height:168px;flex:none"' if big else ""
    return f'<div class="avatar-fallback"{style} role="img" aria-label="{esc(m["name"])}">{esc(initials)}</div>'


def status_badge(p):
    cls = "status" if p["status"] in ("active", "current", "ongoing") else "status past"
    label = "active" if p["status"] in ("active", "current", "ongoing") else p["status"]
    return f'<span class="{cls}">{esc(label)}</span>'


def project_dates(p):
    if p["start"] and p["end"]:
        return f'{esc(p["start"])}–{esc(p["end"])}'
    if p["start"]:
        return f'{esc(p["start"])}–current'
    return esc(p["end"])


ICON_DIR = ROOT / "assets" / "icons"


def icon_tag(kind, slug, *, cls, size, depth=0):
    """<img> tag for assets/icons/{kind}-{slug}.svg, or "" if the file is absent.

    kind is "area" or "proj". Icons are optional — a missing file just means
    no icon renders, so a new project or area never breaks the build.
    """
    fname = f"{kind}-{slug}.svg"
    if not (ICON_DIR / fname).exists():
        return ""
    up = "../" * depth
    return (f'<img class="{cls}" src="{up}assets/icons/{fname}" alt="" '
            f'width="{size}" height="{size}" loading="lazy">')


# ------------------------------------------------------------------------ pages


def write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def build_home(members, projects, news, pubs, pubs_by_year, research, projects_by_slug):
    leads = [m for m in members if m["group"] == "faculty"]
    active = [p for p in projects if p["status"] in ("active", "current", "ongoing")]
    lead_names = " and ".join(m["name"] for m in leads) if leads else ""

    themes = "\n".join(
        f'<div class="theme">'
        + icon_tag("area", t["slug"], cls="theme-icon", size=56)
        + (f'<span class="tag">{esc(", ".join(t["keywords"][:3]))}</span>' if t["keywords"] else "")
        + f'<h3><a href="research.html#{esc(t["slug"])}">{esc(t["name"])}</a></h3>'
        + f'<p>{esc(t["short"])}</p>'
        + f'<a class="theme-link" href="research.html#{esc(t["slug"])}">See projects →</a>'
        + '</div>'
        for t in research
    )

    proj_rows = "\n".join(
        f'<li><a href="projects/{esc(p["slug"])}.html">{esc(p["title"])}</a>'
        + (f' — {esc(p["funder"])}' if p["funder"] else "")
        + (f' · {money(p["amount"])}' if p["amount"] else "")
        + "</li>"
        for p in active[:6]
    ) or '<li class="empty">No active projects listed yet.</li>'

    news_rows = "\n".join(
        news_item_html(n, projects_by_slug) for n in news[:4]
    ) or '<div class="empty">No news yet.</div>'

    body = f"""<section class="masthead">
  <div class="inner top">
    <div class="lockup">
      {HERO_MARK_SVG}
      <div class="names">
        <h1 class="wordmark">RESHAPE<span class="lab">lab</span></h1>
        <p class="expanded">Research in Software: Human Aspects, Practices and Education
        <span class="where">{esc(INSTITUTION)}</span></p>
      </div>
    </div>
    <p class="hero-claim">Software is built by people. We study the conditions they need.</p>
    <p class="thesis">We work on the <em>human side of software engineering</em> &mdash;
    how newcomers get in, why maintainers burn out, how governance holds a project
    together, and what AI changes about all three.</p>
    <div class="btn-row">
      <a class="btn solid" href="publications.html">Publications</a>
      <a class="btn" href="people.html">People</a>
      <a class="btn" href="research.html">Research</a>
    </div>
  </div>
  <div class="strip">
{contrib_strip(pubs_by_year)}
  </div>
  <div class="inner caption">
    <p class="contrib-caption">// {len(pubs)} peer-reviewed papers &middot; {len(members)} people
    &middot; {len(active)} active projects &mdash; each column is one year of output</p>
  </div>
</section>

<section>
  <h2>Research</h2>
  <div class="themes">
{themes}
  </div>
</section>

<section>
  <h2>Active projects</h2>
  <ul class="clean">
{proj_rows}
  </ul>
  <div class="btn-row"><a class="btn" href="research.html">Research areas</a>
  <a class="btn" href="funding.html">Funding</a></div>
</section>

<section>
  <h2>Recent news</h2>
{news_rows}
  <div class="btn-row"><a class="btn" href="news.html">All news</a></div>
</section>

<section>
  <h2>Contact</h2>
  <p class="lead">{esc(SITE_NAME)} is directed by {esc(lead_names)} at NAU&rsquo;s
  School of Informatics, Computing and Cyber Systems in Flagstaff, Arizona.
  We welcome inquiries from prospective PhD and MS students interested in open source,
  software engineering, or AI-assisted learning. Before writing, visit each
  <a href="people.html">faculty page</a> for current advising availability and
  research fit notes.</p>
</section>"""
    write(ROOT / "index.html", page(
        f"{SITE_NAME} — {SITE_TAGLINE}", body,
        description="RESHAPE Lab at Northern Arizona University studies the human and "
                    "educational aspects of software engineering: open source sustainability, "
                    "newcomer onboarding, governance, and AI in software development.",
        nav_current="index.html"))


def build_people(members, pubs_by_member):
    groups = defaultdict(list)
    for m in members:
        groups[m["group"]].append(m)
    ordered = [(g, label) for g, label in GROUP_ORDER if g in groups]
    ordered += [(g, g.title()) for g in sorted(groups) if g not in dict(GROUP_ORDER)]

    sections = []
    for g, label in ordered:
        cards = []
        for m in groups[g]:
            n = len(pubs_by_member.get(m["slug"], []))
            meta = []
            if m["affiliation"]:
                meta.append(esc(m["affiliation"]))
            if n:
                meta.append(f"{n} paper{'s' if n != 1 else ''}")
            cards.append(
                f'<div class="person"><a class="card" href="people/{esc(m["slug"])}.html">'
                f'{photo_html(m)}'
                f'<div class="pname">{esc(m["name"])}</div>'
                f'<div class="prole">{esc(m["role"])}</div>'
                + (f'<div class="pmeta">{" · ".join(meta)}</div>' if meta else "")
                + "</a></div>"
            )
        sections.append(
            f'<section>\n<h2>{esc(label)}</h2>\n<div class="people-grid">\n'
            + "\n".join(cards) + "\n</div>\n</section>"
        )

    intro = """<section>
  <p class="eyebrow">people</p>
  <h1 class="page-title">Who is in the lab</h1>
  <p class="lead">Click anyone to see their publications, projects, and where they are now.
  Publication lists are generated from DBLP, so they stay current without anyone editing them.</p>
</section>"""
    write(ROOT / "people.html", page(
        f"People — {SITE_NAME}", intro + "\n" + "\n".join(sections),
        description=f"Faculty, students, and alumni of {SITE_NAME} at Northern Arizona University.",
        nav_current="people.html"))


def build_member_pages(members, pubs_by_member, projects, members_by_slug, projects_by_slug):
    for m in members:
        mine = pubs_by_member.get(m["slug"], [])
        my_projects = [p for p in projects if m["slug"] in p["members"]]

        facts = []
        if m["affiliation"]:
            facts.append(esc(m["affiliation"]))
        span = f'{m["started"]}–{m["ended"] or "current"}' if m["started"] else m["ended"]
        if span:
            facts.append(esc(span))
        links = []
        if m["email"]:
            links.append(f'<a href="mailto:{esc(m["email"])}">Email</a>')
        for label, url in (("Homepage", m["homepage"]), ("Google Scholar", m["scholar"]),
                           ("GitHub", m["github"])):
            if url:
                links.append(f'<a href="{esc(url)}">{label}</a>')
        if m["dblp_pid"]:
            links.append(f'<a href="https://dblp.org/pid/{esc(m["dblp_pid"])}.html">DBLP</a>')

        proj_html = "\n".join(
            f'<li><a href="../projects/{esc(p["slug"])}.html">{esc(p["title"])}</a>'
            + (f' — {esc(p["funder"])}' if p["funder"] else "") + "</li>"
            for p in my_projects
        )

        body = f"""<section>
  <p class="eyebrow"><a href="../people.html">people</a> / {esc(m["slug"])}</p>
  <div class="member-head">
    {photo_html(m, depth=1, big=True)}
    <div class="bio">
      <h1 class="page-title">{esc(m["name"])}</h1>
      <p class="role mono" style="color:var(--green-deep);margin:0 0 10px">{esc(m["role"])}</p>
      {f'<p class="lead">{esc(m["topic"])}</p>' if m["topic"] else ""}
      {f'<p class="tags mono" style="font-size:11.5px">{" ".join("◆ " + esc(k) for k in m["keywords"])}</p>' if m["keywords"] else ""}
      {f'<p class="mono" style="font-size:12.5px;color:var(--slate)">{" · ".join(facts)}</p>' if facts else ""}
      {f'<p class="mono" style="font-size:12.5px">Now: {esc(m["now"])}</p>' if m["now"] else ""}
      {f'<p class="mono" style="font-size:12.5px">{" · ".join(links)}</p>' if links else ""}
    </div>
  </div>
</section>

{f"""<section>
  <h2>About</h2>
  <div class="prose">{md_to_html(m["bio"])}</div>
</section>""" if m["bio"] else ""}

<section>
  <h2>Projects</h2>
  {f'<ul class="clean">{proj_html}</ul>' if proj_html else '<div class="empty">No projects linked yet.</div>'}
</section>

<section>
  <h2>Publications</h2>
  <p class="mono" style="font-size:12.5px;color:var(--slate)">
    {len(mine)} paper{"s" if len(mine) != 1 else ""} from DBLP
    &middot; <a href="../publications.html?q={esc(m["name"].split()[-1].lower())}">see in the full list</a>
  </p>
  {pubs_by_year_html(mine, members_by_slug, projects_by_slug, depth=1)
   if mine else '<div class="empty">No publications found. Add a dblp_pid in data/members.csv.</div>'}
</section>"""
        write(ROOT / "people" / f"{m['slug']}.html", page(
            f'{m["name"]} — {SITE_NAME}', body,
            description=f'{m["name"]}, {m["role"]} at {SITE_NAME}. '
                        + (m["topic"] or SITE_TAGLINE),
            nav_current="people.html", depth=1))


def build_publications(pubs, members, members_by_slug, projects_by_slug, pubs_by_member):
    years = sorted({p["year"] for p in pubs if p["year"].isdigit()}, reverse=True)
    rail = " ".join(f'<a href="#y{y}">{y}</a>' for y in years)

    # One text field instead of a dropdown: it answers "whose papers", "which
    # venue", "which year" and "that paper about bots" with the same control,
    # and nothing is hidden behind a click.
    controls = f"""<div class="filter">
  <label for="pub-filter">filter</label>
  <input type="search" id="pub-filter" placeholder="name, title, venue, or year"
         autocomplete="off" spellcheck="false">
  <span class="count" id="pub-count">{len(pubs)} papers</span>
</div>
{f'<nav class="year-rail" aria-label="Jump to year">{rail}</nav>' if rail else ""}
<p class="empty" id="pub-none" hidden>Nothing matches that. <button type="button"
   class="linky" id="pub-clear">Clear the filter</button></p>"""

    script = r"""<script>
(function () {
  var input = document.getElementById('pub-filter');
  if (!input) return;
  var count = document.getElementById('pub-count');
  var none = document.getElementById('pub-none');
  var clear = document.getElementById('pub-clear');
  var rail = document.querySelector('.year-rail');

  // Build the haystack from what is already on the page, so the markup carries
  // no duplicated search text. Walking headings and rows together lets each row
  // inherit its year, which otherwise lives only in the heading above it.
  var rows = [], heads = [], year = '';
  Array.prototype.forEach.call(
    document.querySelectorAll('.year-h, .pub'),
    function (el) {
      if (el.classList.contains('year-h')) { year = el.textContent.trim(); heads.push(el); }
      else { rows.push({ el: el, hay: (el.textContent + ' ' + year).toLowerCase().replace(/\s+/g, ' ') }); }
    }
  );

  function apply(q) {
    q = (q || '').trim().toLowerCase();
    var terms = q ? q.split(/\s+/) : [];
    var shown = 0;
    rows.forEach(function (r) {
      var hit = terms.every(function (t) { return r.hay.indexOf(t) > -1; });
      r.el.hidden = !hit;
      if (hit) shown++;
    });
    heads.forEach(function (h) {
      var any = false, n = h.nextElementSibling;
      while (n && !n.classList.contains('year-h')) {
        if (n.classList.contains('pub') && !n.hidden) any = true;
        n = n.nextElementSibling;
      }
      h.hidden = !any;
    });
    count.textContent = shown + (shown === 1 ? ' paper' : ' papers');
    none.hidden = shown !== 0;
    if (rail) rail.hidden = shown === 0;

    var url = new URL(location.href);
    if (q) { url.searchParams.set('q', q); } else { url.searchParams.delete('q'); }
    history.replaceState(null, '', url);
  }

  var initial = new URLSearchParams(location.search).get('q') || '';
  if (initial) { input.value = initial; apply(initial); }

  var timer;
  input.addEventListener('input', function () {
    clearTimeout(timer);
    timer = setTimeout(function () { apply(input.value); }, 90);
  });
  input.addEventListener('keydown', function (e) {
    if (e.key === 'Escape') { input.value = ''; apply(''); }
  });
  if (clear) clear.addEventListener('click', function () {
    input.value = ''; apply(''); input.focus();
  });
})();
</script>"""

    body = f"""<section>
  <p class="eyebrow">publications</p>
  <h1 class="page-title">Publications</h1>
  <p class="lead">Peer-reviewed journal and conference papers by lab members, generated
  automatically from <a href="https://dblp.org">DBLP</a>. Papers link to a self-hosted
  manuscript, the open-access version, or an arXiv preprint where one exists.
  Author names in bold are lab members &mdash; click one for their own page.</p>
{controls}
{pubs_by_year_html(pubs, members_by_slug, projects_by_slug)}
</section>
{script}"""
    write(ROOT / "publications.html", page(
        f"Publications — {SITE_NAME}", body,
        description=f"{len(pubs)} peer-reviewed papers from {SITE_NAME}, auto-generated from DBLP.",
        nav_current="publications.html"))


def build_research_areas(research, projects, members_by_slug):
    """Generate research.html — one section per area, each listing its projects."""

    def proj_card(p):
        meta = [status_badge(p)]
        if project_dates(p):
            meta.append(f'<span>{project_dates(p)}</span>')
        if p["funder"]:
            meta.append(f'<span class="funder">{esc(p["funder"])}</span>')
        if p["amount"]:
            meta.append(f'<span>{money(p["amount"])}</span>')
        foot = []
        if p["pubs"]:
            foot.append(f'{len(p["pubs"])} paper{"s" if len(p["pubs"]) != 1 else ""}')
        if p["members"]:
            foot.append(f'{len(p["members"])} member{"s" if len(p["members"]) != 1 else ""}')
        icon = icon_tag("proj", p["slug"], cls="proj-icon", size=44)
        head = (
            f'<div class="proj-head">{icon}<h4><a href="projects/{esc(p["slug"])}.html">'
            f'{esc(p["title"])}</a></h4></div>'
            if icon else
            f'<h4><a href="projects/{esc(p["slug"])}.html">{esc(p["title"])}</a></h4>'
        )
        return (
            f'<div class="proj">\n'
            f'  <div class="pmeta">{"".join(meta)}</div>\n'
            f'  {head}\n'
            f'  <p class="summary">{esc(p["summary"])}</p>\n'
            + (f'  <div class="foot"><a href="projects/{esc(p["slug"])}.html">'
               f'Project page</a><span>{" · ".join(foot)}</span></div>\n' if foot else
               f'  <div class="foot"><a href="projects/{esc(p["slug"])}.html">Project page</a></div>\n')
            + "</div>"
        )

    # areas with known projects; fall back to listing all active projects
    # under an "Other projects" catch-all for anything not in any area
    area_project_slugs = {s for area in research for s in area["project_slugs"]}
    uncategorised = [p for p in projects if p["slug"] not in area_project_slugs]

    area_sections = []
    for area in research:
        cards = "\n".join(proj_card(p) for p in area["projects"])
        icon = icon_tag("area", area["slug"], cls="area-icon", size=64)
        head = (
            f'<div class="area-head">{icon}<div>'
            f'<h2>{esc(area["name"])}</h2>'
            f'<p class="lead">{esc(area["short"])}</p></div></div>'
            if icon else
            f'<h2>{esc(area["name"])}</h2>\n  <p class="lead">{esc(area["short"])}</p>'
        )
        area_sections.append(
            f'<section id="{esc(area["slug"])}">\n'
            f'  {head}\n'
            + (f'  <div class="prose"><p>{esc(area["description"])}</p></div>\n' if area["description"] else "")
            + (f'\n{cards}\n' if cards else
               f'  <div class="empty">No projects linked yet — add slugs to data/research.csv.</div>\n')
            + '</section>'
        )

    if uncategorised:
        cards = "\n".join(proj_card(p) for p in uncategorised)
        area_sections.append(
            f'<section id="other">\n'
            f'  <h2>Other projects</h2>\n'
            f'  <p class="lead">Projects not yet assigned to a research area.</p>\n'
            f'\n{cards}\n</section>'
        )

    body = f"""<section>
  <p class="eyebrow">research</p>
  <h1 class="page-title">Research Areas</h1>
  <p class="lead">Our work spans four interconnected areas. Each area is supported
  by one or more funded projects — click any project for its full description,
  publications, and team.</p>
</section>
{"".join(area_sections) or '<div class="empty">Add rows to data/research.csv.</div>'}"""
    write(ROOT / "research.html", page(
        f"Research — {SITE_NAME}", body,
        description=f"Research areas and projects at {SITE_NAME}: newcomer onboarding, "
                    "software engineering education, OSS sustainability, and AI in SE.",
        nav_current="research.html"))


def build_project_pages(projects, members_by_slug, projects_by_slug):
    for p in projects:
        team = "\n".join(
            f'<li><a href="../people/{esc(s)}.html">{esc(members_by_slug[s]["name"])}</a>'
            f' — {esc(members_by_slug[s]["role"])}</li>'
            for s in p["members"] if s in members_by_slug
        )
        for s in p["members"]:
            if s not in members_by_slug:
                warn(f"projects.csv '{p['slug']}': unknown member slug '{s}'")

        news_html = "\n".join(
            news_item_html(n, projects_by_slug, depth=1) for n in p["news"]
        )

        facts = []
        if p["funder"]:
            label = p["funder"] + (f' {p["program"]}' if p["program"] else "")
            if p["award_no"]:
                award = f'<span class="award-no">#{esc(p["award_no"])}</span>'
                label += " " + (f'<a href="{esc(p["award_url"])}">{award}</a>' if p["award_url"] else award)
            facts.append(("Funding", label))
        if p["amount"]:
            facts.append(("Amount", money(p["amount"])))
        if project_dates(p):
            facts.append(("Period", project_dates(p)))
        if p["role"]:
            facts.append(("Role", esc(p["role"])))
        if p["url"]:
            facts.append(("Site", f'<a href="{esc(p["url"])}">{esc(p["url"])}</a>'))
        facts_html = "\n".join(
            f'<tr><th>{k}</th><td>{v}</td></tr>' for k, v in facts
        )

        description = p["summary"] or f'{p["title"]} at {SITE_NAME}.'
        page_icon = icon_tag("proj", p["slug"], cls="proj-icon-lg", size=72, depth=1)
        title_block = (
            f'<div class="proj-page-head">{page_icon}<h1 class="page-title">{esc(p["title"])}</h1></div>'
            if page_icon else
            f'<h1 class="page-title">{esc(p["title"])}</h1>'
        )
        body = f"""<section>
  <p class="eyebrow"><a href="../research.html">research</a> / {esc(p["slug"])}</p>
  {title_block}
  <div class="pmeta mono" style="display:flex;gap:14px;flex-wrap:wrap;font-size:12px;color:var(--slate);margin-bottom:14px">
    {status_badge(p)}
  </div>
  <p class="lead">{esc(p["summary"])}</p>
  {f'<div class="table-wrap"><table class="fund" style="max-width:640px">{facts_html}</table></div>' if facts_html else ""}
</section>

<section>
  <h2>About</h2>
  <div class="prose">
{md_to_html(p["body"]) if p["body"] else f'<p>{esc(p["summary"])}</p><p class="empty">Add a longer description at <code>data/projects/{esc(p["slug"])}.md</code>.</p>'}
  </div>
</section>

<section>
  <h2>Team</h2>
  {f'<ul class="clean">{team}</ul>' if team else '<div class="empty">Add member slugs to the <code>members</code> column in data/projects.csv.</div>'}
</section>

<section>
  <h2>Publications</h2>
  {pubs_by_year_html(p["pubs"], members_by_slug, projects_by_slug, depth=1)
   if p["pubs"] else
   f'<div class="empty">Tag papers with <code>{esc(p["slug"])}</code> in the <code>projects</code> column of data/pub_tags.csv.</div>'}
</section>

<section>
  <h2>News and presentations</h2>
  {news_html if news_html else f'<div class="empty">Add rows to data/news.csv with <code>{esc(p["slug"])}</code> in the <code>projects</code> column.</div>'}
</section>"""
        write(ROOT / "projects" / f"{p['slug']}.html", page(
            f'{p["title"]} — {SITE_NAME}', body,
            description=description, nav_current="research.html", depth=1))


def build_funding(projects):
    funded = [p for p in projects if p["funder"]]
    by_funder = defaultdict(list)
    for p in funded:
        by_funder[p["funder"]].append(p)

    blocks = []
    for funder in sorted(by_funder, key=lambda f: -sum(money_value(p["amount"]) for p in by_funder[f])):
        rows = []
        for p in sorted(by_funder[funder], key=lambda p: p["start"], reverse=True):
            award = esc(p["award_no"])
            if p["award_no"] and p["award_url"]:
                award = f'<a href="{esc(p["award_url"])}">{award}</a>'
            icon = icon_tag("proj", p["slug"], cls="proj-icon-sm", size=20)
            rows.append(
                f'<tr><td>{icon}<a href="projects/{esc(p["slug"])}.html">{esc(p["title"])}</a>'
                + (f'<br><span class="award-no">{esc(p["program"])} {award}</span>'
                   if (p["program"] or award) else "")
                + f'</td><td class="mono" style="font-size:13px;white-space:nowrap">{project_dates(p)}</td>'
                + f'<td class="num">{money(p["amount"])}</td></tr>'
            )
        subtotal = sum(money_value(p["amount"]) for p in by_funder[funder])
        blocks.append(
            f'<h3 class="sub-h">{esc(funder)}</h3>\n<div class="table-wrap">\n'
            f'<table class="fund grants">\n'
            f'<colgroup><col class="c-proj"><col class="c-period">'
            f'<col class="c-amt"></colgroup>\n'
            f'<thead><tr><th>Project</th><th>Period</th>'
            f'<th class="num">Amount</th></tr></thead>\n<tbody>\n'
            + "\n".join(rows)
            + f'\n<tr class="total"><td colspan="2">Subtotal</td>'
              f'<td class="num">{money(str(subtotal))}</td></tr>\n</tbody></table></div>'
        )

    total = sum(money_value(p["amount"]) for p in funded)
    body = f"""<section>
  <p class="eyebrow">funding</p>
  <h1 class="page-title">Funding</h1>
  <p class="lead">Grants and awards supporting the lab's work, grouped by funder.
  Every entry links to its project page. Totals reflect the amounts routed to the lab.</p>
  <p class="contrib-caption">// {len(funded)} awards &middot; {money(str(total))} total</p>
</section>
<section>
{chr(10).join(blocks) or '<div class="empty">No funding entries yet.</div>'}
</section>"""
    write(ROOT / "funding.html", page(
        f"Funding — {SITE_NAME}", body,
        description=f"Research funding supporting {SITE_NAME}: {money(str(total))} across {len(funded)} awards.",
        nav_current="funding.html"))


def news_item_html(n, projects_by_slug, *, depth=0, extra_class=""):
    """One row on a news index. The title links to the item's own page."""
    up = "../" * depth
    chips = " ".join(
        f'<a href="{up}projects/{esc(s)}.html">{esc(projects_by_slug[s]["short"])}</a>'
        for s in n["projects"] if s in projects_by_slug
    )
    more = ""
    if n["body"]:
        more = (f' <a class="paper-link" href="{up}news/{esc(n["slug"])}.html">'
                f"Read more &rarr;</a>")
    teaser = ""
    if n["summary"]:
        teaser = f'<p>{esc(n["summary"])}{more}</p>'
    elif more:
        teaser = f"<p>{more}</p>"
    tag = f'<div class="tag">{esc(n["tag"])}</div>' if n["tag"] else ""
    chip_row = ""
    if chips:
        chip_row = f'<div class="tags mono" style="font-size:11.5px;margin-top:5px">{chips}</div>'
    thumb = ""
    if n["image"]:
        thumb = (f'<div class="thumb"><img src="{up}{esc(n["image"])}" alt="" '
                 f'width="88" height="88" loading="lazy"></div>')
    cls = "news-item" + (f" {extra_class}" if extra_class else "")
    return (
        f'<div class="{cls}"><div class="date">{esc(n["date"])}</div>{thumb}<div>'
        f'{tag}'
        f'<h3><a href="{up}news/{esc(n["slug"])}.html">{esc(n["title"])}</a></h3>'
        f"{teaser}{chip_row}</div></div>"
    )


def build_news(news, projects_by_slug):
    VISIBLE = 5
    visible_items = news[:VISIBLE]
    hidden_items = news[VISIBLE:]

    rows = "\n".join(news_item_html(n, projects_by_slug) for n in visible_items)
    hidden_rows = "\n".join(
        news_item_html(n, projects_by_slug, extra_class="news-more") for n in hidden_items
    )

    more_button = ""
    if hidden_items:
        more_button = (
            f'<div class="btn-row" id="news-more-row">'
            f'<button type="button" class="btn" id="news-more-btn">'
            f'View more ({len(hidden_items)})</button></div>'
        )
    script = ""
    if hidden_items:
        script = """<script>
(function () {
  var btn = document.getElementById('news-more-btn');
  var row = document.getElementById('news-more-row');
  if (!btn) return;
  btn.addEventListener('click', function () {
    var items = document.querySelectorAll('.news-more');
    items.forEach(function (el) { el.classList.remove('news-more'); });
    row.hidden = true;
  });
})();
</script>"""

    body = (
        '<section>\n'
        '  <p class="eyebrow">news</p>\n'
        '  <h1 class="page-title">News</h1>\n'
        '  <p class="lead">Awards, talks, papers, and arrivals. Items tagged with a\n'
        "  project also appear on that project's page.</p>\n"
        + (rows or '<div class="empty">No news yet.</div>')
        + ("\n" + hidden_rows if hidden_rows else "")
        + "\n</section>\n"
        + more_button
        + script
    )
    write(ROOT / "news.html", page(
        f"News — {SITE_NAME}", body,
        description=f"Recent news from {SITE_NAME}.", nav_current="news.html"))


def build_news_pages(news, projects_by_slug):
    """A permalink page per item, so news can be linked, shared, and indexed."""
    for i, n in enumerate(news):
        chips = "\n".join(
            f'<li><a href="../projects/{esc(s)}.html">'
            f'{esc(projects_by_slug[s]["title"])}</a></li>'
            for s in n["projects"] if s in projects_by_slug
        )
        related = ""
        if chips:
            related = ('<section>\n  <h2>Related projects</h2>\n'
                       f'  <ul class="clean">{chips}</ul>\n</section>')

        source = ""
        if n["url"]:
            source = (f'  <div class="btn-row"><a class="btn" href="{esc(n["url"])}">'
                      "Read the source &rarr;</a></div>")

        nav = []
        if i + 1 < len(news):
            prev = news[i + 1]
            nav.append(f'<a href="{esc(prev["slug"])}.html">&larr; '
                       f'{esc(prev["title"][:44])}</a>')
        if i > 0:
            nxt = news[i - 1]
            nav.append(f'<a href="{esc(nxt["slug"])}.html">'
                       f'{esc(nxt["title"][:44])} &rarr;</a>')
        nav_row = ""
        if nav:
            nav_row = ('<section>\n  <div class="foot mono" style="display:flex;gap:20px;'
                       'flex-wrap:wrap;font-size:12px">\n    '
                       + " ".join(nav) + "\n  </div>\n</section>")

        content = md_to_html(n["body"]) if n["body"] else f'<p>{esc(n["summary"])}</p>'
        meta = esc(n["date"]) + (f' &middot; {esc(n["tag"])}' if n["tag"] else "")
        hero = ""
        if n["image"]:
            hero = f'  <img class="news-hero" src="../{esc(n["image"])}" alt="" loading="lazy">\n'

        item_body = (
            '<section>\n'
            f'  <p class="eyebrow"><a href="../news.html">news</a> / {esc(n["date"])}</p>\n'
            f'  <h1 class="page-title">{esc(n["title"])}</h1>\n'
            '  <p class="mono" style="font-size:12.5px;color:var(--slate);margin:0 0 20px">'
            f'{meta}</p>\n'
            + hero
            + f'  <div class="prose">\n{content}\n  </div>\n{source}\n</section>\n\n'
            + related + "\n\n" + nav_row
        )
        write(ROOT / "news" / f"{n['slug']}.html", page(
            f'{n["title"]} — {SITE_NAME}', item_body,
            description=n["summary"] or n["title"],
            nav_current="news.html", depth=1))


def build_sitemap(members, projects, news):
    urls = ["index.html", "people.html", "publications.html", "research.html",
            "funding.html", "news.html"]
    urls += [f'people/{m["slug"]}.html' for m in members]
    urls += [f'projects/{p["slug"]}.html' for p in projects]
    urls += [f'news/{n["slug"]}.html' for n in news]
    entries = "\n".join(f"  <url><loc>{SITE_URL}/{u}</loc></url>" for u in urls)
    write(ROOT / "sitemap.xml",
          '<?xml version="1.0" encoding="UTF-8"?>\n'
          '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
          f"{entries}\n</urlset>\n")
    write(ROOT / "robots.txt", f"User-agent: *\nAllow: /\nSitemap: {SITE_URL}/sitemap.xml\n")


def build_pub_index(pubs):
    """Write every harvested paper's DBLP key, so pub_tags.csv is easy to fill in."""
    with (ROOT / "pub_index.csv").open("w", newline="", encoding="utf-8") as fh:
        w = csv.writer(fh)
        w.writerow(["dblp_key", "year", "title", "venue", "members"])
        for p in sorted(pubs, key=lambda p: (p["year"], p["title"].lower()), reverse=True):
            w.writerow([p["key"], p["year"], p["title"], p["venue"],
                        ";".join(sorted(p["members"]))])


def build_missing_report(missing):
    by_year = defaultdict(list)
    for p in missing:
        by_year[p["year"]].append(p)
    lines = [
        "# Papers with no open version",
        "",
        f"Generated by `scripts/build_site.py`. {len(missing)} papers are neither open",
        "access nor on arXiv, so the publication list shows no full-text link for them.",
        "",
        "To fix one: check the publisher's self-archiving policy (most ACM and IEEE",
        "venues allow it), then drop the author-accepted manuscript into",
        "`publications/` using the exact filename below. The next build links it.",
        "",
    ]
    for year in sorted(by_year, reverse=True):
        lines.append(f"## {year}")
        lines.append("")
        for p in sorted(by_year[year], key=lambda p: p["title"].lower()):
            lines.append(f'- [ ] **{p["title"]}** — *{p["venue"]}* — {", ".join(p["authors"])}  ')
            lines.append(f'      drop PDF at: `publications/{key_slug(p["key"])}.pdf`')
        lines.append("")
    write(ROOT / "missing_pdfs.md", "\n".join(lines))


# ------------------------------------------------------------------------- main


def main() -> None:
    offline = "--offline" in sys.argv
    args = {
        "offline": offline,
        "refresh_dblp": "--refresh-dblp" in sys.argv,
    }
    use_oa = "--no-oa" not in sys.argv
    refresh_oa = "--refresh-oa" in sys.argv
    deep = "--deep" in sys.argv

    members = load_members()
    projects = load_projects()
    news = load_news()
    research = load_research()
    tags = load_pub_tags()
    members_by_slug = {m["slug"]: m for m in members}
    if not ATTRIBUTE_BY_NAME:
        current_no_pid = [m["name"] for m in members
                          if m["group"] != "alumni" and not m["dblp_pid"]]
        if current_no_pid:
            warn(f"{len(current_no_pid)} current member(s) have no `dblp_pid`, so their "
                 f"pages show no papers and their names are not linked in author "
                 f"lists: {', '.join(sorted(current_no_pid))}")
    projects_by_slug = {p["slug"]: p for p in projects}

    pubs_map, preprints = harvest(members, **args)
    if ATTRIBUTE_BY_NAME:
        attribute_by_name(pubs_map, members)
    dropped, needs_date = filter_pubs(pubs_map, members_by_slug)
    missing = resolve_links(pubs_map, preprints, use_oa=use_oa, refresh_oa=refresh_oa,
                            deep=deep, offline=offline)

    # hand annotations: awards and project links
    for key, t in tags.items():
        if key not in pubs_map:
            warn(f"pub_tags.csv: DBLP key '{key}' is not in any member's record")
            continue
        pubs_map[key]["award"] = t["award"]
        pubs_map[key]["projects"] = [s for s in t["projects"]]
        for s in t["projects"]:
            if s in projects_by_slug:
                projects_by_slug[s]["pubs"].append(pubs_map[key])
            else:
                warn(f"pub_tags.csv: '{key}' references unknown project '{s}'")

    pubs = sorted(pubs_map.values(), key=lambda p: (p["year"], p["title"].lower()), reverse=True)
    pubs_by_member = defaultdict(list)
    for p in pubs:
        for s in p["members"]:
            pubs_by_member[s].append(p)
    pubs_by_year = defaultdict(list)
    for p in pubs:
        if p["year"].isdigit():
            pubs_by_year[p["year"]].append(p)

    for n in news:
        for s in n["projects"]:
            if s in projects_by_slug:
                projects_by_slug[s]["news"].append(n)
            else:
                warn(f"news.csv '{n['slug']}': unknown project '{s}'")

    # a project's team is explicit members plus anyone who co-authored its papers
    for p in projects:
        implied = {s for pub in p["pubs"] for s in pub["members"]}
        p["members"] = list(dict.fromkeys(p["members"] + sorted(implied - set(p["members"]))))

    # resolve research area project slugs to project objects
    for area in research:
        area["projects"] = [projects_by_slug[s] for s in area["project_slugs"] if s in projects_by_slug]
        missing_slugs = [s for s in area["project_slugs"] if s not in projects_by_slug]
        for s in missing_slugs:
            warn(f"research.csv '{area['slug']}': unknown project slug '{s}'")

    build_home(members, projects, news, pubs, pubs_by_year, research, projects_by_slug)
    build_people(members, pubs_by_member)
    build_member_pages(members, pubs_by_member, projects, members_by_slug, projects_by_slug)
    build_publications(pubs, members, members_by_slug, projects_by_slug, pubs_by_member)
    build_research_areas(research, projects, members_by_slug)
    build_project_pages(projects, members_by_slug, projects_by_slug)
    build_funding(projects)
    build_news(news, projects_by_slug)
    build_news_pages(news, projects_by_slug)
    build_sitemap(members, projects, news)
    build_pub_index(pubs)
    build_dropped_report(dropped, needs_date)
    build_missing_report(missing)

    linked = sum(1 for p in pubs if p["link"])
    print(f"members     {len(members)} ({sum(1 for m in members if m['dblp_pid'])} with a DBLP pid)")
    print(f"publications {len(pubs)} unique ({linked} with a full-text link, {len(missing)} without)")
    if dropped:
        print(f"             {len(dropped)} alumni-only paper(s) left out "
              f"— see dropped_pubs.md")
    print(f"projects    {len(projects)} ({sum(1 for p in projects if p['funder'])} funded)")
    print(f"news        {len(news)}")
    print(f"pages       {6 + len(members) + len(projects) + len(news)}")
    if WARNINGS:
        print(f"\n{len(WARNINGS)} warning(s):")
        for w in WARNINGS:
            print(f"  - {w}")


if __name__ == "__main__":
    main()
