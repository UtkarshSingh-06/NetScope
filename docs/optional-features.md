# Optional Features

## Device Trust Scoring

Devices can be assigned a `trust_score` (0–100) based on:
- Historical behavior (no anomalies over time)
- Threat intel lookups (low risk → higher trust)
- Known internal IP ranges vs external
- Integration with identity providers (future)

The backend `DeviceStore` supports `update_trust(device_id, score)`.

## Timeline Replay

Replay historical flow data for forensics:
- Store flow snapshots with timestamps in a time-series DB (e.g. TimescaleDB, InfluxDB)
- API endpoint: `GET /api/v1/flows/replay?start=&end=&speed=1` streaming events at configurable speed
- Frontend: timeline slider + play/pause for replay visualization

## AI Chatbot Interface

Optional conversational interface for:
- "Show alerts in the last hour"
- "What's the risk score for 192.168.1.5?"
- "Block IP 10.0.0.42"

Implementation: Add `/api/v1/chat` endpoint that parses natural language (e.g. via LLM or rule-based) and invokes the appropriate API, returning structured results.
