'use client';

import { format } from 'date-fns';
import clsx from 'clsx';

type Alert = { id: string; title: string; message: string; severity: string; created_at?: string };

type AlertsPanelProps = { alerts: Alert[] };

const severityColors: Record<string, string> = {
  low: 'border-l-green-500',
  medium: 'border-l-yellow-500',
  high: 'border-l-orange-500',
  critical: 'border-l-red-500',
};

export function AlertsPanel({ alerts }: AlertsPanelProps) {
  return (
    <div className="card">
      <h2 className="text-lg font-semibold mb-4">Alerts</h2>
      <div className="space-y-2 max-h-64 overflow-y-auto">
        {alerts.length === 0 && (
          <p className="text-slate-500 text-sm py-4">No alerts.</p>
        )}
        {alerts.slice(0, 20).map((a) => (
          <div
            key={a.id}
            className={clsx(
              'border-l-4 pl-3 py-2 rounded-r bg-dark-700/50',
              severityColors[a.severity] || 'border-l-slate-500'
            )}
          >
            <div className="font-medium text-sm">{a.title}</div>
            <div className="text-slate-400 text-xs">{a.message}</div>
            {a.created_at && (
              <div className="text-slate-500 text-xs mt-1">{format(new Date(a.created_at), 'PPp')}</div>
            )}
          </div>
        ))}
      </div>
    </div>
  );
}
