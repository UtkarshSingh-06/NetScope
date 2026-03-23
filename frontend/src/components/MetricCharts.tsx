'use client';

import { useEffect, useState } from 'react';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts';
import { fetchWithAuth } from '@/lib/api';

type MetricChartsProps = { token: string | null };

export function MetricCharts({ token }: MetricChartsProps) {
  const [data, setData] = useState<{ time: string; bytes: number }[]>([]);

  useEffect(() => {
    if (!token) return;
    let cancelled = false;
    async function load() {
      try {
        const res = await fetchWithAuth<{ result?: { values?: [number, string][] }[] }>(
          '/api/v1/metrics/query?expr=sum(rate(network_observability_tcp_bytes_sent_total[5m]))*8',
          token
        );
        if (cancelled) return;
        const series = res?.result?.[0]?.values?.slice(-24) || [];
        setData(series.map(([t, v]) => ({ time: new Date(t * 1000).toLocaleTimeString(), bytes: Number(v) })));
      } catch {
        setData([{ time: '--', bytes: 0 }]);
      }
    }
    load();
    const id = setInterval(load, 15000);
    return () => {
      cancelled = true;
      clearInterval(id);
    };
  }, [token]);

  return (
    <div className="card col-span-2">
      <h2 className="text-lg font-semibold mb-4">Throughput (bps)</h2>
      <div className="h-48">
        <ResponsiveContainer width="100%" height="100%">
          <LineChart data={data}>
            <CartesianGrid strokeDasharray="3 3" stroke="#30363d" />
            <XAxis dataKey="time" stroke="#8b949e" fontSize={10} />
            <YAxis stroke="#8b949e" fontSize={10} />
            <Tooltip contentStyle={{ background: '#161b22', border: '1px solid #30363d' }} />
            <Line type="monotone" dataKey="bytes" stroke="#2dd4bf" strokeWidth={2} dot={false} />
          </LineChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
}
