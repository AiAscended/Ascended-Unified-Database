'use client';
import Link from 'next/link';
import { usePathname } from 'next/navigation';
import clsx from 'clsx';

const NAV = [
  { href: '/dashboard', label: 'Dashboard', icon: '⊞' },
  { href: '/databases', label: 'Databases', icon: '🗄' },
  { href: '/users', label: 'Users', icon: '👥' },
  { href: '/metrics', label: 'Metrics', icon: '📈' },
  { href: '/audit', label: 'Audit Log', icon: '📋' },
  { href: '/settings', label: 'Settings', icon: '⚙' },
];

export function Sidebar() {
  const pathname = usePathname();
  return (
    <aside className="w-60 min-h-screen bg-gray-900 text-white flex flex-col">
      <div className="px-5 py-4 border-b border-gray-700">
        <span className="font-bold text-sm tracking-wide text-blue-400">AscendedStack</span>
        <div className="text-xs text-gray-400 mt-0.5">Admin Panel</div>
      </div>
      <nav className="flex-1 py-4 space-y-0.5">
        {NAV.map(({ href, label, icon }) => (
          <Link
            key={href}
            href={href}
            className={clsx(
              'flex items-center gap-3 px-5 py-2.5 text-sm transition-colors',
              pathname.startsWith(href)
                ? 'bg-blue-600 text-white'
                : 'text-gray-300 hover:bg-gray-800',
            )}
          >
            <span>{icon}</span>
            {label}
          </Link>
        ))}
      </nav>
    </aside>
  );
}
