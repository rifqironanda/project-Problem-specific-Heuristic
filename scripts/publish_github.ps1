$ErrorActionPreference = 'Stop'
Set-Location (Join-Path $PSScriptRoot '..')
if (-not (Get-Command gh -ErrorAction SilentlyContinue)) { throw 'Install GitHub CLI: winget install GitHub.cli' }
gh auth status
if ($LASTEXITCODE -ne 0) { throw 'Run gh auth login first' }
$owner = gh api user --jq .login
$repo = "$owner/project-Problem-specific-Heuristic"
if (-not (Test-Path '.git')) {
  git init -b main
  git add .
  git commit -m 'Build reproducible MinVola heuristic and AI application'
  if ($LASTEXITCODE -ne 0) { throw 'Git commit failed; set user.name and user.email' }
}
gh repo view $repo 2>$null | Out-Null
if ($LASTEXITCODE -eq 0) {
  Write-Host "Repository already exists: $repo. Inspect before pushing. No files pushed."
  exit 0
}
gh repo create $repo --private --source=. --remote=origin --push
if ($LASTEXITCODE -ne 0) { throw 'GitHub creation/push failed' }
