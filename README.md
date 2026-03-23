# NetScope

**NetScope** is an **AI-powered network observability and security platform** combining kernel-level eBPF monitoring with a full-stack dashboard, threat intelligence, intrusion detection, and real-time alerting. Built with eBPF (C), Go, FastAPI, Next.js, Prometheus, and Grafana—scalable from single-node to distributed multi-agent deployments.

## Features

- **Real-time network monitoring** — Live device tracking (IP, MAC, bandwidth, ports) via WebSockets
- **AI anomaly detection** — Isolation Forest for device behavior profiling and anomaly scoring
- **Threat intelligence** — AbuseIPDB, VirusTotal, Shodan integration with composite risk scoring
- **IDS** — Port scan, ARP spoofing, MITM detection
- **Alerting** — Severity levels; email, Slack, Discord notifications
- **Auto-response** — Block suspicious IPs, terminate connections (Linux iptables)
- **Full-stack dashboard** — React/Next.js with charts, network graph, alerts panel
- **Backend APIs** — FastAPI with JWT auth, REST + WebSocket
- **Distributed architecture** — Multiple scanning agents, central server
- **Docker & Kubernetes** — Production-ready deployment

---

## Project Overview

This platform provides **east-west** (service-to-service) network visibility inside Kubernetes by attaching eBPF programs to TCP kernel hooks. It exports Prometheus metrics and optional Grafana dashboards, with optional enrichment of metrics by **pod**, **namespace**, and **service** using the Kubernetes API.

**Why eBPF?**  
eBPF runs in the kernel with minimal overhead, no need to modify applications or inject sidecars, and provides accurate per-connection metrics (RTT, retransmissions, bytes, drops) that traditional packet sniffing (tcpdump/Wireshark) would require post-processing to aggregate. It aligns with how products like **Datadog NPM**, **Cilium Hubble**, and **AWS VPC Flow Logs** (and similar) achieve observability without app changes.

---

## Architecture

```
┌─────────────────────────────────────────────────────────────────────────┐
│                         Kubernetes Cluster                               │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐                     │
│  │   Node A    │  │   Node B    │  │   Node C    │  ...                 │
│  │ ┌─────────┐ │  │ ┌─────────┐ │  │ ┌─────────┐ │                     │
│  │ │ eBPF    │ │  │ │ eBPF    │ │  │ │ eBPF    │ │  (DaemonSet: 1 pod   │
│  │ │ (kernel)│ │  │ │ (kernel)│ │  │ │ (kernel)│ │   per node)          │
│  │ └────┬────┘ │  │ └────┬────┘ │  │ └────┬────┘ │                     │
│  │      │      │  │      │      │  │      │      │                     │
│  │ ┌────▼────┐ │  │ ┌────▼────┐ │  │ ┌────▼────┐ │                     │
│  │ │ Agent   │ │  │ │ Agent   │ │  │ │ Agent   │ │                     │
│  │ │ (Go)    │◄┼──┼─┤ /metrics│ │  │ │ /metrics│ │                     │
│  │ └────┬────┘ │  │ └────┬────┘ │  │ └────┬────┘ │                     │
│  └──────┼──────┘  └──────┼──────┘  └──────┼──────┘                     │
│         │                 │                 │                            │
│         └─────────────────┼─────────────────┘                            │
│                           │ scrape                                       │
│                    ┌──────▼──────┐      ┌─────────────┐                   │
│                    │ Prometheus  │─────►│  Grafana    │                   │
│                    └─────────────┘      └─────────────┘                   │
└─────────────────────────────────────────────────────────────────────────┘
```

### 1. Kernel Layer (eBPF)

- **Programs** attach to:
  - `tcp_sendmsg` — bytes sent
  - `tcp_cleanup_rbuf` — bytes received (application read)
  - `tcp_retransmit_skb` — retransmissions
  - `tcp_ack` — RTT sampling (srtt_us from tcp_sock)
  - `kfree_skb` — packet drops (TCP sockets)
  - `tcp_connect` — connection open events
