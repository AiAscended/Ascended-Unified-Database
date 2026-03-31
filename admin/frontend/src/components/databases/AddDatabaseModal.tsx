'use client';
import { useState } from 'react';
import { Modal } from '@/components/ui/Modal';
import { Button } from '@/components/ui/Button';
import { api } from '@/lib/api';
import type { DatabaseConnection } from '@/lib/types';

const DB_TYPES = ['postgres', 'redis', 'qdrant', 'neo4j', 'minio', 'clickhouse', 'kafka'];

interface AddDatabaseModalProps { open: boolean; onClose: () => void; onCreated: (db: DatabaseConnection) => void }

export function AddDatabaseModal({ open, onClose, onCreated }: AddDatabaseModalProps) {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [form, setForm] = useState({ name: '', db_type: 'postgres', host: 'localhost', port: '5432', database_name: '', username: '', password: '' });

  const set = (k: string, v: string) => setForm((f) => ({ ...f, [k]: v }));

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!form.name || !form.host || !form.port) { setError('Name, host and port are required.'); return; }
    setLoading(true); setError('');
    try {
      const db = await api.createDatabase({ ...form, port: Number(form.port) });
      onCreated(db); onClose();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to create connection');
    } finally {
      setLoading(false);
    }
  };

  const field = (label: string, key: string, type = 'text', placeholder = '') => (
    <div key={key}>
      <label className="block text-sm font-medium text-gray-700 mb-1">{label}</label>
      <input
        type={type}
        placeholder={placeholder}
        value={(form as Record<string, string>)[key]}
        onChange={(e) => set(key, e.target.value)}
        className="w-full border border-gray-300 rounded px-3 py-1.5 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
      />
    </div>
  );

  return (
    <Modal open={open} onClose={onClose} title="Register Database Connection">
      <form onSubmit={handleSubmit} className="space-y-3">
        {field('Name', 'name', 'text', 'My Postgres DB')}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">DB Type</label>
          <select value={form.db_type} onChange={(e) => set('db_type', e.target.value)}
            className="w-full border border-gray-300 rounded px-3 py-1.5 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500">
            {DB_TYPES.map((t) => <option key={t} value={t}>{t}</option>)}
          </select>
        </div>
        {field('Host', 'host', 'text', 'localhost')}
        {field('Port', 'port', 'number', '5432')}
        {field('Database Name', 'database_name', 'text', 'mydb')}
        {field('Username', 'username', 'text', 'admin')}
        {field('Password', 'password', 'password')}
        {error && <p className="text-red-600 text-sm">{error}</p>}
        <div className="flex justify-end gap-2 pt-2">
          <Button variant="secondary" type="button" onClick={onClose}>Cancel</Button>
          <Button variant="primary" type="submit" loading={loading}>Add Connection</Button>
        </div>
      </form>
    </Modal>
  );
}
