# Complete walkthrough

From the zip to a live site at `www.reshapelab.site`, without the current site
going down at any point.

**Key fact that makes this safe:** `www.reshapelab.site` is served by **Vercel**,
not GitHub Pages. Vercel builds from `main`. So as long as we stay off `main`,
nothing public changes until you move DNS in step 14.

```
main         ──────────────────►  Vercel  ──►  www.reshapelab.site   (old, stays up)
static-site  ──────────────────►  Pages   ──►  reshapelab.github.io  (new, compare)
```

Roughly an hour of work, plus waiting on DBLP and DNS.

---

## The one thing that would break the live site

**Do not push to `main` until step 16.** Vercel auto-deploys its production
branch. The old site is a Vite app; a `main` without `package.json` gives Vercel
a build it cannot finish, and the live site is what breaks.

Everything below stays on `static-site`.

---

# Part 1 — Set up

## 1. Clone and branch

```bash
cd ~/workspace
git clone https://github.com/RESHAPELab/RESHAPELab.github.io.git reshapelab
cd reshapelab
git checkout --orphan static-site
git rm -rf . -q
```

`--orphan` starts a branch with no parent commit, so the new site's history is
not tangled with the Vue app's. `main` and `gh-pages` are untouched.

## 2. Keep a copy of the old content

The migration reads it:

```bash
cd ~/workspace
git clone --branch main --single-branch \
  https://github.com/RESHAPELab/RESHAPELab.github.io.git reshapelab-old
```

## 3. Unpack the new site onto the branch

Unzip `reshapelab-site.zip`, then from inside the unzipped `reshapelab` folder:

```bash
cp -R . ~/workspace/reshapelab/
cd ~/workspace/reshapelab
```

You should now have `scripts/`, `data/`, `assets/`, `README.md`, `CNAME`, and
`.github/workflows/build.yml`.

---

# Part 2 — Bring the content over

## 4. Migrate

```bash
python3 scripts/migrate_from_vue.py ../reshapelab-old
```

Nothing to install. Photos are resized with Pillow if you have it, otherwise
with `sips` (built into macOS), otherwise copied unchanged with a warning.

Expect:

```
  wrote data/members.csv  (36 rows)
  wrote data/people/*.md  (30 bios)
  wrote assets/people/*.jpg  (29 photos, 7 missing)
    75.6 MB  ->  1.31 MB
  wrote data/research.csv  (3 rows)
  wrote data/projects.csv  (8 rows)
  wrote data/news.csv  (6 rows)
  wrote data/news/*.md  (5 bodies)
```

**Read the review list at the end.** It flags conflicting funding amounts and
missing photos. Nothing blocks you.

> The zip already contains the migrated result, so this step mainly proves the
> script runs on your machine. Skip it if you would rather keep what shipped.

## 5. Build offline and look

```bash
python3 scripts/build_site.py --offline --no-oa
python3 -m http.server 8000
```

Open <http://localhost:8000>. Click through People, a member page, Projects, a
project page, Funding, News, a news item.

Publications show zero. Correct — nothing has fetched DBLP yet. Building offline
first proves the CSVs parse in about a second, so a malformed file surfaces
before you spend minutes on network calls.

## 6. Build for real

```bash
python3 scripts/build_site.py
```

One DBLP record per member pid, then Unpaywall once per DOI. A few minutes the
first time; later builds reuse `cache/`.

Now the site has content. Reload and check the publication list, the text
filter, and a member page.

---

# Part 3 — Fill the gaps (optional, improves quality)

Everything here can wait until after launch. Do as much or as little as you like.

## 7. Missing DBLP pids

21 of 36 members have one. Attribution is pid-only — a member without a pid gets
no papers and is not linked in author lists. Six current members are affected,
Pedro Oliveira most visibly.

```bash
python3 scripts/find_pids.py                 # everyone missing one
python3 scripts/find_pids.py pedro-oliveira  # just one
```

It searches DBLP by name and ranks candidates by how many papers they share with
the members who already have pids. Two or more shared papers with you or Marco
is strong evidence. It prints evidence and **writes nothing** — a wrong pid
silently imports a stranger's whole career, so copy the pid into
`data/members.csv` yourself.

