import { ReactNode } from 'react';

interface CardProps { title?: string; children: ReactNode; className?: string }

export function Card({ title, children, className = '' }: CardProps) {
  return (
    <div className={`bg-white rounded-lg border border-gray-200 shadow-sm ${className}`}>
      {title && <div className="px-5 py-3 border-b border-gray-200 font-semibold text-gray-700">{title}</div>}
      <div className="p-5">{children}</div>
    </div>
  );
}
