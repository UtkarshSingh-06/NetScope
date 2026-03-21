#!/usr/bin/env bash
# Rewrite all commits: remove Co-authored-by trailers and set single author/committer.
# Run from repo root in Git Bash: bash scripts/rewrite-authors.sh
# Then: git push --force origin main

set -e
cd "$(dirname "$0")/.."

NAME="${GIT_AUTHOR_NAME:-Utkarsh Singh}"
EMAIL="${GIT_AUTHOR_EMAIL:-utkarsh.yash77@gmail.com}"

echo "Removing Co-authored-by trailers and rewriting to: $NAME <$EMAIL>"
export FILTER_BRANCH_SQUELCH_WARNING=1

# Remove all Co-authored-by lines from commit messages
git filter-branch -f --msg-filter 'sed -e "/^Co-authored-by:/d"' \
  --env-filter "
export GIT_AUTHOR_NAME='$NAME'
export GIT_AUTHOR_EMAIL='$EMAIL'
export GIT_COMMITTER_NAME='$NAME'
export GIT_COMMITTER_EMAIL='$EMAIL'
" --tag-name-filter cat -- --all

echo "Done. Run: git push --force origin main"
