#!/usr/bin/env python3
"""
migrate_from_vue.py — one-shot import of the old Vue site's content.

Reads the JSON seed files and photo folders from a checkout of the previous
site and writes them into this repo's data format. Run it once, review the
result, then delete this script.

    python scripts/migrate_from_vue.py ../reshapelab-old

Reads   <old>/public/members.json         30 people, 21 with a DBLP pid
        <old>/public/funding.json         NSF awards
        <old>/public/research_areas.json  research themes + descriptions
        <old>/public/posts.json           news items (HTML bodies)
        <old>/public/images/people/*/     photos

Writes  data/members.csv          data/people/<slug>.md
        data/projects.csv         data/projects/<slug>.md
        data/research.csv         data/news.csv, data/news/<slug>.md
        assets/people/<slug>.jpg  (square, 600px, JPEG)

Existing files are backed up to *.pre-migration before being overwritten.
Photo resizing uses Pillow if available, otherwise macOS `sips`, otherwise
the originals are copied unchanged. Nothing else needs a dependency.
Conflicts between the old data and what is already here are printed at the end
rather than resolved silently — funding amounts in particular disagree.
"""

import csv
import html
import io
import json
import re
import shutil
import sys
import unicodedata
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data"
PHOTOS_OUT = ROOT / "assets" / "people"
PHOTO_PX = 600
PAPER = (250, 251, 252)  # --paper, for flattening transparent PNGs


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


NOTES: list[str] = []


def note(msg):
    NOTES.append(msg)


def slugify(s):
    s = unicodedata.normalize("NFKD", (s or "").lower())
    s = "".join(c for c in s if not unicodedata.combining(c))
    return re.sub(r"[^a-z0-9]+", "-", s).strip("-")


# Old free-text roles -> (group, tidied role label). The old site mixed
# seniority and status into one field and misspelled two of them.
ROLE_MAP = {
    "Professor": ("faculty", "Professor · co-director"),
    "Assistant Professor": ("faculty", "Associate Professor · co-director"),
    "PhD Student": ("phd", "PhD student"),
    "MSc": ("ms", "MS student"),
    "Undergraduate": ("undergrad", "Undergraduate researcher"),
    "Alumni (PhD)": ("alumni", "PhD alumnus"),
    "Alumni (MSc.)": ("alumni", "MS alumnus"),
    "Alumni (Undegraduate)": ("alumni", "Undergraduate alumnus"),
    "Alumni (Post-doc)": ("alumni", "Postdoctoral alumnus"),
    "Alumni (Postdoc)": ("alumni", "Postdoctoral alumnus"),
    "Alumni (Visitor)": ("alumni", "Visiting researcher"),
}
GROUP_ORDER = {"faculty": 10, "postdoc": 15, "phd": 20, "ms": 30,
               "undergrad": 40, "collaborator": 50, "alumni": 90}


def html_to_md(raw):
    """Convert the posts' small HTML subset to the Markdown the site accepts."""
    t = raw or ""
    t = re.sub(r"<\s*br\s*/?\s*>", "\n", t, flags=re.I)
    t = re.sub(r"<\s*/\s*p\s*>", "\n\n", t, flags=re.I)
    t = re.sub(r"<\s*p[^>]*>", "", t, flags=re.I)
    t = re.sub(r"<\s*li[^>]*>", "- ", t, flags=re.I)
    t = re.sub(r"<\s*/\s*li\s*>", "\n", t, flags=re.I)
    t = re.sub(r"<\s*/?\s*(ul|ol)[^>]*>", "\n", t, flags=re.I)
    t = re.sub(r"<\s*(strong|b)\s*>(.*?)<\s*/\s*(strong|b)\s*>", r"**\2**", t, flags=re.I | re.S)
    t = re.sub(r"<\s*(em|i)\s*>(.*?)<\s*/\s*(em|i)\s*>", r"*\2*", t, flags=re.I | re.S)
    t = re.sub(r'<\s*a[^>]*href="([^"]*)"[^>]*>(.*?)<\s*/\s*a\s*>', r"[\2](\1)", t, flags=re.I | re.S)
    t = re.sub(r"<[^>]+>", "", t)
    t = html.unescape(t)
    t = re.sub(r"[ \t]+", " ", t)
    t = re.sub(r"\n{3,}", "\n\n", t)
    return "\n\n".join(p.strip() for p in t.split("\n\n") if p.strip())


