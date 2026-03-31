'use client';
import { useState } from 'react';
import useSWR from 'swr';
import { api } from '@/lib/api';
import { Button } from '@/components/ui/Button';
import type { TableInfo, ColumnDef } from '@/lib/types';

interface TableManagerProps { connectionId: string }

const EMPTY_COL: ColumnDef = { name: '', type: 'text', nullable: true, primary_key: false };

export function TableManager({ connectionId }: TableManagerProps) {
  const { data: tables, mutate } = useSWR<TableInfo[]>(`tables-${connectionId}`, () => api.getDatabaseTables(connectionId));
  const [showForm, setShowForm] = useState(false);
  const [tableName, setTableName] = useState('');
  const [columns, setColumns] = useState<ColumnDef[]>([{ ...EMPTY_COL, primary_key: true, name: 'id', type: 'uuid' }]);
  const [loading, setLoading] = useState(false);

  const addCol = () => setColumns((c) => [...c, { ...EMPTY_COL }]);
  const setCol = (i: number, k: keyof ColumnDef, v: string | boolean) =>
    setColumns((cols) => cols.map((c, idx) => idx === i ? { ...c, [k]: v } : c));

  const handleCreate = async () => {
    if (!tableName) return;
    setLoading(true);
    try {
      await api.createTable(connectionId, { connection_id: connectionId, table_name: tableName, columns });
      setShowForm(false); setTableName(''); setColumns([{ ...EMPTY_COL, primary_key: true, name: 'id', type: 'uuid' }]);
      mutate();
    } finally { setLoading(false); }
  };

  const handleDrop = async (name: string) => {
    if (!confirm(`Drop table "${name}"?`)) return;
    await api.dropTable(connectionId, name);
    mutate();
  };

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <h3 className="font-semibold text-gray-700">Tables / Collections</h3>
        <Button variant="primary" onClick={() => setShowForm((v) => !v)}>+ Create Table</Button>
      </div>

      {showForm && (
        <div className="border border-gray-200 rounded-lg p-4 bg-gray-50 space-y-3">
          <input placeholder="Table name" value={tableName} onChange={(e) => setTableName(e.target.value)}
            className="border border-gray-300 rounded px-3 py-1.5 text-sm w-full" />
          <div className="space-y-2">
            {columns.map((col, i) => (
              <div key={i} className="flex gap-2 items-center flex-wrap">
                <input placeholder="column name" value={col.name} onChange={(e) => setCol(i, 'name', e.target.value)}
                  className="border border-gray-300 rounded px-2 py-1 text-xs w-28" />
                <input placeholder="type" value={col.type} onChange={(e) => setCol(i, 'type', e.target.value)}
                  className="border border-gray-300 rounded px-2 py-1 text-xs w-24" />
                <label className="flex items-center gap-1 text-xs">
                  <input type="checkbox" checked={col.nullable} onChange={(e) => setCol(i, 'nullable', e.target.checked)} /> nullable
                </label>
                <label className="flex items-center gap-1 text-xs">
                  <input type="checkbox" checked={col.primary_key} onChange={(e) => setCol(i, 'primary_key', e.target.checked)} /> PK
                </label>
              </div>
            ))}
          </div>
          <div className="flex gap-2">
            <Button variant="secondary" onClick={addCol}>+ Column</Button>
            <Button variant="primary" loading={loading} onClick={handleCreate}>Create</Button>
          </div>
        </div>
      )}

      <div className="overflow-x-auto">
        <table className="w-full text-sm text-left border border-gray-200 rounded-lg overflow-hidden">
          <thead className="bg-gray-50 text-gray-600">
            <tr>
              <th className="px-4 py-2">Name</th>
              <th className="px-4 py-2">Schema</th>
              <th className="px-4 py-2">Rows</th>
              <th className="px-4 py-2">Size</th>
              <th className="px-4 py-2">Columns</th>
              <th className="px-4 py-2"></th>
            </tr>
          </thead>
          <tbody>
            {(tables ?? []).map((t) => (
              <tr key={t.name} className="border-t border-gray-100 hover:bg-gray-50">
                <td className="px-4 py-2 font-medium">{t.name}</td>
                <td className="px-4 py-2 text-gray-500">{t.schema_name ?? '—'}</td>
                <td className="px-4 py-2">{t.row_count?.toLocaleString() ?? '—'}</td>
                <td className="px-4 py-2">{t.size_bytes ? `${Math.round(t.size_bytes / 1024)} KB` : '—'}</td>
                <td className="px-4 py-2">{t.columns.length}</td>
                <td className="px-4 py-2"><Button variant="danger" onClick={() => handleDrop(t.name)}>Drop</Button></td>
              </tr>
            ))}
            {(tables ?? []).length === 0 && (
              <tr><td colSpan={6} className="px-4 py-6 text-center text-gray-400">No tables found.</td></tr>
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
}
