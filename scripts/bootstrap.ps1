param([string]$Python = '3.12')
$ErrorActionPreference = 'Stop'
$projectRoot = Split-Path -Parent $PSScriptRoot
Push-Location $projectRoot
try {
    if (Get-Command uv -ErrorAction SilentlyContinue) {
        & uv sync --frozen --python $Python
    } else {
        & python -m uv sync --frozen --python $Python
    }
    if ($LASTEXITCODE -ne 0) { throw 'Dependency sync failed. See implementation/RUNBOOK.md.' }
    & ./.venv/Scripts/python.exe -c "import sys, swisseph; assert (3, 12) <= sys.version_info[:2] < (3, 14); print('Calculation runtime ready:', sys.version.split()[0], swisseph.version)"
    if ($LASTEXITCODE -ne 0) { throw 'Use an approved Python 3.12 or 3.13 interpreter with native extension support.' }
} finally {
    Pop-Location
}
