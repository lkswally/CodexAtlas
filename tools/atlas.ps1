param(
    [Parameter(Mandatory = $true)]
    [string]$ProjectPath,
    [Parameter(Mandatory = $true)]
    [string]$Task,
    [ValidateSet("plan", "execute", "audit")]
    [string]$Mode = "plan",
    [switch]$DryRun,
    [string]$RequireDispatcher = "true"
)

$ErrorActionPreference = "Stop"
$scriptRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$runner = Join-Path $scriptRoot "atlas_run.py"

$argsList = @(
    $runner,
    "--project-path", $ProjectPath,
    "--task", $Task,
    "--mode", $Mode,
    "--require-dispatcher", $RequireDispatcher
)

if ($DryRun) {
    $argsList += "--dry-run"
}

python @argsList
