$ErrorActionPreference = "SilentlyContinue"
$Ports = 8000, 8004
$Stopped = @()

foreach ($Port in $Ports) {
    $Connections = Get-NetTCPConnection -LocalPort $Port -State Listen
    foreach ($Connection in $Connections) {
        if ($Connection.OwningProcess -and $Stopped -notcontains $Connection.OwningProcess) {
            Stop-Process -Id $Connection.OwningProcess -Force
            $Stopped += $Connection.OwningProcess
            Write-Host "Stopped PID $($Connection.OwningProcess) listening on port $Port."
        }
    }
}

if ($Stopped.Count -eq 0) {
    Write-Host "No listening processes were found on ports 8000 or 8004."
}
