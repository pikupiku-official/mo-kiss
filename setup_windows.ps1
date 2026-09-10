param(
    [string]$Python = "python"
)

$ErrorActionPreference = "Stop"
$ProjectRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$Requirements = Join-Path $ProjectRoot "requirements.txt"
$SeedCheck = Join-Path $ProjectRoot "test_masuda_seed_free_text.py"

Write-Host "Installing mo-kiss runtime dependencies with $Python ..."
& $Python -m pip install -r $Requirements
if ($LASTEXITCODE -ne 0) {
    throw "Dependency installation failed (exit $LASTEXITCODE)."
}

Write-Host "Checking the bundled seed model ..."
& $Python $SeedCheck --judge "増田は真性包茎なんだ"
if ($LASTEXITCODE -ne 0) {
    throw "Seed model verification failed (exit $LASTEXITCODE)."
}

Write-Host "Setup complete. Start the game with: $Python main.py"
