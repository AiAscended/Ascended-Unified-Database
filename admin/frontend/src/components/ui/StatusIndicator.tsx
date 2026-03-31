import clsx from 'clsx';

type StatusType = 'healthy' | 'unhealthy' | 'degraded';
interface StatusIndicatorProps { status: StatusType }

export function StatusIndicator({ status }: StatusIndicatorProps) {
  const cls = clsx('inline-block w-2.5 h-2.5 rounded-full', {
    'bg-green-500 animate-pulse': status === 'healthy',
    'bg-red-500': status === 'unhealthy',
    'bg-yellow-400 animate-pulse': status === 'degraded',
  });
  return <span className={cls} title={status} />;
}
