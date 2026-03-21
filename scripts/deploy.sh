#!/usr/bin/env bash
# Deploy network-observability to a Kubernetes cluster.
# Prerequisites: kubectl, cluster with Linux nodes.

set -e
REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$REPO_ROOT/k8s"

echo "[*] Creating namespace and RBAC..."
kubectl apply -f namespace.yaml
kubectl apply -f rbac.yaml

echo "[*] Deploying agent DaemonSet and Service..."
kubectl apply -f service.yaml
kubectl apply -f daemonset.yaml

echo "[*] Optional: ServiceMonitor (Prometheus Operator)"
echo "    kubectl apply -f servicemonitor.yaml"

kubectl -n network-observability get pods -l app=network-observability-agent -o wide
