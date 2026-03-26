'use client';

import { useEffect, useState } from 'react';
import { MetricCharts } from '@/components/MetricCharts';
import { DeviceTable } from '@/components/DeviceTable';
import { AlertsPanel } from '@/components/AlertsPanel';
import { NetworkGraph } from '@/components/NetworkGraph';
import { useWebSocket } from '@/lib/websocket';

export default function Dashboard() {
  const [token, setToken] = useState<string | null>(null);
  const { devices, alerts, connected } = useWebSocket(token);

  useEffect(() => {
    const t = localStorage.getItem('netscope_token');
    if (t) setToken(t);
  }, []);

  return (
    <div className="min-h-screen p-6">
      <header className="flex justify-between items-center mb-8">
        <h1 className="text-2xl font-display font-bold text-net-400">NetScope Dashboard</h1>
        <div className="flex items-center gap-2">
          <span className={`w-2 h-2 rounded-full ${connected ? 'bg-green-500' : 'bg-red-500'}`} />
          <span className="text-sm text-slate-400">{connected ? 'Live' : 'Disconnected'}</span>
        </div>
      </header>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 mb-6">
        <MetricCharts token={token} />
      </div>

      <div className="grid grid-cols-1 xl:grid-cols-2 gap-6 mb-6">
        <div className="card">
          <h2 className="text-lg font-semibold mb-4">Network Topology</h2>
          <NetworkGraph devices={devices} />
        </div>
        <AlertsPanel alerts={alerts} />
      </div>

      <div className="card">
        <h2 className="text-lg font-semibold mb-4">Devices</h2>
        <DeviceTable devices={devices} token={token} />
      </div>
    </div>
  );
}
