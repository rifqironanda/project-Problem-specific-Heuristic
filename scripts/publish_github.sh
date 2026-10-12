#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
command -v gh >/dev/null || { echo 'Install GitHub CLI (gh) first'; exit 1; }
gh auth status
owner=$(gh api user --jq .login)
repo="$owner/project-Problem-specific-Heuristic"
if ! git rev-parse --git-dir >/dev/null 2>&1; then
  git init -b main
  git add .
  git commit -m 'Build reproducible MinVola heuristic and AI application'
fi
if gh repo view "$repo" >/dev/null 2>&1; then
  echo "Repository already exists: $repo. Inspect before pushing. No files pushed."
  exit 0
fi
gh repo create "$repo" --private --source=. --remote=origin --push
