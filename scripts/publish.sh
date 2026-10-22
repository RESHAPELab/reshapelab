#!/usr/bin/env bash
#
# publish.sh — build the site, commit everything, and push.
#
#   ./scripts/publish.sh                       # build, commit, push
#   ./scripts/publish.sh "Add Morgan's pid"    # with your own commit message
#   ./scripts/publish.sh --offline             # skip the network during the build
#
# Why a script rather than three git commands: the CI workflow also commits the
# regenerated files back to the branch. If you push without pulling first, your
# next push is rejected as non-fast-forward. Building locally before you push
# means CI finds nothing to change and adds no commit at all, so the branch
# stays linear.
#
# It refuses to run on `main`, because Vercel still deploys `main` and a push
# there would break the live site.

set -euo pipefail
cd "$(dirname "$0")/.."

if ! git rev-parse --git-dir >/dev/null 2>&1; then
  echo "Not a git repository. Run this from inside your clone." >&2
  exit 1
fi

# `git rev-parse --abbrev-ref HEAD` blows up on a branch with no commits yet,
# which is exactly what `git checkout --orphan` and a fresh `git init` give you.
# --show-current handles that; symbolic-ref is the fallback for older git.
BRANCH="$(git branch --show-current 2>/dev/null || git symbolic-ref --short -q HEAD || true)"
if [ -z "$BRANCH" ]; then
  echo "Detached HEAD — check out a branch first: git checkout -b static-site" >&2
  exit 1
fi

FIRST_COMMIT=no
if ! git rev-parse --verify -q HEAD >/dev/null; then
  FIRST_COMMIT=yes
  echo "==> '$BRANCH' has no commits yet; this will be the first."
fi

if ! git remote get-url origin >/dev/null 2>&1; then
  cat >&2 <<'NOREMOTE'
No `origin` remote is configured, so there is nowhere to push. If you started
this folder with `git init` rather than by cloning, add the remote:

    git remote add origin https://github.com/RESHAPELab/RESHAPELab.github.io.git
    git fetch origin

NOREMOTE
  exit 1
fi
MESSAGE=""
BUILD_ARGS=()

# macOS ships bash 3.2, where expanding an empty array under `set -u` is an
# error (fixed in bash 4.4). Every array touch below is length-guarded.
if [ $# -gt 0 ]; then
  for arg in "$@"; do
    case "$arg" in
      --*) BUILD_ARGS+=("$arg") ;;
      *)   MESSAGE="$arg" ;;
    esac
  done
fi

if [ "$BRANCH" = "main" ]; then
  cat >&2 <<'WARN'
Refusing to publish from `main`.

Vercel still deploys `main`, and this repo has no package.json — pushing here
would fail the Vercel build and take www.reshapelab.site down. Switch to the
deploy branch first:

    git checkout static-site

Once Vercel is disconnected (Part 6 of WALKTHROUGH.md), delete this check.
WARN
  exit 1
fi

echo "==> Building on '$BRANCH'"
if [ ${#BUILD_ARGS[@]} -gt 0 ]; then
  python3 scripts/build_site.py "${BUILD_ARGS[@]}"
else
  python3 scripts/build_site.py
fi

echo
echo "==> Staging"
git add -A

if git diff --cached --quiet; then
  echo "Nothing changed. Not committing."
  exit 0
fi

git -c color.status=always status --short | sed 's/^/    /'
echo

if [ -z "$MESSAGE" ]; then
  MESSAGE="Update site content"
fi
git commit -q -m "$MESSAGE"
echo "==> Committed: $MESSAGE"

if git ls-remote --exit-code --heads origin "$BRANCH" >/dev/null 2>&1; then
  echo "==> Pulling first (the CI bot commits to this branch too)"
  git pull --rebase origin "$BRANCH"
else
  echo "==> Branch is not on the remote yet; nothing to pull"
fi

echo "==> Pushing"
git push -u origin "$BRANCH"

echo
echo "Done. Watch the deploy:"
echo "  https://github.com/RESHAPELab/RESHAPELab.github.io/actions"
