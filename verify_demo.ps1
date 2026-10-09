$ErrorActionPreference = "Stop"
$ProjectRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$Python = Join-Path $ProjectRoot ".venv\Scripts\python.exe"

if (-not (Test-Path -LiteralPath $Python)) {
    throw "Virtual environment not found. Follow SETUP_WINDOWS.md first."
}

function Invoke-VerificationStep {
    param(
        [Parameter(Mandatory = $true)][string]$Name,
        [Parameter(Mandatory = $true)][scriptblock]$Command
    )

    Write-Host "`n== $Name =="
    & $Command
    if ($LASTEXITCODE -ne 0) {
        throw "$Name failed with exit code $LASTEXITCODE."
    }
}

Set-Location -LiteralPath $ProjectRoot
Invoke-VerificationStep -Name "Environment preflight" -Command {
    & $Python scripts\preflight.py --skip-port-check
}
Invoke-VerificationStep -Name "Unit and integration tests" -Command {
    & $Python -m pytest -v
}
Invoke-VerificationStep -Name "Ruff lint" -Command {
    & $Python -m ruff check .
}
Invoke-VerificationStep -Name "Ruff formatting" -Command {
    & $Python -m ruff format --check .
}
Invoke-VerificationStep -Name "A2A service health" -Command {
    & $Python scripts\check_services.py
}
Invoke-VerificationStep -Name "Portal smoke test" -Command {
    & $Python scripts\smoke_portal.py
}

Write-Host "`nDemo verification passed."
