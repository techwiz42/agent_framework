'use client';

import { useEffect } from 'react';
import { useParams, useRouter } from 'next/navigation';

// This page handles old-format URLs and redirects to the new format
export default function JoinRedirectPage() {
  const params = useParams();
  const router = useRouter();
  const token = params.token;

  useEffect(() => {
    router.replace(`/join-conversation/${token}`);
  }, [token, router]);

  return (
    <div className="flex items-center justify-center min-h-screen">
      <div className="text-center">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-gray-900 mx-auto"></div>
        <p className="mt-4">Redirecting...</p>
      </div>
    </div>
  );
}
