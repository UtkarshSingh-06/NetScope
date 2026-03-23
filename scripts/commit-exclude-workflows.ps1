# Commit all files except .github/workflows, one file per commit.
# Run from repo root.
$ErrorActionPreference = "Stop"
$repoRoot = Split-Path -Parent (Split-Path -Parent $MyInvocation.MyCommand.Path)
Set-Location $repoRoot

git config user.name "UtkarshSingh-06"
git config user.email "utkarsh.yash77@gmail.com"

$commits = @(
    @{ path = ".gitignore"; msg = "chore: extend gitignore for Python, Node, and build artifacts" },
    @{ path = "README.md"; msg = "docs: update README with AI platform features and quick start" },
    @{ path = "docker-compose.yml"; msg = "docker: add compose stack for backend, frontend, Prometheus, Grafana" },
    @{ path = "docs/architecture.md"; msg = "docs: add architecture overview and component diagram" },
    @{ path = "docs/api.md"; msg = "docs: add API reference for REST and WebSocket endpoints" },
    @{ path = "docs/deployment.md"; msg = "docs: add deployment guide for Docker and Kubernetes" },
    @{ path = "docs/optional-features.md"; msg = "docs: add optional features (trust scoring, replay, chatbot)" },
    @{ path = "agents/python_scanner/requirements.txt"; msg = "agents: add Python scanner dependencies" },
    @{ path = "agents/python_scanner/scanner/__init__.py"; msg = "agents: add scanner package init" },
    @{ path = "agents/python_scanner/scanner/device_tracker.py"; msg = "agents: add device discovery and bandwidth tracking" },
    @{ path = "agents/python_scanner/scanner/main.py"; msg = "agents: add scanner main loop and backend reporting" },
    @{ path = "agents/python_scanner/main.py"; msg = "agents: add scanner entry point" },
    @{ path = "agents/python_scanner/Dockerfile"; msg = "agents: add scanner Dockerfile" },
    @{ path = "backend/requirements.txt"; msg = "backend: add FastAPI and service dependencies" },
    @{ path = "backend/pyproject.toml"; msg = "backend: add pyproject for installable package" },
    @{ path = "backend/app/__init__.py"; msg = "backend: add app package and version" },
    @{ path = "backend/app/config.py"; msg = "backend: add Pydantic settings and configuration" },
    @{ path = "backend/app/core/__init__.py"; msg = "backend: add core package" },
    @{ path = "backend/app/core/security.py"; msg = "backend: add JWT auth and password hashing" },
    @{ path = "backend/app/core/deps.py"; msg = "backend: add FastAPI auth dependencies" },
    @{ path = "backend/app/schemas/__init__.py"; msg = "backend: add schemas package" },
    @{ path = "backend/app/schemas/common.py"; msg = "backend: add common schemas (Severity, Health, Token)" },
    @{ path = "backend/app/schemas/devices.py"; msg = "backend: add device and flow schemas" },
    @{ path = "backend/app/schemas/alerts.py"; msg = "backend: add alert schemas" },
    @{ path = "backend/app/api/__init__.py"; msg = "backend: add API package" },
    @{ path = "backend/app/api/v1/__init__.py"; msg = "backend: add API v1 package" },
    @{ path = "backend/app/api/v1/auth.py"; msg = "backend: add login and JWT endpoint" },
    @{ path = "backend/app/api/v1/agents.py"; msg = "backend: add agent registration endpoint" },
    @{ path = "backend/app/api/v1/devices.py"; msg = "backend: add devices CRUD API" },
    @{ path = "backend/app/api/v1/flows.py"; msg = "backend: add flows ingestion and list API" },
    @{ path = "backend/app/api/v1/alerts.py"; msg = "backend: add alerts API with ack support" },
    @{ path = "backend/app/api/v1/threat_intel.py"; msg = "backend: add threat intel lookup endpoint" },
    @{ path = "backend/app/api/v1/metrics.py"; msg = "backend: add Prometheus proxy metrics API" },
    @{ path = "backend/app/api/v1/ws.py"; msg = "backend: add WebSocket endpoint for real-time streaming" },
    @{ path = "backend/app/api/v1/router.py"; msg = "backend: add API v1 router aggregation" },
    @{ path = "backend/app/services/__init__.py"; msg = "backend: add services package" },
    @{ path = "backend/app/services/device_store.py"; msg = "backend: add in-memory device store" },
    @{ path = "backend/app/services/prometheus_client.py"; msg = "backend: add Prometheus HTTP API client" },
    @{ path = "backend/app/services/threat_intel.py"; msg = "backend: add AbuseIPDB, VirusTotal, Shodan integration" },
    @{ path = "backend/app/services/ids_engine.py"; msg = "backend: add IDS for port scan, ARP spoof, MITM" },
    @{ path = "backend/app/services/anomaly_detector.py"; msg = "backend: add Isolation Forest anomaly detection" },
    @{ path = "backend/app/services/alerting.py"; msg = "backend: add email, Slack, Discord alert delivery" },
    @{ path = "backend/app/services/auto_response.py"; msg = "backend: add auto-response IP blocking" },
    @{ path = "backend/app/services/flow_processor.py"; msg = "backend: add flow processor with IDS and anomaly pipeline" },
    @{ path = "backend/app/websocket/manager.py"; msg = "backend: add WebSocket connection manager" },
    @{ path = "backend/app/main.py"; msg = "backend: add FastAPI app with CORS and Prometheus" },
    @{ path = "backend/netscope_cli.py"; msg = "backend: add CLI for login, devices, alerts, threat lookup" },
    @{ path = "backend/Dockerfile"; msg = "backend: add Dockerfile for FastAPI service" },
    @{ path = "frontend/package.json"; msg = "frontend: add Next.js and chart dependencies" },
    @{ path = "frontend/next.config.js"; msg = "frontend: add Next.js config with API proxy" },
    @{ path = "frontend/postcss.config.js"; msg = "frontend: add PostCSS config" },
    @{ path = "frontend/tailwind.config.js"; msg = "frontend: add Tailwind theme and colors" },
    @{ path = "frontend/tsconfig.json"; msg = "frontend: add TypeScript config" },
    @{ path = "frontend/src/app/globals.css"; msg = "frontend: add global styles and Tailwind" },
    @{ path = "frontend/src/app/layout.tsx"; msg = "frontend: add root layout with fonts" },
    @{ path = "frontend/src/app/page.tsx"; msg = "frontend: add landing page" },
    @{ path = "frontend/src/app/login/page.tsx"; msg = "frontend: add login page" },
    @{ path = "frontend/src/app/dashboard/page.tsx"; msg = "frontend: add dashboard page" },
    @{ path = "frontend/src/app/alerts/page.tsx"; msg = "frontend: add alerts page" },
    @{ path = "frontend/src/lib/api.ts"; msg = "frontend: add API client and auth helpers" },
    @{ path = "frontend/src/lib/websocket.ts"; msg = "frontend: add WebSocket hook for live updates" },
    @{ path = "frontend/src/components/MetricCharts.tsx"; msg = "frontend: add throughput chart component" },
    @{ path = "frontend/src/components/DeviceTable.tsx"; msg = "frontend: add device table component" },
    @{ path = "frontend/src/components/AlertsPanel.tsx"; msg = "frontend: add alerts panel component" },
    @{ path = "frontend/src/components/NetworkGraph.tsx"; msg = "frontend: add network topology graph" },
    @{ path = "frontend/Dockerfile"; msg = "frontend: add multi-stage Dockerfile" },
    @{ path = "k8s/backend/deployment.yaml"; msg = "k8s: add backend deployment and service" },
    @{ path = "k8s/frontend/deployment.yaml"; msg = "k8s: add frontend deployment and service" }
)

$count = 0
foreach ($c in $commits) {
    $p = $c.path
    $m = $c.msg
    if (Test-Path $p) {
        git add $p
        $diff = git diff --cached --quiet 2>$null; $ec = $LASTEXITCODE
        if ($ec -ne 0) {
            git commit -m $m
            $count++
        }
    }
}

Write-Host "Done. $count commit(s) created."
Write-Host "Push: git push origin main"
