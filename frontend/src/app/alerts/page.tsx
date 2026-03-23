'use client';

import { useEffect, useState } from 'react';
import { AlertsPanel } from '@/components/AlertsPanel';
import { fetchWithAuth } from '@/lib/api';

type Alert = { id: string; title: string; message: string; severity: string; created_at?: string };

export default function AlertsPage() {
  const [alerts, setAlerts] = useState<Alert[]>([]);
  const token = typeof window !== 'undefined' ? localStorage.getItem('netscope_token') : null;

  useEffect(() => {
    if (!token) return;
    fetchWithAuth<Alert[]>('/api/v1/alerts', token).then(setAlerts).catch(() => setAlerts([]));
  }, [token]);

  return (
    <div className="min-h-screen p-6">
      <h1 className="text-2xl font-display font-bold text-net-400 mb-6">Alerts</h1>
      <AlertsPanel alerts={alerts} />
    </div>
  );
}
