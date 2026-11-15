param([string]$Python = (Join-Path (Split-Path -Parent $PSScriptRoot) '.venv/Scripts/python.exe'))
$ErrorActionPreference = 'Stop'
Push-Location (Split-Path -Parent $PSScriptRoot)
try {
    & $Python -c "import sys, swisseph; assert (3, 12) <= sys.version_info[:2] < (3, 14), 'Calculations require Python 3.12 or 3.13'"
    if ($LASTEXITCODE -ne 0) { throw 'Calculation engine unavailable. Run bootstrap.ps1 with an approved Python 3.12/3.13 interpreter.' }
    & $Python -m pytest tests/test_calculations.py
    if ($LASTEXITCODE -ne 0) { throw 'Calculation tests failed.' }
} finally {
    Pop-Location
}
