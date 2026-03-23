# NetScope Architecture

## Overview

NetScope is an AI-powered network observability and security platform with a distributed architecture.

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           NetScope Platform                                  │
├─────────────────────────────────────────────────────────────────────────────┤
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐    │
│  │   Next.js    │  │   FastAPI    │  │ Prometheus   │  │   Grafana    │    │
│  │  Dashboard   │  │   Backend    │  │              │  │              │    │
│  │  (React)     │  │  (REST+WS)   │  │   Metrics    │  │  Dashboards  │    │
│  └──────┬───────┘  └──────┬───────┘  └──────▲───────┘  └──────▲───────┘    │
│         │                 │                 │                 │             │
│         │    WebSocket    │    Scrape       │                 │             │
│         └─────────────────┼─────────────────┘                 │             │
│                           │                                   │             │
│  ┌────────────────────────┼───────────────────────────────────┼─────────┐   │
│  │  Backend Services      │                                   │         │   │
│  │  • JWT Auth            │  • Threat Intel (AbuseIPDB,       │         │   │
│  │  • Device Store        │    VirusTotal, Shodan)            │         │   │
│  │  • Alerting            │  • IDS (port scan, ARP spoof,     │         │   │
│  │  • Anomaly (ML)        │    MITM)                          │         │   │
│  │  • Auto-response       │  • Prometheus client              │         │   │
│  └────────────────────────┼───────────────────────────────────┴─────────┘   │
│                           ▲                                                 │
│  ┌────────────────────────┼─────────────────────────────────────────────┐   │
│  │  Agents                │                                             │   │
│  │  • Go eBPF agent       │  (DaemonSet, one per node)                   │   │
│  │  • Python scanner      │  (device discovery, optional)                │   │
│  └────────────────────────┴─────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────────────────┘
```

## Components

| Component | Tech | Role |
|-----------|------|------|
| **eBPF** | C, libbpf | Kernel-level TCP hooks (RTT, retrans, drops) |
| **Go Agent** | Go, cilium/ebpf | Load eBPF, collect metrics, expose Prometheus |
| **Backend** | FastAPI, Python | REST API, WebSocket, threat intel, IDS, alerting, ML |
| **Frontend** | Next.js, React | Dashboard, charts, network graph, alerts |
| **Python Agent** | Python | Device discovery, bandwidth, optional scanner |

## Data Flow

1. **eBPF → Go Agent**: Kernel maps and ring buffer stream TCP metrics to userspace.
2. **Go Agent → Prometheus**: Agent exposes `/metrics`; Prometheus scrapes every 15s.
3. **Prometheus → Backend**: Backend queries Prometheus API for charts and aggregation.
4. **Agents → Backend**: Python scanner and (optionally) Go agent push devices/flows to backend.
5. **Backend → Frontend**: REST API and WebSocket stream real-time updates to the dashboard.

## Deployment

- **Docker Compose**: Local dev and single-node deployment.
- **Kubernetes**: DaemonSet for Go agent, Deployments for backend and frontend.
- **Cloud**: Compatible with AWS EKS, GCP GKE, and other managed K8s.
