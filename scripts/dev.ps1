param([Parameter(ValueFromRemainingArguments=$true)][string[]]$Arguments)
$projectRoot = Split-Path -Parent $PSScriptRoot
$previousPythonPath = $env:PYTHONPATH
$previousAutoload = $env:PYTEST_DISABLE_PLUGIN_AUTOLOAD
try {
  $env:PYTHONPATH = (Join-Path $projectRoot 'src') + ';' + (Join-Path $projectRoot '.runtime314')
  $env:PYTEST_DISABLE_PLUGIN_AUTOLOAD = '1'
  & python @Arguments
  exit $LASTEXITCODE
} finally {
  $env:PYTHONPATH = $previousPythonPath
  $env:PYTEST_DISABLE_PLUGIN_AUTOLOAD = $previousAutoload
}
