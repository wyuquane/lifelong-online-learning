# Run the full AKLO reproduction matrix with W&B tracking.
#
# Examples:
#   .\scripts\reproduce_all.ps1
#   .\scripts\reproduce_all.ps1 -Experiments e1_main,e3_catastrophic-forgetting
#   .\scripts\reproduce_all.ps1 -NoWandb -Smoke -LimitPerExperiment 2
#
# The script never pushes to git. It writes local JSON files under results/
# and, unless -NoWandb is used, logs every run to the public W&B project
# configured in configs/base.yaml.

param(
    [string]$Experiments = "e1_main,e2_small_m,e3_catastrophic-forgetting,e4_sensitivity_cls,e5_sensitivity_reg,e6_akloms_tau,e7_akloms_models,e8_runtime",
    [switch]$NoWandb,
    [switch]$Smoke,
    [int]$LimitPerExperiment = 0,
    [switch]$SkipReport
)

$ErrorActionPreference = "Stop"
$root = Split-Path -Parent $PSScriptRoot
Set-Location $root

$arguments = @(
    "scripts/run_matrix.py",
    "--experiments", $Experiments,
    "--continue-on-error"
)
if ($NoWandb) {
    $arguments += "--no-wandb"
}
if ($Smoke) {
    $arguments += "--smoke"
}
if ($LimitPerExperiment -gt 0) {
    $arguments += @("--limit-per-experiment", "$LimitPerExperiment")
}

Write-Host "Running experiments: $Experiments"
python @arguments
$runExit = $LASTEXITCODE

if (-not $SkipReport) {
    Write-Host "Building report..."
    python scripts/make_report.py
}

if ($runExit -ne 0) {
    Write-Error "At least one experiment failed. See the output above."
    exit $runExit
}

Write-Host "Done. Results are in results/ and reports/report.md."
