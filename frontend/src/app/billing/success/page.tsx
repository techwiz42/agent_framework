'use client';

import { useSearchParams } from 'next/navigation';
import { useEffect, useState, useRef } from 'react';
import { useRouter } from 'next/navigation';
import { api } from '@/services/api';
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { useAuth } from '@/context/AuthContext';

interface PaymentDetails {
  status: string;
  message: string;
  tokens_purchased: number;
  product_name: string;
  user_id: string;
}

export default function PaymentSuccessPage() {
  const searchParams = useSearchParams();
  const router = useRouter();
  const { token } = useAuth();
  const [paymentDetails, setPaymentDetails] = useState<PaymentDetails | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  
  // Use a ref to track if we've already made the API call
  const verificationInProgress = useRef(false);

  const session_id = searchParams.get('session_id');

  useEffect(() => {
    console.log('Effect triggered');
    console.log('Session ID:', session_id);
    console.log('Token:', token);
    console.log('Verification in progress:', verificationInProgress.current);

    const verifyPayment = async () => {
      // Prevent multiple simultaneous calls
      if (verificationInProgress.current || !session_id) return;

      try {
        verificationInProgress.current = true;
        console.log('Starting payment verification');

        const response = await api.get<PaymentDetails>('billing/success', {
          headers: { 
            Authorization: `Bearer ${token}`,
          },
          params: new URLSearchParams({ session_id })
        });

        console.log('Payment verification response:', response.data);
        setPaymentDetails(response.data);
      } catch (err) {
        console.error('Payment verification error:', err);
        setError('Unable to verify payment');
      } finally {
        setIsLoading(false);
        verificationInProgress.current = false;
      }
    };

    verifyPayment();
  }, [session_id, token]);

  if (error) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gray-100">
        <Card className="max-w-md w-full">
          <CardHeader>
            <CardTitle className="text-red-500">Payment Verification Failed</CardTitle>
          </CardHeader>
          <CardContent>
            <p>{error}</p>
            <Button 
              onClick={() => router.push('/billing')}
              className="mt-4 w-full"
            >
              Return to Billing
            </Button>
          </CardContent>
        </Card>
      </div>
    );
  }

  if (isLoading || !paymentDetails) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gray-100">
        <Card className="max-w-md w-full">
          <CardContent className="text-center py-6">
            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-gray-900 mx-auto mb-4" />
            <p>Verifying your payment...</p>
          </CardContent>
        </Card>
      </div>
    );
  }

  return (
    <div className="min-h-screen flex items-center justify-center bg-gray-100">
      <Card className="max-w-md w-full">
        <CardHeader>
          <CardTitle className="text-center">
            <svg 
              className="mx-auto h-12 w-12 text-green-500 mb-4" 
              fill="none" 
              stroke="currentColor" 
              viewBox="0 0 24 24"
            >
              <path 
                strokeLinecap="round" 
                strokeLinejoin="round" 
                strokeWidth={2} 
                d="M5 13l4 4L19 7" 
              />
            </svg>
            Payment Successful!
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <div>
            <p className="text-gray-600 mb-1">Product Purchased:</p>
            <p className="font-semibold">{paymentDetails.product_name}</p>
          </div>
          
          <div>
            <p className="text-gray-600 mb-1">Tokens Added:</p>
            <p className="font-semibold">{paymentDetails.tokens_purchased.toLocaleString()}</p>
          </div>
          
          <Button 
            onClick={() => router.push('/conversations')}
            className="w-full"
          >
            Continue to Conversations
          </Button>
        </CardContent>
      </Card>
    </div>
  );
}
