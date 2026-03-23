# NetScope API Reference

Base URL: `http://localhost:8000`

## Authentication

JWT Bearer token. Obtain via:

```bash
curl -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"admin"}'
```

Response:
```json
{"access_token":"...","token_type":"bearer","expires_in":3600}
```

Use in requests:
```
Authorization: Bearer <token>
```

## Endpoints

### Health
- `GET /health` - Health check (no auth)

### Auth
- `POST /api/v1/auth/login` - Login (returns JWT)

### Devices
- `GET /api/v1/devices` - List devices
- `GET /api/v1/devices/{id}` - Get device
- `POST /api/v1/devices` - Register/update device (from agent)

### Flows
- `GET /api/v1/flows` - List recent flows
- `POST /api/v1/flows/batch` - Ingest flow batch (from agent)

### Alerts
- `GET /api/v1/alerts` - List alerts (?severity=, ?limit=)
- `POST /api/v1/alerts` - Create alert
- `PATCH /api/v1/alerts/{id}/ack` - Acknowledge alert

### Threat Intel
- `GET /api/v1/threat-intel/lookup/{ip}` - Lookup IP (AbuseIPDB, VirusTotal, Shodan)

### Metrics
- `GET /api/v1/metrics/connections` - Connection metrics from Prometheus
- `GET /api/v1/metrics/query?expr=<promql>` - PromQL query
- `GET /api/v1/metrics/query_range?expr=&start=&end=&step=` - Range query

### WebSocket
- `WS /api/v1/ws` - Real-time stream (devices, flows, alerts, metrics)

## OpenAPI

Interactive docs: `http://localhost:8000/docs`