Note: Pedro appears on DBLP as both **Pedro Oliveira** and **Pedro Arantes**. He
may have two profiles that need merging on DBLP's side.

## 8. Missing start and end dates

`started` and `ended` bound which of an alumnus's papers count as lab work.
`dates_to_fill.csv` lists everyone missing something, with a `still_needed`
column. Fill what you know, leave the rest blank:

```bash
python3 scripts/apply_dates.py dates_to_fill.csv
```

Merges by slug, writes only non-blank cells, prints every change, backs up
`members.csv` first. Safe to run repeatedly.

**Excel is fine.** It saves CSV as Mac Roman rather than UTF-8, which turns
`João` into a byte no UTF-8 reader accepts. The scripts detect that and decode it
anyway, so you can edit the worksheet however you like. Only `slug`, `dblp_pid`,
`started` and `ended` are read from it, and all four are plain ASCII — names are
never taken from the worksheet, so they cannot be mangled by a bad round-trip.
`members.csv` is always written back as UTF-8.

Years are enough — no months. Only alumni **with a pid** are worth dating; the
others contribute no papers either way.

## 9. Check what the alumni filter removed

```bash
python3 scripts/build_site.py
cat dropped_pubs.md
```

Papers where no lab member was present when they appeared are dropped. To rescue
one, put its DBLP key in `data/include_pubs.txt`.

## 10. Missing photos

Seven people have none and show a green initials tile. Drop a square JPEG at
`assets/people/<slug>.jpg`. The build names the exact file it expected.

---

# Part 4 — Publish

## 11. Push the branch

```bash
git add -A
git commit -m "RESHAPE Lab site: static HTML generated from data/"
git push -u origin static-site
```

Nothing public has changed. Vercel ignores this branch.

## 12. Turn on Pages

In **Settings** on this repo:

1. **Pages → Build and deployment → Source** → **GitHub Actions**
   Not "Deploy from a branch" — a workflow pushing with `GITHUB_TOKEN` cannot
   trigger a branch build, so the monthly DBLP refresh would never go live.
2. **Actions → General → Workflow permissions** → **Read and write**
3. **Settings → Environments → github-pages → Deployment branches** → add
   `static-site`. Easy to miss: GitHub restricts this environment to the default
   branch, and without this the deploy step fails with an environment
   protection error rather than anything informative.

## 13. Run it

**Actions → Build and deploy → Run workflow**, choosing the `static-site` branch.

When it goes green: <https://reshapelab.github.io/>

Both sites are now live — the old one on the real domain, the new one on
github.io. Compare them, show Marco, sit on it as long as you like.

The workflow deploys only from `static-site` (`DEPLOY_BRANCH` at the top of the
file). Pull requests and other branches build as a check and deploy nothing.

---

# Part 5 — Switch the domain

## 14. Point DNS at GitHub

**Settings → Pages → Custom domain** → `www.reshapelab.site` → Save.

Do this **before** DNS. A hostname pointed at GitHub that no repo has claimed is
how subdomain takeovers happen.

See what is there now:

```bash
dig www.reshapelab.site +noall +answer
dig reshapelab.site +noall +answer -t A
```

You will find Vercel records — a CNAME on `www` to a `*.vercel-dns.com` host and
an A record on the apex. **Delete those**, then add:

| Type | Name | Value |
| --- | --- | --- |
| CNAME | `www` | `reshapelab.github.io` |
| A | `@` | `185.199.108.153` |
| A | `@` | `185.199.109.153` |
| A | `@` | `185.199.110.153` |
| A | `@` | `185.199.111.153` |

The CNAME points at the org domain with **no repository name after it**. The
four A records make bare `reshapelab.site` redirect to the `www` version.

Optional IPv6 on the apex: `2606:50c0:8000::153`, `2606:50c0:8001::153`,
`2606:50c0:8002::153`, `2606:50c0:8003::153`.

## 15. Wait, then enforce HTTPS

