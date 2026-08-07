#!/usr/bin/env python3
"""
find_pids.py — suggest DBLP pids for members who have none.

    python scripts/find_pids.py                 # everyone missing a pid
    python scripts/find_pids.py pedro-oliveira  # just one person

For each candidate DBLP profile it counts how many papers that person shares
with the lab members who already have a pid, and prints the candidates ranked
by that overlap. Shared papers with Igor or Marco are strong evidence you have
the right "Pedro Oliveira" out of the dozens DBLP knows about.

It never edits members.csv. Read the evidence, then paste the pid into
`data/members.csv` yourself, or into the worksheet for scripts/apply_dates.py.
A wrong pid silently imports a stranger's entire publication record, so this
step stays manual on purpose.

Needs network access to dblp.org. No third-party packages.
"""

import csv
import json
import re
import sys
import time
import unicodedata
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
MEMBERS = ROOT / "data" / "members.csv"
MAX_CANDIDATES = 6
PAUSE = 1.2   # be polite to dblp.org


def fold(name):
    d = unicodedata.normalize("NFKD", (name or "").lower())
    return re.sub(r"[^a-z0-9]+", " ", "".join(c for c in d if not unicodedata.combining(c))).strip()


def fetch(url):
    req = urllib.request.Request(url, headers={"User-Agent": "reshapelab-pid-finder/1.0"})
    with urllib.request.urlopen(req, timeout=45) as r:
        return r.read()


def author_search(name):
    """Ask DBLP for author profiles matching a name."""
    q = urllib.parse.quote(name)
    url = f"https://dblp.org/search/author/api?q={q}&format=json&h={MAX_CANDIDATES}"
    try:
        data = json.loads(fetch(url))
    except Exception as exc:
        print(f"    ! search failed: {exc}")
        return []
    hits = (data.get("result", {}).get("hits", {}) or {}).get("hit", []) or []
    out = []
    for h in hits:
        info = h.get("info", {})
        url_ = info.get("url", "")
        m = re.search(r"/pid/(.+?)(?:\.html)?$", url_)
        if not m:
            continue
        notes = info.get("notes", {}).get("note", [])
        if isinstance(notes, dict):
            notes = [notes]
        affil = "; ".join(n.get("text", "") for n in notes if n.get("@type") == "affiliation")
        out.append({"pid": m.group(1), "name": info.get("author", ""), "affiliation": affil})
    return out


def paper_keys(pid):
    """Every formal publication key in a DBLP author record."""
    try:
        root = ET.fromstring(fetch(f"https://dblp.org/pid/{pid}.xml"))
    except Exception:
        return set(), []
    keys, coauthors = set(), []
    for r in root.iter("r"):
        if not len(r):
            continue
        pub = r[0]
        if pub.tag not in ("article", "inproceedings") or pub.get("publtype") == "informal":
            continue
        keys.add(pub.get("key", ""))
        coauthors += [a.text or "" for a in pub.findall("author")]
    return keys, coauthors


def main():
    with MEMBERS.open(newline="", encoding="utf-8-sig") as fh:
        rows = list(csv.DictReader(fh))

    known = {r["slug"]: r["dblp_pid"] for r in rows if r["dblp_pid"]}
    if not known:
        sys.exit("No member has a dblp_pid yet — there is nothing to match against.")

    print(f"Loading {len(known)} known lab records for comparison...")
    lab_keys, lab_names = set(), Counter()
    for slug, pid in known.items():
        keys, coauthors = paper_keys(pid)
        lab_keys |= keys
        lab_names.update(fold(c) for c in coauthors)
        time.sleep(PAUSE)
    print(f"  {len(lab_keys)} lab papers, {len(lab_names)} distinct co-author names\n")

    wanted = sys.argv[1:]
    targets = [r for r in rows if not r["dblp_pid"] and (not wanted or r["slug"] in wanted)]
    if not targets:
        print("Nobody to look up.")
        return

    for r in targets:
        print(f"{r['name']}  ({r['role']})")
        if fold(r["name"]) not in lab_names:
            print("    no paper in the lab's records lists this name — they may publish")
            print("    under a different spelling, or have no DBLP record at all")
        for c in author_search(r["name"]):
            keys, _ = paper_keys(c["pid"])
            shared = len(keys & lab_keys)
            time.sleep(PAUSE)
            mark = "  <-- likely" if shared >= 2 else ("  <-- maybe" if shared == 1 else "")
            affil = f" | {c['affiliation'][:52]}" if c["affiliation"] else ""
            print(f"    {c['pid']:14} {c['name'][:30]:30} {shared:3} shared{affil}{mark}")
        print()

    print("Nothing was written. Copy the pids you are confident about into")
    print("data/members.csv, then run: python scripts/build_site.py")


if __name__ == "__main__":
    main()