- **Maps:**
  - **Hash map** `conn_stats_map`: flow key (5-tuple + netns) → per-connection metrics (bytes, retrans, RTT sum/count, drops).
  - **Ring buffer** `events_ringbuf`: real-time events (retrans, drop, connect) for optional userspace processing.
- **Design:** Kernel-side aggregation reduces userspace load; ring buffer provides low-latency events when needed.

### 2. Userspace Agent (Go)

- Loads the compiled eBPF object, attaches kprobes, and iterates the connection-stats map on a configurable interval.
- Optionally resolves IPs to **pod / namespace / service** via the Kubernetes API (list/watch pods and services for the node).
- Exposes **Prometheus** metrics at `GET /metrics` and health at `/health` and `/ready`.

### 3. Kubernetes Integration

- **DaemonSet:** One agent pod per node; each pod loads eBPF on its host (hostNetwork, privileged or CAP_BPF/CAP_PERFMON).
- **RBAC:** ServiceAccount with least-privilege (list/watch pods, services) for enrichment.
- **ServiceMonitor** (optional): For Prometheus Operator to auto-discover scrape targets.

### 4. Observability Stack

- **Prometheus:** Scrapes each agent’s `/metrics` (see `prometheus/prometheus.yaml`).
- **Grafana:** Pre-built dashboard in `dashboards/network-observability.json` (latency, retransmissions, throughput, drops, node health).
- **Alerts:** Example rules in `prometheus/alerts.yaml` (retransmission rate, packet loss, agent down).

---

## Repository Structure

```
NetScope/
├── backend/                 # FastAPI application
│   ├── app/
│   │   ├── api/v1/          # REST + WebSocket endpoints
│   │   ├── services/        # Threat intel, IDS, alerting, anomaly, Prometheus
│   │   ├── websocket/       # Real-time streaming
│   │   └── core/            # Auth, config
│   ├── netscope_cli.py      # CLI (devices, alerts, threat lookup)
│   └── requirements.txt
├── frontend/                # Next.js dashboard
│   ├── src/app/             # Pages (dashboard, alerts, login)
│   └── src/components/      # Charts, device table, network graph
├── agents/
│   └── python_scanner/      # Device discovery, bandwidth, flow collection
├── ebpf/                    # Kernel eBPF programs (C)
├── agent/                   # Go eBPF userspace agent
├── k8s/                     # Kubernetes manifests (agent, backend, frontend)
├── docs/                    # Architecture, API, deployment
├── .github/workflows/       # CI (backend, agent, eBPF, frontend)
├── docker-compose.yml       # Full stack (backend, frontend, Prometheus, Grafana)
└── README.md
```

## Quick Start

```bash
# Docker Compose (recommended)
docker-compose up -d

# Backend: http://localhost:8000  |  Frontend: http://localhost:3000
# Login: admin / admin
```

```bash
# CLI (from backend directory)
cd backend && pip install -e .
netscope login  # Get token, then:
export NETSCOPE_TOKEN=<your-token>
netscope devices
netscope threat-lookup 8.8.8.8
```

---

## Metrics Exposed

| Metric | Type | Description |
|--------|------|-------------|
| `network_observability_tcp_bytes_sent_total` | Counter | Bytes sent per connection (from tcp_sendmsg). |
| `network_observability_tcp_bytes_recv_total` | Counter | Bytes received per connection (from tcp_cleanup_rbuf). |
| `network_observability_tcp_retransmissions_total` | Counter | TCP retransmissions per connection. |
| `network_observability_tcp_rtt_avg_nanoseconds` | Gauge | Average RTT (ns) per connection. |
| `network_observability_tcp_rtt_samples_total` | Counter | Number of RTT samples. |
| `network_observability_tcp_drops_total` | Counter | Packet drops (kfree_skb) per connection. |
| `network_observability_events_retrans_total` | Counter | Retrans events from ring buffer (per node). |
| `network_observability_events_drops_total` | Counter | Drop events from ring buffer (per node). |

