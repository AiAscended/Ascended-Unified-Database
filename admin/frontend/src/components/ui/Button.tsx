import clsx from 'clsx';
import { ButtonHTMLAttributes } from 'react';

type Variant = 'primary' | 'secondary' | 'danger';
interface ButtonProps extends ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: Variant;
  loading?: boolean;
}

export function Button({ variant = 'primary', loading, children, className, disabled, ...props }: ButtonProps) {
  const cls = clsx(
    'inline-flex items-center px-4 py-2 rounded text-sm font-medium transition-colors disabled:opacity-50 cursor-pointer',
    {
      'bg-blue-600 text-white hover:bg-blue-700': variant === 'primary',
      'bg-white text-gray-700 border border-gray-300 hover:bg-gray-50': variant === 'secondary',
      'bg-red-600 text-white hover:bg-red-700': variant === 'danger',
    },
    className,
  );
  return (
    <button className={cls} disabled={disabled || loading} {...props}>
      {loading ? <span className="mr-2 animate-spin">⟳</span> : null}
      {children}
    </button>
  );
}
