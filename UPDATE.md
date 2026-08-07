# Code-only update

Unzip **over** your working copy. Touches nothing that holds content:

    overwritten     scripts/*, assets/style.css, assets/*.svg,
                    .github/workflows/build.yml, README.md, WALKTHROUGH.md
    never touched   data/**, assets/people/**, publications/**, cache/**, *.html

```bash
cd ~/workspace/reshapelab
unzip -o ~/Downloads/reshapelab-code-update.zip
chmod +x scripts/publish.sh
```

The shell script targets bash 3.2, which is what macOS still ships.

## Cosmetic fix the update cannot make (it lives in your data/)

Two projects have slugs auto-generated from NSF titles, and slugs are permanent
URLs. In `data/projects.csv`, rename:

    chs-shf-small-collaborative-research-scaffolding  ->  skill-acquisition-onboarding
    learning-software-engineering-by-contributing-to  ->  learning-by-contributing

Rename any matching file in `data/projects/` to match.