def backup(path):
    """Copy a file aside before overwriting it.

    Deliberately refuses to overwrite an existing .pre-migration file, so that
    re-running the script keeps the genuine original rather than replacing it
    with the previous run's output.
    """
    if not path.exists():
        return
    dest = path.with_suffix(path.suffix + ".pre-migration")
    if dest.exists():
        return
    shutil.copy2(path, dest)


def write_csv(path, fieldnames, rows):
    backup(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=fieldnames, extrasaction="ignore")
        w.writeheader()
        for r in rows:
            w.writerow(r)
    print(f"  wrote {path.relative_to(ROOT)}  ({len(rows)} rows)")


# ------------------------------------------------------------------- members


def migrate_members(old, existing):
    people = json.load((old / "public" / "members.json").open(encoding="utf-8"))["members"]
    rows, bios = [], {}

    for m in people:
        name = f"{(m.get('first_name') or '').strip()} {(m.get('last_name') or '').strip()}".strip()
        if not name:
            continue
        slug = slugify(name)
        raw_role = (m.get("role") or "").strip()
        group, role = ROLE_MAP.get(raw_role, ("collaborator", raw_role or "Collaborator"))
        if raw_role not in ROLE_MAP:
            note(f"unmapped role '{raw_role}' for {name} — filed as collaborator")

        contacts = m.get("contacts") or {}
        gh = (contacts.get("github") or "").strip().lstrip("@")
        keywords = m.get("research_keywords") or []

        # author_name is exactly what the aliases column is for: every spelling
        # DBLP uses for this person. The old site already stored it as a list.
        raw_aliases = m.get("author_name") or []
        if isinstance(raw_aliases, str):
            raw_aliases = [raw_aliases]
        aliases = [a.strip() for a in raw_aliases
                   if a and a.strip() and slugify(a) != slug]

        prev = existing.get(slug, {})
        rows.append({
            "slug": slug,
            "name": name,
            "role": role,
            "group": group,
            "order": GROUP_ORDER.get(group, 500),
            "dblp_pid": (m.get("dblp_pid") or "").strip() or prev.get("dblp_pid", ""),
            "aliases": ";".join(aliases),
            "affiliation": prev.get("affiliation", ""),
            "started": prev.get("started", ""),
            "ended": prev.get("ended", ""),
            "now": prev.get("now", ""),
            # keywords already render as chips; a duplicate topic line reads as
            # filler, so leave it for a human to write one real sentence
            "topic": prev.get("topic", ""),
            "keywords": ";".join(keywords),
            "email": (contacts.get("email") or "").strip(),
            "homepage": prev.get("homepage", ""),
            "scholar": prev.get("scholar", ""),
            "github": f"https://github.com/{gh}" if gh else prev.get("github", ""),
            "pub_from": prev.get("pub_from", ""),
            "pub_to": prev.get("pub_to", ""),
            "_photo_dir": ((m.get("photos") or {}).get("small_image")
                           or next(iter((m.get("photos") or {}).values()), "")),
            "_areas": [slugify(x) for x in (m.get("projects") or [])],
        })

        desc = (m.get("description") or "").strip()
        if desc and len(desc) > 60:
            bios[slug] = desc

    # anyone already in members.csv that the old site never listed
    for slug, prev in existing.items():
        if slug not in {r["slug"] for r in rows}:
            rows.append({**prev, "keywords": prev.get("keywords", ""),
                         "email": prev.get("email", ""), "_photo_dir": "", "_areas": []})
            note(f"kept '{slug}' from the current members.csv (not in the old site)")

    rows.sort(key=lambda r: (int(r["order"]), r["name"].split()[-1].lower()))

    fields = ["slug", "name", "role", "group", "order", "dblp_pid", "aliases",
              "affiliation", "started", "ended", "now", "topic", "keywords",
              "email", "homepage", "scholar", "github", "pub_from", "pub_to"]
    write_csv(DATA / "members.csv", fields, rows)

    (DATA / "people").mkdir(parents=True, exist_ok=True)
    for slug, text in bios.items():
        p = DATA / "people" / f"{slug}.md"
        backup(p)
        p.write_text(text + "\n", encoding="utf-8")
    print(f"  wrote data/people/*.md  ({len(bios)} bios)")
    return rows


# -------------------------------------------------------------------- photos


def _photo_backend():
    """Pick an image processor. Returns ('pil'|'sips'|'copy', detail).

    Pillow is preferred. On macOS, `sips` ships with the OS and does everything
    we need, so no install is required. Failing both, photos are copied
    unchanged and the site still builds — just heavier.
    """
    try:
        from PIL import Image  # noqa: F401
        return "pil", "Pillow"
    except ImportError:
        pass
    if shutil.which("sips"):
        return "sips", "sips (macOS built-in)"
    return "copy", "none"


