import type { AuditEntry } from '@/lib/types';

export function ActivityFeed({ entries }: { entries: AuditEntry[] }) {
  return (
    <div className="space-y-2">
      {entries.length === 0 && <p className="text-sm text-gray-400">No recent activity.</p>}
      {entries.map((e) => (
        <div key={e.id} className="flex items-start gap-3 text-sm py-2 border-b border-gray-100 last:border-0">
          <span className="w-6 h-6 rounded-full bg-blue-100 text-blue-600 flex items-center justify-center text-xs shrink-0">
            {(e.action[0] ?? 'A').toUpperCase()}
          </span>
          <div className="flex-1 min-w-0">
            <p className="text-gray-800 font-medium truncate">{e.action} <span className="text-gray-500 font-normal">{e.resource}</span></p>
            <p className="text-xs text-gray-400">{new Date(e.created_at).toLocaleString()}</p>
          </div>
        </div>
      ))}
    </div>
  );
}
