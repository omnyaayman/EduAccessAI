$ErrorActionPreference = "Stop"
$repo = "omnyaayman/EduAccessAI"
$site = "C:\Users\hp\Downloads\EduAccess-AI\EduAccess-AI\demosite"
$tmp = "C:\Users\hp\Downloads\EduAccess-AI\EduAccess-AI\.pages-build"

if (-not (Test-Path -LiteralPath "$site\index.html")) {
    throw "demosite/index.html not found - run build-static-demo.ps1 first"
}

# Prepare a clean deploy workspace
if (Test-Path -LiteralPath $tmp) { Remove-Item -LiteralPath $tmp -Recurse -Force }
New-Item -ItemType Directory -Path $tmp | Out-Null

# Copy static site + .nojekyll (so Jekyll won't ignore the _next folder)
Copy-Item -Path (Join-Path $site "*") -Destination $tmp -Recurse -Force
Set-Content -LiteralPath "$tmp\.nojekyll" -Value ""

Push-Location $tmp
try {
    git init -q
    git checkout -qb gh-pages
    git config user.name "omnyaayman"
    git config user.email "omnyaayman@users.noreply.github.com"
    git add -A
    git commit -q -m "Static demo site for EduAccess AI (demo mode, no backend)"
    git push -qf "https://x-access-token:$(gh auth token)@github.com/$repo.git" gh-pages
    Write-Host "Pushed demosite to gh-pages branch"
}
finally {
    Pop-Location
}

# Enable GitHub Pages pointing at the gh-pages branch (idempotent)
$pages = gh api "repos/$repo/pages" -X GET 2>$null
if ($LASTEXITCODE -ne 0) {
    gh api "repos/$repo/pages" -X POST -f "source[branch]=gh-pages" -f "source[path]=/" | Out-Null
    Write-Host "Enabled GitHub Pages"
} else {
    gh api "repos/$repo/pages" -X PUT -f "source[branch]=gh-pages" -f "source[path]=/" | Out-Null
    Write-Host "GitHub Pages already enabled; source set to gh-pages"
}

Start-Sleep -Seconds 3
$live = Invoke-RestMethod -Uri "https://api.github.com/repos/$repo/pages" -Headers @{ Authorization = "token $(gh auth token)" }
Write-Host "Live URL: $($live.html_url)"