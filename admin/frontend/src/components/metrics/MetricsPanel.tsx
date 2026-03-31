'use client';
import { useEffect, useRef, useState } from 'react';
import useSWR from 'swr';
import { api } from '@/lib/api';
import { Card } from '@/components/ui/Card';
import { StatusIndicator } from '@/components/ui/StatusIndicator';
import type { MetricsData, SystemHealth } from '@/lib/types';

const BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8001';

export function MetricsPanel() {
  const { data: metrics } = useSWR<MetricsData>('metrics', () => api.getMetrics(), { refreshInterval: 5000 });
  const { data: health } = useSWR<SystemHealth>('health', () => api.getSystemHealth(), { refreshInterval: 5000 });
  const [wsStatus, setWsStatus] = useState<'connecting' | 'connected' | 'disconnected'>('connecting');
  const [liveMetrics, setLiveMetrics] = useState<MetricsData | null>(null);
  const wsRef = useRef<WebSocket | null>(null);

  useEffect(() => {
    const wsUrl = BASE_URL.replace(/^http/, 'ws') + '/admin/ws/metrics';
    const ws = new WebSocket(wsUrl);
    wsRef.current = ws;
    ws.onopen = () => setWsStatus('connected');
    ws.onmessage = (e) => { try { setLiveMetrics(JSON.parse(e.data)); } catch {} };
    ws.onclose = () => setWsStatus('disconnected');
    ws.onerror = () => setWsStatus('disconnected');
    return () => ws.close();
  }, []);

  const display = liveMetrics ?? metrics;

  return (
    <div className="space-y-6">
      <div className="flex items-center gap-2 text-sm text-gray-600">
        <StatusIndicator status={wsStatus === 'connected' ? 'healthy' : 'unhealthy'} />
        WebSocket: {wsStatus}
      </div>

      {health && (
        <Card title="Database Health">
          <div className="grid grid-cols-2 md:grid-cols-3 gap-3">
            {Object.entries(health.databases).map(([db, ok]) => (
              <div key={db} className="flex items-center gap-2">
                <StatusIndicator status={ok ? 'healthy' : 'unhealthy'} />
                <span className="text-sm capitalize">{db}</span>
              </div>
            ))}
          </div>
        </Card>
      )}

      {display && (
        <>
          <Card title="Memory">
            <div className="space-y-1">
              <div className="flex justify-between text-sm">
                <span>Used</span>
                <span>{display.memory.used_pct.toFixed(1)}%</span>
              </div>
              <div className="w-full bg-gray-200 rounded-full h-4 overflow-hidden">
                <div className="h-4 bg-blue-500 rounded-full transition-all" style={{ width: `${display.memory.used_pct}%` }} />
              </div>
              <p className="text-xs text-gray-500">
                {Math.round(display.memory.used_bytes / 1024 / 1024)} MB / {Math.round(display.memory.total_bytes / 1024 / 1024)} MB
              </p>
            </div>
          </Card>

          <Card title="System Load">
            <div className="flex gap-6 text-sm">
              {(['load_1m', 'load_5m', 'load_15m'] as const).map((k) => (
                <div key={k}>
                  <p className="text-gray-500 text-xs">{k.replace('load_', '').replace('m', ' min')}</p>
                  <p className="text-xl font-bold">{display.load[k].toFixed(2)}</p>
                </div>
              ))}
            </div>
          </Card>
        </>
      )}
    </div>
  );
}
