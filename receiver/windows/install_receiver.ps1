#Requires -RunAsAdministrator
$ErrorActionPreference = "Stop"
$Folder = Join-Path $env:PUBLIC "PiDrop"
$ShareName = "PiDrop"
$InstallFolder = Join-Path $env:ProgramData "PiDropReceiver"

New-Item -ItemType Directory -Force -Path $Folder | Out-Null
New-Item -ItemType Directory -Force -Path $InstallFolder | Out-Null
if (-not (Get-SmbShare -Name $ShareName -ErrorAction SilentlyContinue)) {
    New-SmbShare -Name $ShareName -Path $Folder -ChangeAccess "$env:COMPUTERNAME\$env:USERNAME" | Out-Null
}

$startup = [Environment]::GetFolderPath("CommonStartup")
$readyScript = Join-Path $startup "PiDrop-Ready.cmd"
@"
@echo off
if not exist "$Folder" mkdir "$Folder"
"@ | Set-Content -Encoding ASCII -Path $readyScript

Copy-Item -Force (Join-Path $PSScriptRoot "show_status.ps1") $InstallFolder
Copy-Item -Force (Join-Path $PSScriptRoot "show_status.cmd") $InstallFolder

$desktopStatus = Join-Path ([Environment]::GetFolderPath("Desktop")) "PiDrop Status.cmd"
@"
@echo off
title PiDrop Transfer Status
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "$InstallFolder\show_status.ps1"
"@ | Set-Content -Encoding ASCII -Path $desktopStatus

Write-Host "Ready. SMB destination: \\$env:COMPUTERNAME\$ShareName"
Write-Host "Use Windows account '$env:USERNAME' and its password in the Pi config."
Write-Host "If the Pi cannot connect, allow File and Printer Sharing through Windows Firewall."
Write-Host "Open 'PiDrop Status' from the desktop at any time to see live progress."
