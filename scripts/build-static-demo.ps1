$ErrorActionPreference = "Stop"
$src = "C:\Users\hp\Downloads\EduAccess-AI\EduAccess-AI\frontend\next-app"
$out = "C:\Users\hp\Downloads\EduAccess-AI\EduAccess-AI\demosite"
$tmp = "C:\Users\hp\Downloads\EduAccess-AI\EduAccess-AI\.static-build"

# Clean temp build dir
if (Test-Path -LiteralPath $tmp) {
    Remove-Item -LiteralPath $tmp -Recurse -Force
}
New-Item -ItemType Directory -Path $tmp | Out-Null

# Copy project files, excluding heavy/locked dirs
robocopy $src $tmp /E /XD node_modules .next out .vercel /NFL /NDL /NJH /NJS /NC /NS
if ($LASTEXITCODE -ge 8) { throw "robocopy failed with code $LASTEXITCODE" }

# Junction node_modules (same instance the app already has, avoids 800MB copy)
New-Item -ItemType Junction -Path "$tmp\node_modules" -Target "$src\node_modules" | Out-Null

# Remove Next.js Route Handlers: they need a server runtime and are not
# compatible with `output: export`. Demo mode never calls them.
$apiDir = Join-Path $tmp "app\api"
if (Test-Path -LiteralPath $apiDir) {
    Remove-Item -LiteralPath $apiDir -Recurse -Force
    Write-Host "app/api removed in build copy"
}

$env:NEXT_STATIC_EXPORT = "1"
$env:NEXT_PUBLIC_ENABLE_DEMO_MODE = "1"
$env:NEXT_PUBLIC_BASE_PATH = "/EduAccessAI"
$env:NEXT_PUBLIC_ASSET_PREFIX = "/EduAccessAI/"

try {
    Push-Location $tmp
    Write-Host "Building static export (this may take a while)..."
    npm run build
    if ($LASTEXITCODE -ne 0) { throw "next build failed" }

    if (Test-Path -LiteralPath $out) { Remove-Item -LiteralPath $out -Recurse -Force }
    New-Item -ItemType Directory -Path $out -Force | Out-Null
    Copy-Item -Path (Join-Path $tmp "out\*") -Destination $out -Recurse -Force
    Write-Host "Static site copied to $out"
    Pop-Location
}
finally {
    Pop-Location -ErrorAction SilentlyContinue
    Remove-Item Env:NEXT_STATIC_EXPORT -ErrorAction SilentlyContinue
    Remove-Item Env:NEXT_PUBLIC_ENABLE_DEMO_MODE -ErrorAction SilentlyContinue
    Remove-Item Env:NEXT_PUBLIC_BASE_PATH -ErrorAction SilentlyContinue
    Remove-Item Env:NEXT_PUBLIC_ASSET_PREFIX -ErrorAction SilentlyContinue
}