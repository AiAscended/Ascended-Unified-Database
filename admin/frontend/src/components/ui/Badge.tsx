import clsx from 'clsx';

type BadgeProps = { status: 'healthy' | 'unhealthy' | 'degraded' | 'active' | 'inactive' | string; label?: string };

export function Badge({ status, label }: BadgeProps) {
  const text = label ?? status;
  const cls = clsx('inline-flex items-center px-2 py-0.5 rounded text-xs font-medium', {
    'bg-green-100 text-green-800': status === 'healthy' || status === 'active',
    'bg-red-100 text-red-800': status === 'unhealthy' || status === 'inactive',
    'bg-yellow-100 text-yellow-800': status === 'degraded',
    'bg-gray-100 text-gray-700': !['healthy','active','unhealthy','inactive','degraded'].includes(status),
  });
  return <span className={cls}>{text}</span>;
}