Labels (when K8s enrichment is on): `node`, `src_ip`, `dst_ip`, `src_port`, `dst_port`, `src_pod`, `src_namespace`, `src_svc`, `dst_pod`, `dst_namespace`, `dst_svc`.

---

## Setup & Deployment

### Prerequisites

- **Linux** kernel 5.4+ (for ring buffer and kprobes); 5.10+ recommended.
- **Build:** clang, llvm, libbpf headers, kernel headers (e.g. `linux-headers-$(uname -r)`), Go 1.21+.
- **Run:** Root or CAP_BPF, CAP_PERFMON, CAP_NET_ADMIN (or privileged container).
- **Kubernetes:** Linux nodes; optional Prometheus/Grafana.

### Build

```bash
# From repo root (Linux recommended for eBPF)
./scripts/build.sh
# Binary: bin/network-observability-agent
```

**Docker image (build on Linux so eBPF compiles):**

```bash
docker build -t network-observability/agent:latest .
```

If eBPF cannot be built in Docker (e.g. missing kernel headers), build the `.o` on a host with matching kernel, copy `ebpf/tcp_observability.o` into the image or mount it via ConfigMap/host path (see `k8s/daemonset.yaml` and `k8s/configmap-ebpf.yaml`).

### Deploy to Kubernetes

```bash
# Build and push image (replace registry as needed)
docker build -t <registry>/network-observability/agent:latest .
docker push <registry>/network-observability/agent:latest

# Update k8s/daemonset.yaml image, then:
./scripts/deploy.sh
```

Or apply manually:

```bash
kubectl apply -f k8s/namespace.yaml
kubectl apply -f k8s/rbac.yaml
kubectl apply -f k8s/service.yaml
kubectl apply -f k8s/daemonset.yaml
```

Ensure the DaemonSet has access to the eBPF object. **Option A:** Build the Docker image on Linux so the eBPF object is embedded; then remove the `volumes` and `volumeMounts` for `ebpf-object` from `k8s/daemonset.yaml` so the container uses the in-image path. **Option B:** Build the `.o` on a node, create a ConfigMap with it (`kubectl create configmap network-observability-ebpf -n network-observability --from-file=tcp_observability.o=ebpf/tcp_observability.o`), and keep the volume mount so the agent loads from the ConfigMap.

### Prometheus

- **Standalone:** Use `prometheus/prometheus.yaml` (or merge its `scrape_configs` into your config).
- **Prometheus Operator:** `kubectl apply -f k8s/servicemonitor.yaml` (adjust `release` label if needed).

### Grafana

- Add Prometheus as a datasource.
- Import `dashboards/network-observability.json` (set the Prometheus datasource variable).

---

## Production Practices

- **Error handling:** Agent logs load/attach failures and degrades gracefully if K8s API is unavailable (metrics without pod/ns/svc labels).
- **Resource limits:** DaemonSet specifies requests/limits (e.g. 50m–500m CPU, 64Mi–256Mi memory).
- **Security:** RBAC limits agent to list/watch pods and services; run with least privilege possible (e.g. CAP_BPF/CAP_PERFMON instead of full privileged if your cluster allows).
- **Performance:** Kernel aggregation in hash map and ring buffer; poll interval (e.g. 15s) configurable to balance freshness vs. CPU.

---

## Troubleshooting

