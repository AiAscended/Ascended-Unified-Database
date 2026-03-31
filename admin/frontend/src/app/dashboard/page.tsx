'use client';
import useSWR from 'swr';
import { api } from '@/lib/api';
import { AppShell } from '@/components/layout/AppShell';
import { StatsCard } from '@/components/dashboard/StatsCard';
import { DatabaseGrid } from '@/components/dashboard/DatabaseGrid';
import { ActivityFeed } from '@/components/dashboard/ActivityFeed';
import { Card } from '@/components/ui/Card';
import type { SystemHealth, DatabaseConnection, AuditEntry } from '@/lib/types';

export default function DashboardPage() {
  const { data: health } = useSWR<SystemHealth>('health', () => api.getSystemHealth(), { refreshInterval: 10000 });
  const { data: databases } = useSWR<DatabaseConnection[]>('databases', () => api.getDatabases());
  const { data: audit } = useSWR<AuditEntry[]>('audit', () => api.getAuditLog(1));

  const activeCount = databases?.filter((d) => d.is_active).length ?? 0;
  const healthyCount = Object.values(health?.databases ?? {}).filter(Boolean).length;

  return (
    <AppShell title="Dashboard">
      <div className="space-y-6">
        <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
          <StatsCard title="Total Databases" value={databases?.length ?? '—'} icon="🗄" />
          <StatsCard title="Active Connections" value={activeCount} icon="🔗" />
          <StatsCard title="Healthy DBs" value={`${healthyCount}/${Object.keys(health?.databases ?? {}).length}`} icon="💚" />
          <StatsCard title="System Status" value={health?.status ?? 'checking'} icon="🛡" />
        </div>

        <Card title="Database Connections">
          <DatabaseGrid databases={databases ?? []} />
        </Card>

        <Card title="Recent Activity">
          <ActivityFeed entries={(audit ?? []).slice(0, 10)} />
        </Card>
      </div>
    </AppShell>
  );
}
