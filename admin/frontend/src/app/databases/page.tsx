'use client';

import { useState } from 'react';
import useSWR from 'swr';
import { AppShell } from '@/components/layout/AppShell';
import { DatabaseCard } from '@/components/databases/DatabaseCard';
import { AddDatabaseModal } from '@/components/databases/AddDatabaseModal';
import { Button } from '@/components/ui/Button';
import { api } from '@/lib/api';
import type { DatabaseConnection } from '@/lib/types';

const DB_TYPES = ['all', 'postgres', 'redis', 'qdrant', 'neo4j', 'minio', 'clickhouse', 'kafka'] as const;

export default function DatabasesPage() {
  const [filter, setFilter] = useState<string>('all');
  const [showModal, setShowModal] = useState(false);

  const { data, isLoading, error, mutate } = useSWR<DatabaseConnection[]>(
    'databases',
    () => api.getDatabases(),
    { refreshInterval: 15000 },
  );

  const filtered = (data ?? []).filter((db) => filter === 'all' || db.db_type === filter);

  const handleDelete = async (id: string) => {
    if (!confirm('Remove this database connection?')) return;
    await api.deleteDatabase(id);
    mutate();
  };

  return (
    <AppShell title="Databases">
      <div className="space-y-6">
        {/* Header */}
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-2xl font-bold text-gray-900">Database Connections</h1>
            <p className="mt-1 text-sm text-gray-500">
              Register, inspect, and manage every database in the AscendedStack.
            </p>
          </div>
          <Button onClick={() => setShowModal(true)}>+ Add Database</Button>
        </div>

        {/* Type filter */}
        <div className="flex flex-wrap gap-2">
          {DB_TYPES.map((t) => (
            <button
              key={t}
              onClick={() => setFilter(t)}
              className={`px-3 py-1.5 rounded-full text-xs font-medium transition-colors ${
                filter === t
                  ? 'bg-blue-600 text-white'
                  : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
              }`}
            >
              {t.charAt(0).toUpperCase() + t.slice(1)}
            </button>
          ))}
        </div>

        {/* Error */}
        {error && (
          <div className="bg-red-50 border border-red-200 rounded-lg p-4 text-sm text-red-700">
            Failed to load database connections. Ensure the admin backend is running.
          </div>
        )}

        {/* Loading skeletons */}
        {isLoading && (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {[...Array(6)].map((_, i) => (
              <div key={i} className="h-40 bg-gray-100 rounded-lg animate-pulse" />
            ))}
          </div>
        )}

        {/* Empty state */}
        {!isLoading && !error && filtered.length === 0 && (
          <div className="text-center py-16 text-gray-400">
            <p className="text-lg">No connections found.</p>
            <p className="text-sm mt-1">Click &quot;Add Database&quot; to register your first connection.</p>
          </div>
        )}

        {/* Grid */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {filtered.map((db) => (
            <DatabaseCard key={db.id} db={db} onDelete={handleDelete} />
          ))}
        </div>
      </div>

      {showModal && (
        <AddDatabaseModal
          open={showModal}
          onClose={() => setShowModal(false)}
          onCreated={() => { setShowModal(false); mutate(); }}
        />
      )}
    </AppShell>
  );
}
