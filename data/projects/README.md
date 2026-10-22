# Long project descriptions

One optional Markdown file per project, named after the project's `slug`
column in `../projects.csv`:

    data/projects/oss-doorway.md   ->   projects/oss-doorway.html

Everything factual (funder, amount, dates, team, links) lives in the CSV.
This file holds only the prose that appears under "About" on the project page.

Supported formatting: paragraphs, `## Heading`, `- bullets`, `[links](url)`,
`**bold**`, `*italic*`, and `` `code` ``. Nothing else — keep it plain.

A project with no file here still gets a page; it just shows the `summary`
from the CSV.
