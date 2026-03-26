'use client';

import { useEffect, useState, useCallback } from 'react';

type Device = { id: string; ip: string; mac?: string; status: string; bandwidth_tx_bps?: number; bandwidth_rx_bps?: number; open_ports?: number[] };
type Alert = { id: string; title: string; message: string; severity: string; created_at?: string };

function getApiBase(): string {
  if (typeof window === 'undefined') return 'http://localhost:8000';
  return process.env.NEXT_PUBLIC_API_URL || `http://${window.location.hostname}:8000`;
}

function getWsBase(): string {
  const api = getApiBase();
  return api.replace(/^http/, 'ws');
}

export function useWebSocket(token: string | null) {
  const [devices, setDevices] = useState<Device[]>([]);
  const [alerts, setAlerts] = useState<Alert[]>([]);
  const [connected, setConnected] = useState(false);
  const [apiReachable, setApiReachable] = useState(false);

  const wsUrl = typeof window !== 'undefined'
    ? `${getWsBase()}/api/v1/ws${token ? `?token=${encodeURIComponent(token)}` : ''}`
    : '';

  // Fallback: ping API health to show "Live" if backend is reachable
  useEffect(() => {
    const check = () => {
      fetch(`${getApiBase()}/health`, { method: 'GET' })
        .then((r) => r.ok && setApiReachable(true))
        .catch(() => setApiReachable(false));
    };
    check();
    const id = setInterval(check, 10000);
    return () => clearInterval(id);
  }, []);

  useEffect(() => {
    if (!wsUrl) return;
    const ws = new WebSocket(wsUrl);
    ws.onopen = () => setConnected(true);
    ws.onclose = () => setConnected(false);
    ws.onerror = () => setConnected(false);
    ws.onmessage = (e) => {
      try {
        const msg = JSON.parse(e.data);
        if (msg.type === 'device') {
          setDevices((prev) => {
            const idx = prev.findIndex((d) => d.id === msg.payload.id);
            const next = [...prev];
            if (idx >= 0) next[idx] = { ...next[idx], ...msg.payload };
            else next.push(msg.payload);
            return next;
          });
        } else if (msg.type === 'alert') {
          setAlerts((prev) => [msg.payload, ...prev].slice(0, 50));
        }
      } catch {}
    };
    return () => ws.close();
  }, [wsUrl, token]);

  const fetchDevices = useCallback(async (t: string | null) => {
    if (!t) return;
    try {
      const res = await fetch(
        `${getApiBase()}/api/v1/devices`,
        { headers: { Authorization: `Bearer ${t}` } }
      );
      if (res.ok) {
        const data = await res.json();
        setDevices(data);
      }
    } catch {}
  }, []);

  const fetchAlerts = useCallback(async (t: string | null) => {
    if (!t) return;
    try {
      const res = await fetch(
        `${getApiBase()}/api/v1/alerts`,
        { headers: { Authorization: `Bearer ${t}` } }
      );
      if (res.ok) {
        const data = await res.json();
        setAlerts(data);
      }
    } catch {}
  }, []);

  useEffect(() => {
    if (token) {
      fetchDevices(token);
      fetchAlerts(token);
    }
  }, [token, fetchDevices, fetchAlerts]);

  const isLive = connected || apiReachable;
  return { devices, alerts, connected: isLive, refreshDevices: () => fetchDevices(token), refreshAlerts: () => fetchAlerts(token) };
}
