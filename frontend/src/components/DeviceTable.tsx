'use client';

import { format } from 'date-fns';

type Device = { id: string; ip: string; mac?: string; status: string; bandwidth_tx_bps?: number; bandwidth_rx_bps?: number; open_ports?: number[]; last_seen?: string };

type DeviceTableProps = { devices: Device[]; token: string | null };

export function DeviceTable({ devices, token }: DeviceTableProps) {
  return (
    <div className="overflow-x-auto">
      <table className="w-full text-sm">
        <thead>
          <tr className="border-b border-dark-500 text-left text-slate-400">
            <th className="py-2">IP</th>
            <th className="py-2">MAC</th>
            <th className="py-2">Status</th>
            <th className="py-2">TX (bps)</th>
            <th className="py-2">RX (bps)</th>
            <th className="py-2">Ports</th>
            <th className="py-2">Last seen</th>
          </tr>
        </thead>
        <tbody>
          {devices.length === 0 && (
            <tr>
              <td colSpan={7} className="py-8 text-center text-slate-500">
                No devices yet. Start the scanner agent or connect eBPF agents.
              </td>
            </tr>
          )}
          {devices.map((d) => (
            <tr key={d.id} className="border-b border-dark-600/50 hover:bg-dark-700/50">
              <td className="py-2 font-mono">{d.ip}</td>
              <td className="py-2 font-mono text-slate-400">{d.mac || '--'}</td>
              <td className="py-2">
                <span
                  className={`inline-block w-2 h-2 rounded-full mr-2 ${
                    d.status === 'online' ? 'bg-green-500' : d.status === 'offline' ? 'bg-red-500' : 'bg-slate-500'
                  }`}
                />
                {d.status}
              </td>
              <td className="py-2 font-mono">{(d.bandwidth_tx_bps ?? 0).toFixed(0)}</td>
              <td className="py-2 font-mono">{(d.bandwidth_rx_bps ?? 0).toFixed(0)}</td>
              <td className="py-2 font-mono text-slate-400">
                {d.open_ports?.length ? d.open_ports.slice(0, 5).join(', ') + (d.open_ports.length > 5 ? '...' : '') : '--'}
              </td>
              <td className="py-2 text-slate-400">{d.last_seen ? format(new Date(d.last_seen), 'HH:mm:ss') : '--'}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
