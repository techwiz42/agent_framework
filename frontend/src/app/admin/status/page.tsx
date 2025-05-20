'use client';

import { useState, useEffect } from 'react';
import { useAuth } from '@/context/AuthContext';
import { Card } from '@/components/ui/card';
import { MainLayout } from '@/components/layout/MainLayout';
import { api } from '@/services/api';

interface SystemStatus {
  system: {
    cpu_percent: number;
    memory_percent: number;
    disk_percent: number;
    load_averages: {
      '1min': number;
      '5min': number;
      '15min': number;
    };
  };
  database: {
    connections: {
      active: number;
      available: number;
      total: number;
    };
  };
  websockets: {
    current_connections: number;
    peak_connections: number;
    active_conversations: number;
  };
  rag: {
    storage: string;            // Now matches backend's humanized size string
    total_documents: number;    // Now matches backend's actual document count
    collections: number;
    users: number;
  };
}

export default function AdminStatusPage() {
   console.log('Component rendering'); 
  const [status, setStatus] = useState<SystemStatus | null>(null);
  const { token, user } = useAuth();

  useEffect(() => {
      console.log('Effect triggered with:', {
    hasToken: !!token,
    hasUser: !!user,
    userRole: user?.role
  });
    if (!token || !user || user.role !== 'admin') {
      return;
    }

  const fetchStatus = async () => {
    console.log("Starting status fetch");
    try {
      console.log("Token present:", !!token);
      const response = await api.get<SystemStatus>('/api/admin/status', {
        headers: { Authorization: `Bearer ${token}` }
      });
      console.log("API Response received:", response.data);
      setStatus(response.data);
    } catch (error) {
      console.error('Failed to fetch status:', error);
      // Log more details about the error
      if (error instanceof Error) {
        console.error('Error details:', {
          message: error.message,
          name: error.name,
          stack: error.stack
        });
      }
    }
  };

    fetchStatus();
    const interval = setInterval(fetchStatus, 30000); // Poll every 30s
    return () => clearInterval(interval);
  }, [token, user]);

  if (!token || !user || user.role !== 'admin') {
    return (
      <MainLayout>
        <div className="text-red-600">Not authenticated as admin</div>
      </MainLayout>
    );
  }

  if (!status) {
    return (
      <MainLayout title="System Status">
        <div className="flex items-center justify-center h-64">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-gray-900"></div>
        </div>
      </MainLayout>
    );
  }

  return (
    <MainLayout title="System Status">
      <div className="space-y-8">
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {/* System Status Card */}
          <Card className="p-6">
            <h3 className="text-lg font-bold mb-4">System Resources</h3>
            <div className="space-y-3">
              <div className="flex justify-between items-center">
                <span>CPU Usage:</span>
                <span className={`font-mono ${status.system.cpu_percent > 80 ? 'text-red-600' : 'text-green-600'}`}>
                  {status.system.cpu_percent.toFixed(1)}%
                </span>
              </div>
              <div className="flex justify-between items-center">
                <span>Memory Usage:</span>
                <span className={`font-mono ${status.system.memory_percent > 80 ? 'text-red-600' : 'text-green-600'}`}>
                  {status.system.memory_percent.toFixed(1)}%
                </span>
              </div>
              <div className="flex justify-between items-center">
                <span>Disk Usage:</span>
                <span className={`font-mono ${status.system.disk_percent > 80 ? 'text-red-600' : 'text-green-600'}`}>
                  {status.system.disk_percent.toFixed(1)}%
                </span>
              </div>
              <div className="flex justify-between items-center">
                <span>Load Average:</span>
                <span className="font-mono">
                  {status.system.load_averages['1min'].toFixed(2)} / {' '}
                  {status.system.load_averages['5min'].toFixed(2)} / {' '}
                  {status.system.load_averages['15min'].toFixed(2)}
                </span>
              </div>
            </div>
          </Card>

          {/* Database Status Card */}
          <Card className="p-6">
            <h3 className="text-lg font-bold mb-4">Database Connections</h3>
            <div className="space-y-3">
              <div className="flex justify-between items-center">
                <span>Active:</span>
                <span className="font-mono">{status.database.connections.active}</span>
              </div>
              <div className="flex justify-between items-center">
                <span>Available:</span>
                <span className="font-mono">{status.database.connections.available}</span>
              </div>
              <div className="flex justify-between items-center">
                <span>Total:</span>
                <span className="font-mono">{status.database.connections.total}</span>
              </div>
            </div>
          </Card>

          {/* WebSocket Status Card */}
          <Card className="p-6">
            <h3 className="text-lg font-bold mb-4">WebSocket Connections</h3>
            <div className="space-y-3">
              <div className="flex justify-between items-center">
                <span>Active Connections:</span>
                <span className="font-mono">{status.websockets.current_connections}</span>
              </div>
              <div className="flex justify-between items-center">
                <span>Peak Connections:</span>
                <span className="font-mono">{status.websockets.peak_connections}</span>
              </div>
              <div className="flex justify-between items-center">
                <span>Active Conversations:</span>
                <span className="font-mono">{status.websockets.active_conversations}</span>
              </div>
            </div>
          </Card>

          {/* RAG Storage Status Card */}
          <Card className="p-6">
            <h3 className="text-lg font-bold mb-4">RAG Storage</h3>
            <div className="space-y-3">
              <div className="flex justify-between items-center">
                <span>Total Storage Used:</span>
                <span className="font-mono">{status.rag.storage}</span>
              </div>
              <div className="flex justify-between items-center">
                <span>Active Collections:</span>
                <span className="font-mono">{status.rag.collections}</span>
              </div>
              <div className="flex justify-between items-center">
                <span>Total Documents:</span>
                <span className="font-mono">{status.rag.total_documents}</span>
              </div>
              <div className="flex justify-between items-center">
                <span>Total Users:</span>
                <span className="font-mono">{status.rag.users}</span>
              </div>
            </div>
          </Card>
        </div>

        {/* Auto-refresh notice */}
        <p className="text-sm text-gray-500 text-center">
          Status updates automatically every 30 seconds
        </p>
      </div>
    </MainLayout>
  );
}
