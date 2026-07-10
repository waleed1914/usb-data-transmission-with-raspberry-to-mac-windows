$StatusFile = Join-Path $env:PUBLIC "PiDrop\.pi_transfer_status.json"
$HeartbeatFile = Join-Path $env:PUBLIC "PiDrop\.pi_heartbeat"

while ($true) {
    Clear-Host
    Write-Host "PiDrop receiver - live status" -ForegroundColor Cyan
    Write-Host "Closing this window does NOT stop receiving files."
    Write-Host ""

    $piConnected = $false
    $statusFresh = $false
    if (Test-Path $HeartbeatFile) {
        $age = (Get-Date) - (Get-Item $HeartbeatFile).LastWriteTime
        $piConnected = $age.TotalSeconds -le 30
    }
    if (Test-Path $StatusFile) {
        $statusAge = (Get-Date) - (Get-Item $StatusFile).LastWriteTime
        $statusFresh = $statusAge.TotalSeconds -le 30
    }
    if ($statusFresh) {
        $piConnected = $true
    }
    if ($piConnected) {
        Write-Host "Raspberry Pi: CONNECTED" -ForegroundColor Green
    } else {
        Write-Host "Raspberry Pi: DISCONNECTED" -ForegroundColor Red
    }
    Write-Host ""

    if (Test-Path $StatusFile) {
        try {
            $s = Get-Content -Raw $StatusFile | ConvertFrom-Json
            $sent = "{0:N2} GB" -f ($s.sent_bytes / 1GB)
            $left = "{0:N2} GB" -f ($s.remaining_bytes / 1GB)
            Write-Host "Status:    $($s.state)"
            Write-Host "Receiver:  $($s.receiver)"
            Write-Host "File:      $($s.filename)"
            Write-Host "Progress:  $($s.percent)%"
            Write-Host "Received:  $sent"
            Write-Host "Remaining: $left"
            Write-Host "Updated:   $($s.updated)"
        } catch {
            Write-Host "Status is being updated. Retrying..." -ForegroundColor Yellow
        }
    } else {
        Write-Host "Waiting for the Raspberry Pi to start a transfer..." -ForegroundColor Yellow
    }

    Write-Host ""
    Write-Host "Press Ctrl+C or close this window to hide status."
    Start-Sleep -Seconds 2
}