| Issue | Check |
|-------|--------|
| Agent won’t start / eBPF load fails | Object path correct? Run on Linux with sufficient capabilities (privileged or CAP_BPF, CAP_PERFMON, etc.). |
| No metrics | eBPF attached? Check `/ready`. Ensure kernel supports kprobes and required helpers (e.g. `bpf_probe_read_kernel`). |
| No K8s labels | K8s API reachable? RBAC and ServiceAccount correct? `--enable-kubernetes=true` and NODE_NAME set. |
| RTT always 0 | Some kernels store `srtt_us` at a different offset; build with BTF vmlinux or adjust offset in `tcp_observability.c` for your kernel. |
| High CPU | Increase `--poll-interval`; reduce map size or event rate if needed. |

---

## Comparison with Packet Sniffing (tcpdump / Wireshark)

| Aspect | This platform (eBPF) | tcpdump / Wireshark |
|--------|----------------------|----------------------|
| Overhead | Low; kernel aggregation, no full packet copy to userspace by default. | High; can capture every packet, large storage and CPU. |
| Metrics | Direct counters/gauges (RTT, retrans, bytes, drops) per connection. | Raw packets; need post-processing for aggregates. |
| App changes | None. | None. |
| K8s integration | Native (DaemonSet, pod/ns/svc enrichment). | Manual; correlate IPs with K8s API yourself. |
| Use case | Continuous observability, SLOs, alerting. | Ad-hoc debugging, deep packet inspection. |

---

## Future Improvements

- IPv6 support in eBPF and agent.
- Optional OpenTelemetry export (metrics/traces).
- Service mesh awareness (e.g. Istio/Linkerd labels).
- Latency SLO tracking and anomaly detection.
- Multi-cluster aggregation (federation or central Prometheus).

---

## Resume & Interview Talking Points

**Resume bullets (4–5):**

- Designed and implemented a **cloud-native network observability platform** using **eBPF** (C) and **Go**, providing TCP RTT, retransmissions, packet drops, and throughput metrics with **zero application code changes**.
- Deployed as a **Kubernetes DaemonSet** with **RBAC**, **Prometheus** scraping, and **Grafana** dashboards; enriched metrics with **pod/namespace/service** via the Kubernetes API for east-west traffic visibility.
- Built **kernel-level** instrumentation with **BPF maps** (hash, ring buffer) and **kprobes** on TCP hooks (`tcp_sendmsg`, `tcp_retransmit_skb`, `tcp_ack`, `kfree_skb`), following production patterns used by vendors like Datadog and Cilium.
- Implemented **Prometheus exporters**, **alerting rules**, and **resource limits**; applied **least-privilege** and security best practices for in-cluster deployment.
- Delivered **end-to-end observability** (eBPF → Go agent → Prometheus → Grafana) with documentation, build/deploy scripts, and troubleshooting guidance for production-style operations.

**Technologies:** Linux kernel networking, eBPF (C), Go, Kubernetes (DaemonSet, RBAC), Prometheus, Grafana, Docker, (optional) OpenTelemetry.

**Interview topics:** Why eBPF over iptables or packet capture; tradeoffs of kernel vs userspace aggregation; how you’d add IPv6 or service mesh labels; how you’d scale to many nodes or multiple clusters.

---

## Repository maintenance

**Removing other contributors from the GitHub contributors list**

GitHub shows anyone in **Co-authored-by** or as author/committer. To show only you:

1. **In Git Bash** (or WSL) from the repo root, run (this strips `Co-authored-by` lines and sets you as author/committer):

```bash
git filter-branch -f --msg-filter 'sed -e "/^Co-authored-by:/d"' --env-filter '
  export GIT_AUTHOR_NAME="Utkarsh Singh"
  export GIT_AUTHOR_EMAIL="utkarsh.yash77@gmail.com"
  export GIT_COMMITTER_NAME="Utkarsh Singh"
  export GIT_COMMITTER_EMAIL="utkarsh.yash77@gmail.com"
' --tag-name-filter cat -- --all
```

2. **Force-push** so GitHub recalculates contributors:

```bash
git push --force origin main
```

Use your own name/email if different. After the force-push, only you will appear under Contributors.

---

## License

Apache-2.0.
