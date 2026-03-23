# NetScope Deployment

## Docker Compose (Local / Dev)

```bash
docker-compose up -d
```

Services:
- Backend: http://localhost:8000
- Frontend: http://localhost:3000
- Prometheus: http://localhost:9090
- Grafana: http://localhost:3001 (admin/admin)

Login: admin / admin

## Kubernetes

### Prerequisites
- Kubernetes cluster (EKS, GKE, or kind)
- Prometheus Operator (optional, for ServiceMonitor)

### Deploy

```bash
# Create namespace and RBAC
kubectl apply -f k8s/namespace.yaml
kubectl apply -f k8s/rbac.yaml

# Deploy eBPF agent (DaemonSet)
kubectl apply -f k8s/daemonset.yaml
kubectl apply -f k8s/service.yaml
kubectl apply -f k8s/configmap-ebpf.yaml  # if using ConfigMap for eBPF object

# Deploy backend and frontend
kubectl apply -f k8s/backend/
kubectl apply -f k8s/frontend/

# Prometheus (if not using Operator)
kubectl apply -f prometheus/
```

### Build Images

```bash
docker build -t netscope/backend:latest ./backend
docker build -t netscope/frontend:latest ./frontend
docker build -t network-observability/agent:latest .
```

## Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| JWT_SECRET_KEY | JWT signing key | (change in prod) |
| PROMETHEUS_URL | Prometheus base URL | http://localhost:9090 |
| ABUSEIPDB_API_KEY | AbuseIPDB API key | (optional) |
| VIRUSTOTAL_API_KEY | VirusTotal API key | (optional) |
| SHODAN_API_KEY | Shodan API key | (optional) |
| SLACK_WEBHOOK_URL | Slack alert webhook | (optional) |
| DISCORD_WEBHOOK_URL | Discord webhook | (optional) |
