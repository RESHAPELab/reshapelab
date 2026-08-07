# Build cache — commit this directory

- `dblp/<pid>.xml` — one DBLP author record per member pid
- `oa_cache.json` — Unpaywall answers, keyed by DOI

Both are committed on purpose. They make builds reproducible, let
`--offline` work, and keep the monthly CI run from hammering dblp.org and
Unpaywall. Delete a file to force a refetch, or use `--refresh-dblp` /
`--refresh-oa`.
