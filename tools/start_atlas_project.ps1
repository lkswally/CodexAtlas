param(
    [Parameter(Mandatory = $true)]
    [string]$ProjectPath,
    [string]$ProjectProfile
)

$ErrorActionPreference = "Stop"
$atlasRoot = Split-Path -Parent $PSScriptRoot
$auditTool = Join-Path $PSScriptRoot "atlas_context_audit.py"
$bootstrapTool = Join-Path $PSScriptRoot "atlas_project_bootstrap.py"

Write-Host "== Atlas context audit =="
python $auditTool --project $ProjectPath

Write-Host ""
Write-Host "== Atlas governance bootstrap =="
if ($ProjectProfile) {
    python $bootstrapTool --project $ProjectPath --project-profile $ProjectProfile
}
else {
    python $bootstrapTool --project $ProjectPath
}

Write-Host ""
Write-Host "== Atlas context audit after bootstrap =="
python $auditTool --project $ProjectPath
