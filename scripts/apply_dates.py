#!/usr/bin/env python3
"""
apply_dates.py — merge a filled-in worksheet back into data/members.csv.

    python scripts/apply_dates.py dates_to_fill.csv

Reads `slug` plus any of `dblp_pid`, `started`, `ended` and writes those values
into the matching row of data/members.csv. Blank cells are left alone, so you
can fill the worksheet in over several sittings. Every change is printed, and
the original is copied to data/members.csv.bak first.

Delete this script once the roster is complete.
"""
import csv
import io
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
MEMBERS = ROOT / "data" / "members.csv"
FIELDS = ("dblp_pid", "started", "ended")

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



def main():
    if len(sys.argv) < 2:
        sys.exit("usage: python scripts/apply_dates.py <filled-worksheet.csv>")
    sheet = Path(sys.argv[1]).expanduser()
    if not sheet.exists():
        sys.exit(f"{sheet} not found")

    text, enc = decode_bytes(MEMBERS.read_bytes())
    if not enc.startswith("utf-8"):
        print(f"  note: data/members.csv is {enc}, not UTF-8 — reading it anyway, "
              f"and rewriting it as UTF-8")
    with io.StringIO(text, newline="") as fh:
        reader = csv.DictReader(fh)
        cols = reader.fieldnames
        rows = list(reader)
    by_slug = {r["slug"]: r for r in rows}

    text, enc = decode_bytes(sheet.read_bytes())
    if not enc.startswith("utf-8"):
        print(f"  note: {sheet.name} is {enc}, not UTF-8 (Excel does this by "
              f"default) — decoded it anyway")
    with io.StringIO(text, newline="") as fh:
        updates = list(csv.DictReader(fh))

    # Only slug, dblp_pid, started and ended are read, and all four are ASCII —
    # so even if the encoding guess is wrong, the values written are correct.
    # Names are never taken from the worksheet.
    changed = missing = 0
    for u in updates:
        slug = (u.get("slug") or "").strip()
        row = by_slug.get(slug)
        if not row:
            if slug:
                print(f"  ?  no member with slug {slug!r}")
                missing += 1
            continue
        for f in FIELDS:
            new = (u.get(f) or "").strip()
            if new and new != row.get(f, ""):
                print(f"  +  {row['name']:26} {f} {row.get(f) or '—'} -> {new}")
                row[f] = new
                changed += 1

    if not changed:
        print("Nothing to change.")
        return
    shutil.copy2(MEMBERS, MEMBERS.with_suffix(".csv.bak"))
    with MEMBERS.open("w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=cols, extrasaction="ignore")
        w.writeheader()
        w.writerows(rows)
    print(f"\n{changed} value(s) written to data/members.csv "
          f"(original saved as members.csv.bak)")
    if missing:
        print(f"{missing} worksheet row(s) matched no member.")
    print("Next: python scripts/build_site.py")


if __name__ == "__main__":
    main()
