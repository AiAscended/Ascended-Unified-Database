'use client';

import { use } from 'react';
import { useRouter } from 'next/navigation';
import useSWR from 'swr';
import { AppShell } from '@/components/layout/AppShell';
import { TableManager } from '@/components/databases/TableManager';
import { Badge } from '@/components/ui/Badge';
import { StatusIndicator } from '@/components/ui/StatusIndicator';
import { api } from '@/lib/api';
import type { DatabaseConnection, SystemHealth } from '@/lib/types';

interface PageProps {
  params: Promise<{ id: string }>;
}

export default function DatabaseDetailPage({ params }: PageProps) {
  const { id } = use(params);
  const router = useRouter();

  const { data: db, isLoading, error } = useSWR<DatabaseConnection>(
    `db-${id}`,
    () => api.getDatabase(id),
    { refreshInterval: 20000 },
  );

  const { data: health } = useSWR<SystemHealth>(
    `db-health-${id}`,
    () => api.getDatabaseHealth(id),
    { refreshInterval: 20000 },
  );

  if (isLoading) {
    return (
      <AppShell title="Database">
        <div className="animate-pulse space-y-4">
          <div className="h-8 bg-gray-200 rounded w-1/3" />
          <div className="h-36 bg-gray-200 rounded" />
        </div>
      </AppShell>
    );
  }

  if (error || !db) {
    return (
      <AppShell title="Database">
        <div className="bg-red-50 border border-red-200 rounded-lg p-4 text-sm text-red-700">
          Failed to load database. It may have been deleted or the backend is unavailable.
        </div>
      </AppShell>
    );
  }

  const healthy = health?.databases?.[db.db_type] ?? false;

  return (
    <AppShell title={db.name}>
      <div className="space-y-6">
        {/* Breadcrumb */}
        <button
          onClick={() => router.push('/databases')}
          className="text-sm text-gray-500 hover:text-gray-700 flex items-center gap-1"
        >
          ← Back to Databases
        </button>

        {/* Connection card */}
        <div className="bg-white rounded-lg border border-gray-200 shadow-sm p-6">
          <div className="flex items-start justify-between mb-4">
            <div>
              <h1 className="text-2xl font-bold text-gray-900">{db.name}</h1>
              <p className="text-sm text-gray-500 mt-0.5">
                {db.host}:{db.port}
                {db.database_name ? ` / ${db.database_name}` : ''}
              </p>
            </div>
            <div className="flex items-center gap-2">
              <StatusIndicator status={healthy ? 'healthy' : 'unhealthy'} />
              <Badge status={db.is_active ? 'active' : 'inactive'} label={db.is_active ? 'Active' : 'Inactive'} />
            </div>
          </div>

          <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
            {[
              { label: 'Type', value: db.db_type.toUpperCase() },
              { label: 'Health', value: db.health_status },
              { label: 'SSL', value: db.ssl_enabled ? 'Enabled' : 'Disabled' },
              { label: 'Created', value: new Date(db.created_at).toLocaleDateString() },
            ].map(({ label, value }) => (
              <div key={label} className="bg-gray-50 rounded p-3">
                <p className="text-xs text-gray-500 uppercase tracking-wide">{label}</p>
                <p className="text-sm font-semibold text-gray-900 mt-0.5 capitalize">{value}</p>
              </div>
            ))}
          </div>
        </div>

        {/* Table manager */}
        <div className="bg-white rounded-lg border border-gray-200 shadow-sm p-5">
          <TableManager connectionId={id} />
        </div>
      </div>
    </AppShell>
  );
}
