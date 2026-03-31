'use client';
import { useRouter } from 'next/navigation';
import { logout } from '@/lib/auth';
import { StatusIndicator } from '@/components/ui/StatusIndicator';
import useSWR from 'swr';
import { api } from '@/lib/api';
import type { SystemHealth } from '@/lib/types';

interface HeaderProps { title: string }

export function Header({ title }: HeaderProps) {
  const router = useRouter();
  const { data } = useSWR<SystemHealth>('health', () => api.getSystemHealth(), { refreshInterval: 10000 });

  const handleLogout = () => { logout(); router.push('/login'); };

  const status = data?.status === 'healthy' ? 'healthy' : data?.status === 'degraded' ? 'degraded' : 'unhealthy';

  return (
    <header className="h-14 bg-white border-b border-gray-200 flex items-center justify-between px-6">
      <h1 className="text-lg font-semibold text-gray-800">{title}</h1>
      <div className="flex items-center gap-4">
        <div className="flex items-center gap-2 text-sm text-gray-600">
          <StatusIndicator status={status} />
          <span>{data?.status ?? 'checking…'}</span>
        </div>
        <button onClick={handleLogout} className="text-sm text-gray-500 hover:text-gray-800 border border-gray-200 px-3 py-1 rounded">
          Logout
        </button>
      </div>
    </header>
  );
}
