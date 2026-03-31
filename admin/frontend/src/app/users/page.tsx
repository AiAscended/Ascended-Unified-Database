'use client';

import { useState } from 'react';
import useSWR from 'swr';
import { AppShell } from '@/components/layout/AppShell';
import { Badge } from '@/components/ui/Badge';
import { Button } from '@/components/ui/Button';
import { api } from '@/lib/api';
import type { UserSummary } from '@/lib/types';

const ROLES = ['viewer', 'developer', 'operator', 'admin'] as const;

export default function UsersPage() {
  const [page, setPage] = useState(0);
  const [busy, setBusy] = useState<string | null>(null);

  const { data, isLoading, error, mutate } = useSWR<UserSummary[]>(
    `users-${page}`,
    () => api.getUsers(page * 20, 20),
    { refreshInterval: 30000 },
  );

  const act = async (fn: () => Promise<unknown>, key: string) => {
    setBusy(key);
    try { await fn(); mutate(); } finally { setBusy(null); }
  };

  return (
    <AppShell title="Users">
      <div className="space-y-6">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">User Management</h1>
          <p className="mt-1 text-sm text-gray-500">
            Manage accounts and roles across the AscendedStack platform.
          </p>
        </div>

        {error && (
          <div className="bg-red-50 border border-red-200 rounded-lg p-4 text-sm text-red-700">
            Failed to load users.
          </div>
        )}

        <div className="bg-white rounded-lg border border-gray-200 shadow-sm overflow-hidden">
          <table className="min-w-full divide-y divide-gray-200 text-sm">
            <thead className="bg-gray-50 text-gray-500 uppercase text-xs">
              <tr>
                {['Username', 'Email', 'Role', 'Status', 'Created', 'Actions'].map((h) => (
                  <th key={h} className="px-4 py-3 text-left font-medium tracking-wider">{h}</th>
                ))}
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-100">
              {isLoading && [...Array(5)].map((_, i) => (
                <tr key={i}>
                  {[...Array(6)].map((__, j) => (
                    <td key={j} className="px-4 py-3">
                      <div className="h-4 bg-gray-100 rounded animate-pulse" />
                    </td>
                  ))}
                </tr>
              ))}

              {(data ?? []).map((user) => (
                <tr key={user.id} className="hover:bg-gray-50 transition-colors">
                  <td className="px-4 py-3 font-medium text-gray-900">{user.username}</td>
                  <td className="px-4 py-3 text-gray-500">{user.email ?? '—'}</td>
                  <td className="px-4 py-3">
                    <select
                      value={user.role}
                      disabled={busy === `role-${user.id}`}
                      onChange={(e) => act(() => api.updateUserRole(user.id, e.target.value), `role-${user.id}`)}
                      className="border border-gray-200 rounded px-2 py-1 text-xs bg-white focus:outline-none focus:ring-2 focus:ring-blue-500"
                    >
                      {ROLES.map((r) => (
                        <option key={r} value={r}>{r.charAt(0).toUpperCase() + r.slice(1)}</option>
                      ))}
                    </select>
                  </td>
                  <td className="px-4 py-3">
                    <Badge status={user.is_active ? 'active' : 'inactive'} label={user.is_active ? 'Active' : 'Inactive'} />
                  </td>
                  <td className="px-4 py-3 text-gray-500">{new Date(user.created_at).toLocaleDateString()}</td>
                  <td className="px-4 py-3">
                    <Button
                      variant={user.is_active ? 'danger' : 'secondary'}
                      loading={busy === `toggle-${user.id}`}
                      onClick={() =>
                        act(
                          () => user.is_active ? api.deactivateUser(user.id) : api.activateUser(user.id),
                          `toggle-${user.id}`,
                        )
                      }
                    >
                      {user.is_active ? 'Deactivate' : 'Activate'}
                    </Button>
                  </td>
                </tr>
              ))}

              {!isLoading && (data ?? []).length === 0 && (
                <tr>
                  <td colSpan={6} className="px-4 py-8 text-center text-gray-400">No users found.</td>
                </tr>
              )}
            </tbody>
          </table>
        </div>

        {/* Pagination */}
        <div className="flex items-center justify-between text-sm text-gray-500">
          <span>Page {page + 1}</span>
          <div className="flex gap-2">
            <Button variant="secondary" onClick={() => setPage(Math.max(0, page - 1))} disabled={page === 0}>
              Previous
            </Button>
            <Button variant="secondary" onClick={() => setPage(page + 1)} disabled={(data?.length ?? 0) < 20}>
              Next
            </Button>
          </div>
        </div>
      </div>
    </AppShell>
  );
}
