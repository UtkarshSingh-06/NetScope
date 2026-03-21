# NetScope: Create multiple commits (one per file) and push to GitHub.
# Run from repo root: .\scripts\git-multi-commit.ps1
# Requires: git, and GitHub auth (HTTPS or SSH) for push.

$ErrorActionPreference = "Stop"
$repoRoot = Split-Path -Parent (Split-Path -Parent $MyInvocation.MyCommand.Path)
Set-Location $repoRoot

if (-not (Test-Path ".git")) {
    git init
}
git config user.name "UtkarshSingh-06"
git config user.email "utkarsh.yash77@gmail.com"
$remotes = @(git remote 2>$null)
if ($remotes -notcontains "origin") {
    git remote add origin https://github.com/UtkarshSingh-06/NetScope.git
}

$commits = @(
    @{ path = ".gitignore"; msg = "chore: add .gitignore to exclude binaries, secrets, and IDE files" },
    @{ path = "agent/go.mod"; msg = "agent: add Go module (netscope) and dependencies" },
    @{ path = "ebpf/headers/vmlinux.h"; msg = "ebpf: add minimal vmlinux types for CO-RE compatibility" },
    @{ path = "ebpf/Makefile"; msg = "ebpf: add Makefile for building eBPF object with clang and libbpf" },
    @{ path = "ebpf/tcp_observability.c"; msg = "ebpf: add TCP observability programs (kprobes, maps, ring buffer)" },
    @{ path = "agent/main.go"; msg = "agent: add main entrypoint, eBPF load, metrics server, and health endpoints" },
    @{ path = "agent/ebpfimpl/loader.go"; msg = "agent: add eBPF loader, kprobe attach, and map/ringbuf reader" },
    @{ path = "agent/metrics/collector.go"; msg = "agent: add Prometheus collector with optional K8s enrichment" },
    @{ path = "agent/k8s/resolver.go"; msg = "agent: add Kubernetes IP-to-pod/namespace/service resolver" },
    @{ path = "k8s/namespace.yaml"; msg = "k8s: add namespace for NetScope agent" },
    @{ path = "k8s/rbac.yaml"; msg = "k8s: add RBAC (ServiceAccount, ClusterRole, ClusterRoleBinding)" },
    @{ path = "k8s/daemonset.yaml"; msg = "k8s: add DaemonSet for node-level eBPF agent" },
    @{ path = "k8s/service.yaml"; msg = "k8s: add Service for agent metrics discovery" },
    @{ path = "k8s/servicemonitor.yaml"; msg = "k8s: add ServiceMonitor for Prometheus Operator" },
    @{ path = "k8s/configmap-ebpf.yaml"; msg = "k8s: add optional ConfigMap template for eBPF object" },
    @{ path = "prometheus/prometheus.yaml"; msg = "prometheus: add scrape config for NetScope agents" },
    @{ path = "prometheus/alerts.yaml"; msg = "prometheus: add alert rules for retransmissions and drops" },
    @{ path = "dashboards/network-observability.json"; msg = "dashboards: add Grafana dashboard for TCP metrics" },
    @{ path = "scripts/build.sh"; msg = "scripts: add build script for eBPF and Go agent" },
    @{ path = "scripts/deploy.sh"; msg = "scripts: add deploy script for Kubernetes" },
    @{ path = "scripts/rewrite-authors.sh"; msg = "scripts: add shell script to rewrite Git author history" },
    @{ path = "scripts/rewrite-authors.ps1"; msg = "scripts: add PowerShell script to rewrite Git authors" },
    @{ path = "scripts/git-multi-commit.ps1"; msg = "scripts: add PowerShell helper for staged per-file commits and push" },
    @{ path = "scripts/build-and-run.ps1"; msg = "scripts: add PowerShell build-and-run for one-shot Docker build and run" },
    @{ path = "Dockerfile"; msg = "build: add multi-stage Dockerfile with go mod tidy for dependency fetch" },
    @{ path = "README.md"; msg = "docs: add NetScope README with architecture, setup, and resume content" }
)

$count = 0
foreach ($c in $commits) {
    $p = $c.path
    $m = $c.msg
    if (Test-Path $p) {
        git add $p
        git diff --cached --quiet
        if ($LASTEXITCODE -ne 0) {
            git commit -m $m
            $count++
        }
    }
}

git branch -M main
Write-Host "Done. $count commit(s) created on branch 'main'."
Write-Host "Push to GitHub (use a terminal where you can enter credentials): git push -u origin main"
