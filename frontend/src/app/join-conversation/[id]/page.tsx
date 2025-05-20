'use client';

import { useEffect, useState } from 'react';
import { useParams, useRouter } from 'next/navigation';
import { MainLayout } from '@/components/layout/MainLayout';
import { Card, CardContent } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { toast } from '@/components/ui/use-toast';
import { participantStorage } from '@/lib/participantStorage';

export default function JoinConversationPage() {
  const params = useParams();
  const router = useRouter();
  const invitationToken = params.id as string;
  const [name, setName] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Check if already joined
  useEffect(() => {
    const allSessions = participantStorage.getAllSessions();
    for (const session of allSessions) {
      if (session.invitationToken === invitationToken) {
        router.replace(`/conversations/${session.conversationId}`);
        return;
      }
    }
  }, [invitationToken, router]);

  const handleJoin = async () => {
    setIsLoading(true);
    setError(null);

    try {
      const response = await fetch('/api/conversations/join', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          invitation_token: invitationToken,
          name: name.trim() || undefined
        })
      });

      if (!response.ok) {
        const data = await response.json();
        throw new Error(data.detail || 'Failed to join conversation');
      }

      const data = await response.json();

      participantStorage.setSession(data.conversation_id, {
        token: data.participant_token,
        conversationId: data.conversation_id,
        name: data.name,
        email: data.email,
        invitationToken
      });

      router.replace(`/conversations/${data.conversation_id}`);

    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to join conversation');
      toast({
        title: "Error",
        description: err instanceof Error ? err.message : 'Failed to join conversation',
        variant: "destructive",
        duration: 5000,
      });
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <MainLayout hideAuthButtons={true}>
      <div className="max-w-md mx-auto mt-8">
        <Card>
          <CardContent className="pt-6">
            <h2 className="text-2xl font-bold mb-4">Join Conversation</h2>

            {error && (
              <div className="bg-red-50 text-red-500 p-3 rounded-md mb-4">
                {error}
              </div>
            )}

            <div className="space-y-4">
              <div>
                <label htmlFor="name" className="block text-sm font-medium text-gray-700 mb-1">
                  Your Name (optional)
                </label>
                <Input
                  id="name"
                  type="text"
                  placeholder="Enter your name"
                  value={name}
                  onChange={(e) => setName(e.target.value)}
                  disabled={isLoading}
                />
              </div>

              <Button
                onClick={handleJoin}
                disabled={isLoading}
                className="w-full"
              >
                {isLoading ? 'Joining...' : 'Join Conversation'}
              </Button>
            </div>
          </CardContent>
        </Card>
      </div>
    </MainLayout>
  );
}
