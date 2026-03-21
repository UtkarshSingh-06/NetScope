#!/usr/bin/env bash
# Build eBPF object and Go agent. Run from repo root.
# Requires: clang, libbpf headers, go, and (for full image) docker.

set -e
REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$REPO_ROOT"

echo "[*] Building eBPF object..."
make -C ebpf clean
make -C ebpf
cp ebpf/tcp_observability.o agent/ 2>/dev/null || true

echo "[*] Building Go agent..."
mkdir -p "$REPO_ROOT/bin"
cd agent
go mod tidy
CGO_ENABLED=0 GOOS=linux go build -ldflags="-s -w" -o "$REPO_ROOT/bin/network-observability-agent" .
cd "$REPO_ROOT"
echo "[*] Binary: bin/network-observability-agent"

echo "[*] To build Docker image (Linux): docker build -t network-observability/agent:latest ."
