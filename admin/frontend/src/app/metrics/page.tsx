'use client';

import { AppShell } from '@/components/layout/AppShell';
import { MetricsPanel } from '@/components/metrics/MetricsPanel';

export default function MetricsPage() {
  return (
    <AppShell title="Metrics">
      <div className="space-y-6">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Live Metrics</h1>
          <p className="mt-1 text-sm text-gray-500">
            Real-time system performance and database health across the stack.
            Updates every 5 seconds via WebSocket.
          </p>
        </div>
        <MetricsPanel />
      </div>
    </AppShell>
  );
}
