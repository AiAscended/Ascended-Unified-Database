'use client';

import useSWR from 'swr';
import { AppShell } from '@/components/layout/AppShell';
import { Card } from '@/components/ui/Card';
import { Badge } from '@/components/ui/Badge';
import { Button } from '@/components/ui/Button';
import { api } from '@/lib/api';
import type { EnvConfig, DatabaseConfig } from '@/lib/types';

export default function SettingsPage() {
  const { data: config, isLoading, mutate } = useSWR<EnvConfig>(
    'config',
    () => api.getConfig(),
    { revalidateOnFocus: false },
  );

  const toggle = async (name: string, currently: boolean) => {
    if (currently) {
      await api.disableDatabase(name);
    } else {
      await api.enableDatabase(name);
    }
    mutate();
  };

  const isEnabled = (db: DatabaseConfig): boolean =>
    typeof db.enabled === 'boolean' ? db.enabled : true;

  return (
    <AppShell title="Settings">
      <div className="space-y-6">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">System Settings</h1>
          <p className="mt-1 text-sm text-gray-500">
            Manage environment configuration and database availability across the stack.
          </p>
        </div>

        {isLoading && (
          <div className="space-y-4">
            {[...Array(3)].map((_, i) => (
              <div key={i} className="h-24 bg-gray-100 rounded-lg animate-pulse" />
            ))}
          </div>
        )}

        {config && (
          <>
            {/* Environment */}
            <Card title="Environment">
              <div className="flex items-center gap-4">
                <div>
                  <p className="text-sm text-gray-500">Active Environment</p>
                  <p className="text-xl font-bold text-gray-900 capitalize mt-1">{config.environment}</p>
                </div>
                <Badge
                  status={config.environment === 'production' || config.environment === 'enterprise' ? 'active' : 'degraded'}
                  label={config.environment}
                />
              </div>
            </Card>

            {/* Gateway config */}
            {config.gateway && (
              <Card title="Gateway Configuration">
                <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
                  {Object.entries(config.gateway).map(([key, val]) => (
                    <div key={key} className="bg-gray-50 rounded p-3">
                      <p className="text-xs text-gray-500 uppercase tracking-wide">{key.replace(/_/g, ' ')}</p>
                      <p className="text-sm font-semibold text-gray-900 mt-0.5">{String(val)}</p>
                    </div>
                  ))}
                </div>
              </Card>
            )}

            {/* Database toggles */}
            <Card title="Database Availability">
              <div className="space-y-2">
                {Object.entries(config.databases).map(([name, db]) => {
                  const enabled = isEnabled(db as DatabaseConfig);
                  return (
                    <div key={name} className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
                      <div className="flex items-center gap-3">
                        <span className={`w-2.5 h-2.5 rounded-full ${enabled ? 'bg-green-500' : 'bg-gray-300'}`} />
                        <div>
                          <p className="text-sm font-medium text-gray-900 capitalize">{name.replace(/_/g, ' ')}</p>
                          {(db as DatabaseConfig).provider && (
                            <p className="text-xs text-gray-500">
                              Provider: {(db as DatabaseConfig).provider}
                            </p>
                          )}
                        </div>
                      </div>
                      <Button
                        variant={enabled ? 'danger' : 'secondary'}
                        onClick={() => toggle(name, enabled)}
                      >
                        {enabled ? 'Disable' : 'Enable'}
                      </Button>
                    </div>
                  );
                })}
              </div>
            </Card>
          </>
        )}
      </div>
    </AppShell>
  );
}
