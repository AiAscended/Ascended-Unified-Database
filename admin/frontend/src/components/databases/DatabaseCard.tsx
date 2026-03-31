'use client';
import { Badge } from '@/components/ui/Badge';
import { Button } from '@/components/ui/Button';
import { StatusIndicator } from '@/components/ui/StatusIndicator';
import type { DatabaseConnection } from '@/lib/types';
import { useRouter } from 'next/navigation';

interface DatabaseCardProps {
  db: DatabaseConnection;
  onDelete: (id: string) => void;
}

export function DatabaseCard({ db, onDelete }: DatabaseCardProps) {
  const router = useRouter();
  const status = db.health_status === 'healthy' ? 'healthy' : db.health_status === 'degraded' ? 'degraded' : 'unhealthy';
  return (
    <div className="bg-white rounded-lg border border-gray-200 shadow-sm p-4 flex flex-col gap-3">
      <div className="flex items-center justify-between">
        <Badge status={db.db_type} label={db.db_type.toUpperCase()} />
        <div className="flex items-center gap-1.5">
          <StatusIndicator status={status} />
          <span className="text-xs text-gray-500">{db.health_status ?? 'unknown'}</span>
        </div>
      </div>
      <div>
        <p className="font-semibold text-gray-800">{db.name}</p>
        <p className="text-xs text-gray-500 mt-0.5">{db.host}:{db.port}</p>
        {db.database_name && <p className="text-xs text-gray-400">db: {db.database_name}</p>}
      </div>
      <div className="flex gap-2 mt-auto">
        <Button variant="secondary" onClick={() => router.push(`/databases/${db.id}`)}>
          View Tables
        </Button>
        <Button variant="danger" onClick={() => onDelete(db.id)}>
          Delete
        </Button>
      </div>
    </div>
  );
}
