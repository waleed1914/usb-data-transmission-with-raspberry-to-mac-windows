@echo off
title PiDrop Transfer Status
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%~dp0show_status.ps1"
