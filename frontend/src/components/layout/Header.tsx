// src/components/layout/Header.tsx
'use client';

import Link from 'next/link';
import { useAuth } from '@/context/AuthContext';

export function Header() {
  const { user, logout } = useAuth();

  return (
    <header className="bg-white shadow-sm">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4">
        <div className="flex justify-between items-center">
          <Link href="/" className="text-2xl font-bold text-gray-900">
            Agent Framework
          </Link>
          {user && (
            <nav className="flex items-center">
              <button 
                onClick={logout}
                className="text-gray-600 hover:text-gray-900"
              >
                Logout
		</button>
               {user?.role === 'ADMIN' && (
                  <>
                  <Link href="/admin/status">System Status</Link>
                  <Link href="/admin/health">System Health</Link>
                </>
              )}
    	    </nav>
          )}
        </div>
      </div>
    </header>
  );
}
