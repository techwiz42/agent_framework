'use client';

import { useEffect, useState } from 'react';
import { useRouter, useParams } from 'next/navigation';
import { Card, CardContent } from "@/components/ui/card";
import { MainLayout } from '@/components/layout/MainLayout';
import { api } from '@/services/api';
import { EmailVerificationResponse } from '@/types';

export default function VerifyEmailPage() {
  const [status, setStatus] = useState<'verifying' | 'success' | 'error'>('verifying');
  const [message, setMessage] = useState('Verifying your email...');
  const router = useRouter();
  const params = useParams();
  const token = params.token as string;

  useEffect(() => {
    const verifyEmail = async () => {
      try {
        const response = await api.get<EmailVerificationResponse>(`/api/auth/verify-email/${token}`);
        if (response?.data) {
          setStatus('success');
          setMessage(response.data.message);
        
          // Redirect to login after 3 seconds
          setTimeout(() => {
            router.push('/login');
         }, 3000);
        } else {
          setStatus('error');
          setMessage('Invalid response from server');
        }
      } catch (err) {
        setStatus('error');
        if (err instanceof Error) {
          setMessage(err.message);
        } else {
          setMessage('Verification failed. Please try again or contact support.');
        }
      }
    };

    verifyEmail();
  }, [token, router]);

  return (
    <MainLayout>
      <div className="max-w-md mx-auto mt-8">
        <Card>
          <CardContent className="pt-6">
            <div className={`text-center ${
              status === 'error' ? 'text-red-600' : 
              status === 'success' ? 'text-green-600' : 
              'text-gray-600'
            }`}>
              <h2 className="text-2xl font-bold mb-4">Email Verification</h2>
              <p>{message}</p>
              {status === 'success' && (
                <p className="mt-4 text-sm text-gray-500">
                  Redirecting to login page...
                </p>
              )}
            </div>
          </CardContent>
        </Card>
      </div>
    </MainLayout>
  );
}
