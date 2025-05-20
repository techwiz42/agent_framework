'use client';

import React from 'react';
import { useAuth } from '@/context/AuthContext';
import { Button } from '@/components/ui/button';
import { usePathname, useRouter } from 'next/navigation';
import { LogOut } from 'lucide-react';
import Image from 'next/image';

interface MainLayoutProps {
  children: React.ReactNode;
  title?: string;
  hideAuthButtons?: boolean;
}

const MainLayout: React.FC<MainLayoutProps> = ({ 
  children, 
  title, 
  hideAuthButtons = false 
}) => {
  const { user, logout } = useAuth();
  const router = useRouter();
  const pathname = usePathname();

  const isConversationsPage = pathname === '/conversations';
  const isStatusPage = pathname === '/admin/status';
  const isHealthPage = pathname === '/admin/health';

  const handleLogout = () => {
    logout();
    router.push('/login');
  };

  return (
    <div className="min-h-screen bg-gray-50">
      <header className="bg-white shadow-sm">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4">
          <div className="flex justify-between items-center">
            <div className="flex items-center">
              <div className="flex items-center cursor-pointer" onClick={() => router.push('/')}>
                <div className="relative w-8 h-8 mr-2">
                  <Image
                    src="/icons/logo.svg"
                    alt="Agent Framework Logo"
                    width={32}
                    height={32}
                    priority
                  />
                </div>
                <h1 className="text-2xl font-bold text-blue-600">
                  Agent Framework
                </h1>
              </div>
              {title && (
                <>
                  <span className="ml-4 text-gray-500">|</span>
                  <h2 className="ml-4 text-xl text-gray-700">{title}</h2>
                </>
              )}
            </div>

            <div className="flex items-center gap-4">
              {user && (
                <div className="flex gap-2 items-center">
                  {!isConversationsPage && (
                    <Button
                      variant="outline"
                      onClick={() => router.push('/conversations')}
                    >
                      My Conversations
                    </Button>
                  )}
                  
                  {user.role === 'admin' && (
                    <>
                      {!isStatusPage && (
                        <Button
                          variant="outline"
                          onClick={() => router.push('/admin/status')}
                        >
                          System Status
                        </Button>
                      )}
                      {!isHealthPage && (
                        <Button
                          variant="outline"
                          onClick={() => router.push('/admin/health')}
                        >
                          System Health
                        </Button>
                      )}
                    </>
                  )}

                  <Button
                    variant="ghost"
                    onClick={handleLogout}
                    className="ml-2 text-gray-600 hover:text-gray-900"
                  >
                    <LogOut className="h-5 w-5 mr-1" />
                    Logout
                  </Button>
                </div>
              )}

              {!hideAuthButtons && !user && (
                <div className="flex gap-2">
                  <Button
                    variant="ghost"
                    onClick={() => router.push('/login')}
                  >
                    Login
                  </Button>
                  <Button
                    variant="default"
                    onClick={() => router.push('/register')}
                  >
                    Register
                  </Button>
                </div>
              )}
            </div>
          </div>
        </div>
      </header>

      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {children}
      </main>
    </div>
  );
};

export { MainLayout };
