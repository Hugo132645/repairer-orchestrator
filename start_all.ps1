$ErrorActionPreference = "Stop"
$ProjectRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$Python = Join-Path $ProjectRoot ".venv\Scripts\python.exe"

if (-not (Test-Path $Python)) {
    throw "Virtual environment not found. Run the installation steps in SETUP_WINDOWS.md first."
}
if (-not (Test-Path (Join-Path $ProjectRoot ".env"))) {
    Write-Warning ".env does not exist. Copy .env.example to .env and configure the selected LLM provider."
}

Write-Host "Running startup preflight..."
& $Python (Join-Path $ProjectRoot "scripts\preflight.py")
if ($LASTEXITCODE -ne 0) {
    throw "Startup preflight failed. No services were started."
}

function Start-PrototypeWindow {
    param(
        [Parameter(Mandatory = $true)][string]$Title,
        [Parameter(Mandatory = $true)][string]$Command
    )

    $escapedRoot = $ProjectRoot.Replace("'", "''")
    $escapedTitle = $Title.Replace("'", "''")
    $script = "`$Host.UI.RawUI.WindowTitle='$escapedTitle'; Set-Location '$escapedRoot'; $Command"
    $encoded = [Convert]::ToBase64String([Text.Encoding]::Unicode.GetBytes($script))
    Start-Process powershell -ArgumentList "-NoExit", "-ExecutionPolicy", "Bypass", "-EncodedCommand", $encoded
}

Start-PrototypeWindow -Title "A2A + MCP Agent Gateway :8004" -Command "& '$Python' -m uvicorn agent_gateway.server:app --host 127.0.0.1 --port 8004"
Start-Sleep -Seconds 2
Start-PrototypeWindow -Title "Repairer Portal :8000" -Command "& '$Python' -m uvicorn repairer_portal.app:app --host 127.0.0.1 --port 8000"

Write-Host "Started the dual-protocol agent gateway and authenticated repairer portal."
Write-Host "Open http://127.0.0.1:8000 and sign in with the prototype credentials."
