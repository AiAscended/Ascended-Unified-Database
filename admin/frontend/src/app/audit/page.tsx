'use client';

import { useState } from 'react';
import useSWR from 'swr';
import { AppShell } from '@/components/layout/AppShell';
import { Badge } from '@/components/ui/Badge';
import { Button } from '@/components/ui/Button';
import { api } from '@/lib/api';
import { authHeaders } from '@/lib/auth';
import type { AuditEntry } from '@/lib/types';

const BASE = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8001';
const RESOURCES = ['all', 'database', 'user', 'config', 'deployment', 'auth'] as const;

export default function AuditPage() {
  const [page, setPage] = useState(1);
  const [resource, setResource] = useState('all');

  const { data, isLoading, error } = useSWR<AuditEntry[]>(
    `audit-${page}-${resource}`,
    () => api.getAuditLog(page, 50, resource === 'all' ? undefined : resource),
    { refreshInterval: 10000 },
  );

  const handleExport = async () => {
    const res = await fetch(`${BASE}/admin/api/audit/export`, { headers: authHeaders() });
    if (!res.ok) return;
    const blob = await res.blob();
    const a = document.createElement('a');
    a.href = URL.createObjectURL(blob);
    a.download = `audit-log-${new Date().toISOString().split('T')[0]}.csv`;
    a.click();
  };

  return (
    <AppShell title="Audit Log">
      <div className="space-y-6">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-2xl font-bold text-gray-900">Audit Log</h1>
            <p className="mt-1 text-sm text-gray-500">
              Complete history of all administrative actions on the platform.
            </p>
          </div>
          <Button variant="secondary" onClick={handleExport}>Export CSV</Button>
        </div>

        {/* Resource filter */}
        <div className="flex flex-wrap gap-2">
          {RESOURCES.map((r) => (
            <button
              key={r}
              onClick={() => { setResource(r); setPage(1); }}
              className={`px-3 py-1.5 rounded-full text-xs font-medium transition-colors ${
                resource === r ? 'bg-blue-600 text-white' : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
              }`}
            >
              {r.charAt(0).toUpperCase() + r.slice(1)}
            </button>
          ))}
        </div>

        {error && (
          <div className="bg-red-50 border border-red-200 rounded-lg p-4 text-sm text-red-700">
            Failed to load audit log.
          </div>
        )}

        <div className="bg-white rounded-lg border border-gray-200 shadow-sm overflow-hidden">
          <table className="min-w-full divide-y divide-gray-200 text-sm">
            <thead className="bg-gray-50 text-gray-500 uppercase text-xs">
              <tr>
                {['Timestamp', 'User', 'Action', 'Resource', 'Status', 'IP'].map((h) => (
                  <th key={h} className="px-4 py-3 text-left font-medium tracking-wider">{h}</th>
                ))}
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-100">
              {isLoading && [...Array(8)].map((_, i) => (
                <tr key={i}>
                  {[...Array(6)].map((__, j) => (
                    <td key={j} className="px-4 py-3">
                      <div className="h-4 bg-gray-100 rounded animate-pulse" />
                    </td>
                  ))}
                </tr>
              ))}

              {(data ?? []).map((entry) => (
                <tr key={entry.id} className="hover:bg-gray-50">
                  <td className="px-4 py-3 text-gray-500 whitespace-nowrap">
                    {new Date(entry.created_at).toLocaleString()}
                  </td>
                  <td className="px-4 py-3 font-mono text-xs text-gray-600">
                    {entry.user_id ? entry.user_id.slice(0, 8) + '…' : 'system'}
                  </td>
                  <td className="px-4 py-3 font-medium text-gray-900">{entry.action}</td>
                  <td className="px-4 py-3 text-gray-600">{entry.resource}</td>
                  <td className="px-4 py-3">
                    <Badge status={entry.status === 'success' ? 'healthy' : 'unhealthy'} label={entry.status} />
                  </td>
                  <td className="px-4 py-3 font-mono text-xs text-gray-500">{entry.ip_address ?? '—'}</td>
                </tr>
              ))}

              {!isLoading && (data ?? []).length === 0 && (
                <tr>
                  <td colSpan={6} className="px-4 py-8 text-center text-gray-400">No log entries found.</td>
                </tr>
              )}
            </tbody>
          </table>
        </div>

        {/* Pagination */}
        <div className="flex items-center justify-between text-sm text-gray-500">
          <span>Page {page} · {data?.length ?? 0} entries</span>
          <div className="flex gap-2">
            <Button variant="secondary" onClick={() => setPage(Math.max(1, page - 1))} disabled={page === 1}>
              Previous
            </Button>
            <Button variant="secondary" onClick={() => setPage(page + 1)} disabled={(data?.length ?? 0) < 50}>
              Next
            </Button>
          </div>
        </div>
      </div>
    </AppShell>
  );
}
