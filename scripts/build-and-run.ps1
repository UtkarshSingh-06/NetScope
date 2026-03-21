# Build NetScope image and run the agent once (downloads all requirements via Docker).
# Prerequisite: Docker Desktop must be running.
# Run from repo root: .\scripts\build-and-run.ps1

$ErrorActionPreference = "Stop"
$RepoRoot = Split-Path -Parent (Split-Path -Parent $PSScriptRoot)
Set-Location $RepoRoot

Write-Host "[*] Building Docker image (eBPF + Go agent)..."
docker build -t network-observability/agent:latest .

if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

Write-Host "[*] Running agent once (metrics on :9090, requires Linux capabilities for eBPF)..."
Write-Host "    On Windows, eBPF will not attach (Linux kernel only); agent may still start and expose /metrics."
docker run --rm -p 9090:9090 network-observability/agent:latest
