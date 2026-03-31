import { StatusIndicator } from '@/components/ui/StatusIndicator';

const DB_ICONS: Record<string, string> = {
  postgres: '🐘', redis: '⚡', qdrant: '🔮', neo4j: '🕸',
  minio: '📦', clickhouse: '🖱', kafka: '📨',
};

interface DbEntry { name: string; db_type: string; is_active: boolean; health_status?: string; count?: number }

export function DatabaseGrid({ databases }: { databases: DbEntry[] }) {
  return (
    <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-4">
      {databases.map((db) => {
        const status = db.health_status === 'healthy' ? 'healthy' : db.health_status === 'degraded' ? 'degraded' : 'unhealthy';
        return (
          <div key={db.name} className="bg-white rounded-lg border border-gray-200 p-4 flex flex-col gap-2">
            <div className="flex items-center gap-2 text-2xl">
              {DB_ICONS[db.db_type] ?? '🗄'}
              <span className="text-sm font-medium text-gray-700 capitalize">{db.db_type}</span>
            </div>
            <p className="text-xs text-gray-500 truncate">{db.name}</p>
            <div className="flex items-center gap-1.5 mt-auto">
              <StatusIndicator status={db.is_active ? status : 'unhealthy'} />
              <span className="text-xs text-gray-500">{db.is_active ? (db.health_status ?? 'unknown') : 'disabled'}</span>
            </div>
          </div>
        );
      })}
    </div>
  );
}
