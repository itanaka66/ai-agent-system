<#
.SYNOPSIS
  Select which Docker services to start for this project (Windows PowerShell).

.DESCRIPTION
  Picks which services to start - this project's own backend and/or web UI
  (independently selectable), and/or its optional backing services (Qdrant,
  PostgreSQL, Ollama, Flowise) - via CLI switches or an interactive prompt,
  then starts them with `docker compose` using matching Compose profiles.
  Requires Docker Desktop (with the Compose plugin, included by default) to
  be installed and running.

.EXAMPLE
  .\install.ps1 -All

.EXAMPLE
  .\install.ps1 -Qdrant -Postgres

.EXAMPLE
  .\install.ps1 -WebUI
  # Just the web UI - see README "Installing just the Web UI".

.EXAMPLE
  .\install.ps1
  # No switches: interactive yes/no prompt per service.
#>
[CmdletBinding()]
param(
    [switch]$Orchestrator,
    [switch]$WebUI,
    [switch]$App,
    [switch]$Qdrant,
    [switch]$Postgres,
    [switch]$Ollama,
    [switch]$Flowise,
    [switch]$All,
    [switch]$Help
)

$ErrorActionPreference = "Stop"
Set-Location -Path $PSScriptRoot

$AllServices = @("orchestrator", "webui", "qdrant", "postgres", "ollama", "flowise")

function Show-Usage {
    Write-Host @"
Usage: .\install.ps1 [-Orchestrator] [-WebUI] [-App] [-Qdrant] [-Postgres] [-Ollama] [-Flowise] [-All]

Selects which services to start via docker compose profiles. Run with no
switches for an interactive yes/no prompt per service.

  -Orchestrator  This project's own backend API (built locally)
  -WebUI         This project's own web UI / Agent Console (built locally)
  -App           Shorthand for -Orchestrator -WebUI together
  -Qdrant        Vector database (RAG / conversation memory)
  -Postgres      PostgreSQL (chat/session logs)
  -Ollama        Local Ollama server (LLM inference)
  -Flowise       Flowise (visual workflow designer)
  -All           Start every service above (recommended for a first try)
  -Help          Show this help

First time on Windows? Run: .\install.ps1 -All
Only want the web UI (e.g. backend runs elsewhere)? Run: .\install.ps1 -WebUI
"@
}

if ($Help) {
    Show-Usage
    exit 0
}

$explicitSwitches = @($Orchestrator, $WebUI, $App, $Qdrant, $Postgres, $Ollama, $Flowise, $All) -contains $true
$services = [System.Collections.Generic.List[string]]::new()

if ($explicitSwitches) {
    if ($All) {
        $services.AddRange([string[]]$AllServices)
    }
    else {
        if ($App) { $services.Add("orchestrator"); $services.Add("webui") }
        if ($Orchestrator) { $services.Add("orchestrator") }
        if ($WebUI) { $services.Add("webui") }
        if ($Qdrant) { $services.Add("qdrant") }
        if ($Postgres) { $services.Add("postgres") }
        if ($Ollama) { $services.Add("ollama") }
        if ($Flowise) { $services.Add("flowise") }
    }
}
else {
    Write-Host "起動するサービスを選択してください / Select services to start:"
    foreach ($svc in $AllServices) {
        $answer = Read-Host "  $svc を起動しますか？ [y/N]"
        if ($answer -match '^[yY]') {
            $services.Add($svc)
        }
    }
}

if ($services.Count -eq 0) {
    Write-Host "サービスが選択されませんでした。終了します。 / No services selected, exiting."
    exit 0
}

# De-duplicate (e.g. -App -WebUI would otherwise list "webui" twice)
$services = [System.Collections.Generic.List[string]]($services | Select-Object -Unique)

if (-not (Test-Path ".env")) {
    if (($services.Contains("orchestrator") -or $services.Contains("webui")) -and (Test-Path ".env.docker.example")) {
        Write-Host ".env が見つからないため .env.docker.example からコピーします / .env not found, copying from .env.docker.example"
        Copy-Item ".env.docker.example" ".env"
    }
    else {
        Write-Host ".env が見つからないため .env.example からコピーします / .env not found, copying from .env.example"
        Copy-Item ".env.example" ".env"
    }
}

Write-Host "起動するサービス / Starting services: $($services -join ', ')"

$profileArgs = @()
foreach ($svc in $services) {
    $profileArgs += @("--profile", $svc)
}

docker compose @profileArgs up -d --build
if ($LASTEXITCODE -ne 0) {
    Write-Error "docker compose failed (exit code $LASTEXITCODE)"
    exit $LASTEXITCODE
}

Write-Host ""
Write-Host "起動完了。状態確認: docker compose ps"
Write-Host "Done. Check status with: docker compose ps"

if ($services.Contains("ollama")) {
    Write-Host "Ollama モデルの取得例 / pull the default models:"
    Write-Host "  docker compose exec ollama ollama pull llama3:8b"
    Write-Host "  docker compose exec ollama ollama pull phi3:mini"
}

if ($services.Contains("webui") -or $services.Contains("orchestrator")) {
    Write-Host ""
    if ($services.Contains("webui")) { Write-Host "Web UI: http://localhost:3000" }
    if ($services.Contains("orchestrator")) { Write-Host "API:    http://localhost:8000" }
}