```bash
dig www.reshapelab.site +noall +answer      # expect reshapelab.github.io
dig reshapelab.site +noall +answer -t A     # expect the four 185.199.x IPs
```

Once both resolve, **Settings → Pages** → tick **Enforce HTTPS**. Greyed out
means the certificate is not issued yet, which only happens after DNS resolves —
wait rather than reconfiguring. Still greyed out after a few hours: remove the
custom domain, save, re-add, save again.

**Rollback here is a DNS revert.** Put the Vercel records back and the old site
returns. Keep that option for a week or two before Part 6.

---

# Part 6 — Tidy up, when you are confident

## 16. Retire Vercel and promote the branch

Order matters:

1. **In Vercel**, disconnect the Git integration or delete the project. First —
   or the next push triggers a failing build.
2. Make `static-site` the default branch: **Settings → General → Default
   branch**. (Or merge into `main` with
   `git merge --allow-unrelated-histories static-site`.)
3. Edit `.github/workflows/build.yml`, set `DEPLOY_BRANCH: main`.
4. **Settings → Environments → github-pages** — drop the `static-site` rule.

## 17. Delete the one-off scripts

```bash
rm scripts/migrate_from_vue.py
rm -f data/*.pre-migration
# once the roster is complete:
rm scripts/find_pids.py scripts/apply_dates.py dates_to_fill.csv
git commit -am "Remove one-off migration scripts"
git push
```

## 18. Turn off Pages anywhere else in the org

A custom domain on an **organization** site is inherited by every project site
in the account: any RESHAPELab repo with Pages enabled is served at
`www.reshapelab.site/<repo>/`. Among the public repos only this one has it, but
private repos are not visible from outside — check the org and switch off
anything you do not want published there.

---

# Afterwards

## Publishing a change

```bash
./scripts/publish.sh "Add Morgan's DBLP pid"
```

Builds, stages everything, commits, pulls, pushes. Or by hand:

```bash
python3 scripts/build_site.py
git add -A
git commit -m "Add Morgan's DBLP pid"
git pull --rebase
git push
```

Three things about this repo that are easy to get wrong:

**Commit the generated HTML.** `git add -A`, not just `data/`. GitHub Pages
serves the repo as-is, so the HTML has to be in it. `.gitignore` already excludes
the things that should not be committed.

**Pull before you push.** The CI workflow commits regenerated files back to the
branch, so the remote usually has one commit you do not. Skip the pull and your
next push is rejected as non-fast-forward.

**Build locally first.** Then CI finds nothing to change and adds no commit at
all, which keeps the branch linear and avoids the previous problem entirely.
`publish.sh` does this in the right order.

`publish.sh` refuses to run on `main` until you disconnect Vercel — a push there
would fail the Vercel build and take the live site down.

## Day-to-day

| Task | What to do |
| --- | --- |
| New paper | Nothing. The monthly job picks it up from DBLP. |
| New member | Row in `data/members.csv` + photo at `assets/people/<slug>.jpg` |
| Someone graduates | Set their `group` to `alumni`, fill `ended` and `now` |
| New project | Row in `data/projects.csv`, optional `data/projects/<slug>.md` |
| News item | Row in `data/news.csv`, optional `data/news/<slug>.md` |
| Paper award | Row in `data/pub_tags.csv` |
| Link paper to project | `projects` column in `data/pub_tags.csv` |
| Self-host a PDF | Drop it at `publications/<dblp-key-with-dashes>.pdf` |

Push to the deploy branch and the workflow rebuilds and republishes.

## Reports the build writes

- `dropped_pubs.md` — papers the alumni filter removed, with keys to rescue them
- `missing_pdfs.md` — papers with no open version, with the filename to use
- `pub_index.csv` — every harvested paper and its DBLP key

Every build also ends with a warning list naming the exact file or cell at fault.
Read it before assuming the generator is wrong.

## Rolling back

Nothing is destroyed at any stage. The Vue app stays on `main` and `gh-pages`.
Before step 14, rollback is doing nothing. After, it is putting the Vercel DNS
records back.