def _resize_pil(src, out):
    from PIL import Image

    im = Image.open(src)
    if im.mode in ("RGBA", "LA", "P"):
        im = im.convert("RGBA")
        bg = Image.new("RGB", im.size, PAPER)
        bg.paste(im, mask=im.split()[-1])
        im = bg
    else:
        im = im.convert("RGB")

    # square crop biased toward the top, because faces sit high in portraits
    w, h = im.size
    side = min(w, h)
    left = (w - side) // 2
    top = int((h - side) * 0.15)
    im = im.crop((left, top, left + side, top + side))
    im = im.resize((PHOTO_PX, PHOTO_PX), Image.LANCZOS)
    im.save(out, "JPEG", quality=82, optimize=True, progressive=True)


def _resize_sips(src, out):
    """Square-crop and downscale with macOS sips. Crop is centred, not
    top-biased: sips has no crop offset. Good enough for headshots."""
    import subprocess

    tmp = out.with_suffix(".tmp.jpg")
    shutil.copy2(src, tmp)

    def run(*args):
        subprocess.run(["sips", *args, str(tmp)],
                       check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

    probe = subprocess.run(["sips", "-g", "pixelWidth", "-g", "pixelHeight", str(tmp)],
                           check=True, capture_output=True, text=True).stdout
    dims = {}
    for line in probe.splitlines():
        if ":" in line:
            k, _, v = line.strip().rpartition(":")
            if v.strip().isdigit():
                dims[k.strip()] = int(v.strip())
    w, h = dims.get("pixelWidth", 0), dims.get("pixelHeight", 0)

    # flatten any transparency onto the paper colour, then scale the short
    # side to the target, then crop the long side down to a square
    run("-s", "format", "jpeg", "-s", "formatOptions", "82")
    if w and h:
        if w <= h:
            run("--resampleWidth", str(PHOTO_PX))
        else:
            run("--resampleHeight", str(PHOTO_PX))
    run("-c", str(PHOTO_PX), str(PHOTO_PX))
    tmp.replace(out)


def migrate_photos(rows, old):
    backend, detail = _photo_backend()
    if backend == "copy":
        note("no image processor found (no Pillow, no sips) — photos copied at "
             "full size. Install Pillow in a venv and re-run to shrink them: "
             "python3 -m venv .venv && source .venv/bin/activate && pip install Pillow")

    src_root = old / "public" / "images" / "people"
    PHOTOS_OUT.mkdir(parents=True, exist_ok=True)
    done = skipped = failed = 0
    before = after = 0

    for r in rows:
        hint = r.get("_photo_dir") or ""
        candidates = []
        if hint:
            candidates.append(old / "public" / hint)
        # the old folder names do not match our slugs, so try a few spellings
        for variant in {r["slug"].replace("-", "_"),
                        r["name"].split()[0].lower(),
                        slugify(r["name"]).replace("-", "_")}:
            for fn in ("image_with_background.png", "image_without_background.png"):
                candidates.append(src_root / variant / fn)

        src = next((c for c in candidates
                    if c.exists() and c.is_file() and "user_icon" not in c.name), None)
        if src is None:
            skipped += 1
            note(f"no photo found for {r['name']} — add assets/people/{r['slug']}.jpg by hand")
            continue

        before += src.stat().st_size
        out = PHOTOS_OUT / f"{r['slug']}.jpg"
        try:
            if backend == "pil":
                _resize_pil(src, out)
            elif backend == "sips":
                _resize_sips(src, out)
            else:
                out = PHOTOS_OUT / f"{r['slug']}{src.suffix.lower()}"
                shutil.copy2(src, out)
        except Exception as exc:
            failed += 1
            note(f"could not process {src.name} for {r['name']} ({exc}) — copied unchanged")
            out = PHOTOS_OUT / f"{r['slug']}{src.suffix.lower()}"
            shutil.copy2(src, out)
        after += out.stat().st_size
        done += 1

    print(f"  wrote assets/people/*  ({done} photos via {detail}, {skipped} missing)")
    if before:
        print(f"    {before / 1e6:.1f} MB  ->  {after / 1e6:.2f} MB")
    if failed:
        print(f"    {failed} could not be processed and were copied as-is")


# ------------------------------------------------------- research + projects


def migrate_research_and_projects(old, existing_projects, member_rows):
    areas = json.load((old / "public" / "research_areas.json").open(encoding="utf-8"))["projects"]
    awards = json.load((old / "public" / "funding.json").open(encoding="utf-8"))["funding"]

    # research themes: keep the old descriptions, they are the best copy we have
    research_rows = []
    for a in areas:
        research_rows.append({
            "slug": slugify(a["project_name"]),
            "name": a["project_name"],
            "short": (a.get("short_project_description") or "").strip(),
            "keywords": ";".join(a.get("project_key_words") or []),
        })
    write_csv(DATA / "research.csv", ["slug", "name", "short", "keywords"], research_rows)

    area_desc = {a["project_name"]: (a.get("project_description") or "").strip() for a in areas}
    area_slug = {a["project_name"]: slugify(a["project_name"]) for a in areas}

    def parse_amount(v):
        """'$528.864,00' and '$249,941.00' both mean the same thing here."""
        s = re.sub(r"[^\d.,]", "", v or "")
        if not s:
            return ""
        s = re.sub(r"[.,]\d{2}$", "", s)        # drop cents
        return re.sub(r"[.,]", "", s) or ""

    def parse_year(v):
        m = re.search(r"(19|20)\d{2}", v or "")
        return m.group(0) if m else ""

    rows, seen = [], {}
    for a in awards:
        award_no = re.sub(r"[^\d]", "", a.get("id") or "")
        title = (a.get("name") or "").strip()
        if not title:
            continue
        if award_no and award_no in seen:
            note(f"award #{award_no} appears twice in funding.json — merged")
            row = seen[award_no]
            for area in a.get("projetcs") or []:
                if area_slug.get(area) and area_slug[area] not in row["_areas"]:
                    row["_areas"].append(area_slug[area])
            continue

        # NSF titles stack a program acronym and qualifiers in front of the real
        # title: "CHS: Large: Collaborative Research: Gender-Inclusive ...".
        # Walk the colon-separated head, keeping the program and dropping the rest.
        PROGRAMS = {"CHS", "SHF", "HSI", "RETTL", "POSE", "IUSE", "CAREER",
                    "CISE", "EAGER", "SaTC", "ITEST"}
        QUALIFIERS = {"large", "small", "medium", "collaborative research",
                      "collaborative", "research"}
        parts = [x.strip() for x in title.split(":")]
        program, head = "", []
        while len(parts) > 1:
            token = parts[0]
            if token.upper() in PROGRAMS:
                head.append(token.upper())
                parts.pop(0)
            elif token.lower() in QUALIFIERS:
                parts.pop(0)
            else:
                break
        program = " ".join(head)
        clean = ": ".join(parts).strip() or title
        if clean.count(")") > clean.count("("):
            clean = clean.rstrip(")").strip()
            note(f"award #{award_no or '?'}: stripped an unbalanced ')' from the title")

        end_raw = a.get("final_date") or ""
        ongoing = "ongoing" in end_raw.lower()
        areas_here = [area_slug[x] for x in (a.get("projetcs") or []) if x in area_slug]

        row = {
            "slug": slugify(clean)[:48],
            "title": clean,
            "short": program + (f" {award_no}" if award_no else "") or clean[:24],
            "summary": next((area_desc[x][:240] for x in (a.get("projetcs") or [])
                             if area_desc.get(x)), ""),
            "status": "active" if ongoing else "completed",
            "start": parse_year(a.get("initial_date")),
            "end": "" if ongoing else parse_year(end_raw),
            "funder": "NSF" if award_no else "",
            "program": program,
            "award_no": award_no,
            "award_url": (a.get("access_link") or "").strip(),
            "amount": parse_amount(a.get("total_amount")),
            "role": "",
            "url": "",
            "members": "",
            "_areas": areas_here,
        }
        rows.append(row)
        if award_no:
            seen[award_no] = row

    # merge with what is already in projects.csv, matching on award number
    by_award = {r["award_no"]: r for r in rows if r["award_no"]}
    for slug, prev in existing_projects.items():
        aw = prev.get("award_no", "")
        if aw and aw in by_award:
            tgt = by_award[aw]
            for field in ("role", "url", "members", "funder"):
                if prev.get(field) and not tgt.get(field):
                    tgt[field] = prev[field]
            if prev.get("amount") and parse_amount(prev["amount"]) != tgt["amount"]:
                note(f"award #{aw}: current projects.csv says {prev['amount']}, "
                     f"old site says {tgt['amount']} — using the old site's figure, please verify")
            if prev.get("slug") and prev["slug"] != tgt["slug"]:
                tgt["slug"] = prev["slug"]   # keep existing URLs stable
                tgt["short"] = prev.get("short") or tgt["short"]
                tgt["summary"] = prev.get("summary") or tgt["summary"]
        else:
            rows.append({**prev, "_areas": []})
            note(f"kept project '{slug}' from the current projects.csv "
                 f"(no matching award in the old site)")

    # the old site linked people and awards indirectly, both via research areas
    for r in rows:
        implied = [m["slug"] for m in member_rows
                   if set(m.get("_areas") or []) & set(r.get("_areas") or [])]
        existing_members = [x for x in (r.get("members") or "").split(";") if x]
        r["members"] = ";".join(dict.fromkeys(existing_members + implied))

    fields = ["slug", "title", "short", "summary", "status", "start", "end", "funder",
              "program", "award_no", "award_url", "amount", "role", "url", "members"]
    write_csv(DATA / "projects.csv", fields, rows)

    # long descriptions, from the research area each award belongs to
    (DATA / "projects").mkdir(parents=True, exist_ok=True)
    written = 0
    for r in rows:
        text = next((area_desc[k] for k, v in area_slug.items()
                     if v in r.get("_areas", []) and area_desc.get(k)), "")
        if not text:
            continue
        p = DATA / "projects" / f"{r['slug']}.md"
        if p.exists():
            note(f"data/projects/{r['slug']}.md already exists — left untouched")
            continue
        p.write_text(text + "\n", encoding="utf-8")
        written += 1
    print(f"  wrote data/projects/*.md  ({written} descriptions)")
    return rows


# ----------------------------------------------------------------------- news


def migrate_news(old):
    posts = json.load((old / "public" / "posts.json").open(encoding="utf-8"))["posts"]
    rows, bodies = [], {}

    for p in posts:
        title = (p.get("title") or "").strip()
        if not title:
            continue
        date = (p.get("date") or "").strip()
        if re.fullmatch(r"\d{4}-\d{2}", date):
            date += "-01"
            note(f"news '{title[:40]}' had only a month ({p['date']}) — set to {date}")
        slug = slugify(p.get("id") or title)[:60]
        body = html_to_md(p.get("description") or "")
        first = body.split("\n\n")[0] if body else ""
        rows.append({
            "date": date,
            "slug": slug,
            "title": title,
            "tag": (p.get("tag") or "").strip().lower(),
            "url": (p.get("link") or "").strip(),
            "summary": first[:200] + ("…" if len(first) > 200 else ""),
            "projects": "",
        })
        if body and len(body) > len(first):
            bodies[slug] = body

    rows.sort(key=lambda r: r["date"], reverse=True)
    write_csv(DATA / "news.csv",
              ["date", "slug", "title", "tag", "url", "summary", "projects"], rows)

    (DATA / "news").mkdir(parents=True, exist_ok=True)
    for slug, text in bodies.items():
        (DATA / "news" / f"{slug}.md").write_text(text + "\n", encoding="utf-8")
    print(f"  wrote data/news/*.md  ({len(bodies)} bodies)")
    return rows


# ----------------------------------------------------------------------- main


def read_existing(path, key="slug"):
    if not path.exists():
        return {}
    text, _ = decode_bytes(path.read_bytes())
    with io.StringIO(text, newline="") as fh:
        out = {}
        for r in csv.DictReader(fh):
            k = (r.get(key) or "").strip()
            if k and not k.startswith("#"):
                out[k] = {kk: (vv or "").strip() for kk, vv in r.items() if kk}
        return out


def main():
    if len(sys.argv) < 2:
        sys.exit(f"usage: python {Path(__file__).name} <path-to-old-reshapelab-checkout>")
    old = Path(sys.argv[1]).expanduser().resolve()
    if not (old / "public" / "members.json").exists():
        sys.exit(f"{old} does not look like the old site (no public/members.json)")

    print(f"migrating from {old}\n")
    existing_members = read_existing(DATA / "members.csv")
    existing_projects = read_existing(DATA / "projects.csv")

    rows = migrate_members(old, existing_members)
    migrate_photos(rows, old)
    migrate_research_and_projects(old, existing_projects, rows)
    migrate_news(old)

    print(f"\n{len(NOTES)} thing(s) to review:")
    for n in NOTES:
        print(f"  - {n}")
    print("\nNext: python scripts/build_site.py")


if __name__ == "__main__":
    main()
