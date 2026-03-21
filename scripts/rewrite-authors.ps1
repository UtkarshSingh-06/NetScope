# Rewrite all commits to have a single author/committer (removes other contributors from GitHub).
# Run from repo root in Git Bash or WSL to avoid Windows signal pipe issues.
#
# Steps (run these in Git Bash or your terminal from the repo root):
#
# 1. Set your name and email (use your GitHub email or noreply):
#    export GIT_AUTHOR_NAME="Utkarsh Singh"
#    export GIT_AUTHOR_EMAIL="utkarsh.yash77@gmail.com"
#
# 2. Rewrite history:
#    git filter-branch -f --env-filter '
#      export GIT_AUTHOR_NAME="Utkarsh Singh"
#      export GIT_AUTHOR_EMAIL="utkarsh.yash77@gmail.com"
#      export GIT_COMMITTER_NAME="Utkarsh Singh"
#      export GIT_COMMITTER_EMAIL="utkarsh.yash77@gmail.com"
#    ' --tag-name-filter cat -- --all
#
# 3. Force-push to update GitHub (this recalculates contributors):
#    git push --force origin main
#
# GitHub will then show only you as the contributor.
param(
    [string]$AuthorName = "Utkarsh Singh",
    [string]$AuthorEmail = "utkarsh.yash77@gmail.com"
)

$ErrorActionPreference = "Stop"
$repoRoot = Split-Path -Parent (Split-Path -Parent $MyInvocation.MyCommand.Path)
Set-Location $repoRoot

Write-Host "To remove extra contributors, run these commands in Git Bash from this repo:"
Write-Host ""
Write-Host '  git filter-branch -f --env-filter "export GIT_AUTHOR_NAME=''"'$AuthorName''"'; export GIT_AUTHOR_EMAIL=''"'$AuthorEmail''"'; export GIT_COMMITTER_NAME=''"'$AuthorName''"'; export GIT_COMMITTER_EMAIL=''"'$AuthorEmail''"'" --tag-name-filter cat -- --all'
Write-Host "  git push --force origin main"
Write-Host ""
