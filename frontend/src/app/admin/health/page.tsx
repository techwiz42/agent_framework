'use client';

import { useEffect, useState } from 'react';
import { MainLayout } from '@/components/layout/MainLayout';
import { Card } from '@/components/ui/card';
import { useAuth } from '@/context/AuthContext';
import { api } from '@/services/api';

interface ComponentHealth {
  status: 'healthy' | 'degraded' | 'unhealthy';
  connections?: number;
  [key: string]: unknown;
}

interface HealthStatus {
  status: 'healthy' | 'degraded' | 'unhealthy';
  components: {
    [key: string]: ComponentHealth;
  };
}

export default function AdminHealthPage() {
  const [health, setHealth] = useState<HealthStatus | null>(null);
  const { token, user } = useAuth();

  useEffect(() => {
    if (!token || !user || user.role !== 'admin') {
      return;
    }

    const fetchHealth = async () => {
      try {
        const response = await api.get<HealthStatus>('/api/admin/health', {
          headers: { Authorization: `Bearer ${token}` }
        });
        setHealth(response.data);
      } catch (error) {
        console.error('Failed to fetch health:', error);
      }
    };

    fetchHealth();
    const interval = setInterval(fetchHealth, 30000); // Poll every 30s
    return () => clearInterval(interval);
  }, [token, user]);

  if (!token || !user || user.role !== 'admin') {
    return (
      <MainLayout>
        <div className="text-red-600">Not authenticated</div>
      </MainLayout>
    );
  }

  if (!health) {
    return (
      <MainLayout>
        <div>Loading health...</div>
      </MainLayout>
    );
  }

  return (
    <MainLayout>
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <Card className="p-4">
          <h3 className="font-bold mb-2">Overview</h3>
          <div className={`${
            health.status === 'healthy' ? 'text-green-600' : 'text-red-600'
          }`}>
            Status: {health.status}
          </div>
        </Card>

        <Card className="p-4">
          <h3 className="font-bold mb-2">Components</h3>
          {Object.entries(health.components).map(([key, value]) => (
            <div key={key} className={`${
              value.status === 'healthy' ? 'text-green-600' : 'text-red-600'
            }`}>
              {key}: {value.status}
            </div>
          ))}
        </Card>
      </div>
    </MainLayout>
  );
}
