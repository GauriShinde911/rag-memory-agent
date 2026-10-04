# PowerShell script to run both backend and frontend for local development
$ErrorActionPreference = "Stop"

$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$rootDir = Split-Path -Parent $scriptDir

Write-Host "==========================================================" -ForegroundColor Cyan
Write-Host "   RAG Memory Agent - Development Server Launcher        " -ForegroundColor Cyan
Write-Host "==========================================================" -ForegroundColor Cyan

# 1. Start Backend in a background job or terminal
Write-Host "[1/2] Launching Backend on http://127.0.0.1:8000..." -ForegroundColor Green
$backendProcess = Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd '$rootDir'; uvicorn backend.app.main:app --host 127.0.0.1 --port 8000 --reload" -PassThru

# 2. Start Frontend
Write-Host "[2/2] Launching Frontend on http://localhost:5173..." -ForegroundColor Green
Set-Location -Path "$rootDir/frontend"
npm run dev

# Cleanup when frontend is closed
if ($backendProcess -and -not $backendProcess.HasExited) {
    Stop-Process -Id $backendProcess.Id -Force
}
