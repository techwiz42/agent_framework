'use client';

import { useState, useEffect } from 'react';
import { useAuth } from '@/context/AuthContext';
import { useToast } from '@/components/ui/use-toast';
import { MainLayout } from '@/components/layout/MainLayout';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { api } from '@/services/api';

interface Product {
  id: string;
  name: string;
  tokens: number;
  price: number;
  description: string;
}

interface Subscription {
  id: string;
  name: string;
  tokens_per_month: number;
  price: number;
  description: string;
}

interface ProductsResponse {
  one_time: Product[];
  subscriptions: Subscription[];
}

interface CheckoutResponse {
  checkout_url: string;
}

export default function BillingPage() {
  const [products, setProducts] = useState<ProductsResponse>({
    one_time: [],
    subscriptions: []
  });
  const [isLoading, setIsLoading] = useState(false);
  const { token } = useAuth();
  const { toast } = useToast();

  useEffect(() => {
    const fetchProducts = async () => {
      try {
        const response = await api.get<ProductsResponse>('/api/billing/products', {
          headers: { Authorization: `Bearer ${token}` }
        });
        setProducts(response.data);
      } catch (error) {
        toast({
          title: "Error",
          description: error instanceof Error ? error.message : "Failed to load products",
          variant: "destructive"
        });
      }
    };

    fetchProducts();
  }, [token, toast]);

  const handlePurchase = async (productId: string) => {
    try {
      setIsLoading(true);
      const response = await api.post<CheckoutResponse>(
        '/api/billing/create-checkout-session',
        { product_key: productId },
        { headers: { Authorization: `Bearer ${token}` }}
      );

      // Redirect to Stripe Checkout
      window.location.href = response.data.checkout_url;
    } catch (error) {
      toast({
        title: "Error",
        description: error instanceof Error ? error.message : "Failed to initiate purchase",
        variant: "destructive"
      });
    } finally {
      setIsLoading(false);
    }
  };

  const handleManageSubscription = async () => {
    try {
      setIsLoading(true);
      const response = await api.post<CheckoutResponse>(
        '/api/billing/create-portal-session',
        {},
        { headers: { Authorization: `Bearer ${token}` }}
      );

      // Redirect to Stripe Customer Portal
      window.location.href = response.data.checkout_url;
    } catch (error) {
      toast({
        title: "Error",
        description: error instanceof Error ? error.message : "Failed to open subscription management",
        variant: "destructive"
      });
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <MainLayout title="Purchase Tokens">
      <div className="container mx-auto p-4 space-y-8">
        {/* One-time Purchases */}
        <div>
          <h2 className="text-2xl font-bold mb-4">One-time Token Packages</h2>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            {products.one_time.map((product) => (
              <Card key={product.id}>
                <CardHeader>
                  <CardTitle>{product.name}</CardTitle>
                </CardHeader>
                <CardContent>
                  <p className="text-2xl font-bold mb-2">${product.price}</p>
                  <p className="text-gray-600 mb-4">{product.description}</p>
                  <p className="text-sm text-gray-500 mb-4">
                    {product.tokens.toLocaleString()} tokens
                  </p>
                  <Button
                    onClick={() => handlePurchase(product.id)}
                    disabled={isLoading}
                    className="w-full"
                  >
                    {isLoading ? 'Processing...' : 'Purchase'}
                  </Button>
                </CardContent>
              </Card>
            ))}
          </div>
        </div>

        {/* Subscriptions */}
        <div>
          <h2 className="text-2xl font-bold mb-4">Monthly Subscriptions</h2>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {products.subscriptions.map((subscription) => (
              <Card key={subscription.id}>
                <CardHeader>
                  <CardTitle>{subscription.name}</CardTitle>
                </CardHeader>
                <CardContent>
                  <p className="text-2xl font-bold mb-2">
                    ${subscription.price}/month
                  </p>
                  <p className="text-gray-600 mb-4">{subscription.description}</p>
                  <p className="text-sm text-gray-500 mb-4">
                    {subscription.tokens_per_month.toLocaleString()} tokens monthly
                  </p>
                  <Button
                    onClick={() => handlePurchase(subscription.id)}
                    disabled={isLoading}
                    className="w-full"
                  >
                    {isLoading ? 'Processing...' : 'Subscribe'}
                  </Button>
                </CardContent>
              </Card>
            ))}
          </div>
        </div>

        {/* Subscription Management */}
        <div className="mt-8 text-center">
          <Button
            onClick={handleManageSubscription}
            variant="outline"
            className="bg-gray-100 hover:bg-gray-200"
            disabled={isLoading}
          >
            {isLoading ? 'Loading...' : 'Manage Existing Subscription'}
          </Button>
        </div>

        {/* Custom Programming Note */}
        <div className="mt-12 text-center border-t pt-8">
          <p className="text-gray-800 text-lg font-semibold">
            Agent Framework can provide custom programming for all your AI Agent needs.{' '}
            <a 
              href="mailto:pete@agentframework.ai"
              className="text-blue-600 hover:text-blue-800 font-bold underline"
            >
              Contact us
            </a>
          </p>
        </div>
      </div>
    </MainLayout>
  );
}
