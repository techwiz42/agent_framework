'use client';

import { useEffect, useState } from 'react';
import { useAuth } from '@/context/AuthContext';
import { conversationService } from '@/services/conversations';
import { Conversation } from '@/types/conversation';
import { TokenResponse } from '@/types/user.types';
import { useRouter } from 'next/navigation';
import { Button } from '@/components/ui/button';
import { Card, CardContent } from '@/components/ui/card';
import { PrivacyToggle } from '@/components/conversation/PrivacyToggle';
import { Link } from '@/components/ui/link';
import { Plus, Trash2, X } from 'lucide-react';
import { MainLayout } from '@/components/layout/MainLayout';
import { api } from '@/services/api';
import { useToast } from '@/components/ui/use-toast';
import GoogleDriveButton from '@/components/conversation/GoogleDriveButton';
import OneDriveButton from '@/components/conversation/OneDriveButton';
import { TooltipProvider } from "@/components/ui/tooltip";

interface AlertDialogProps {
  isOpen: boolean;
  onClose: () => void;
  onConfirm: () => void;
  title: string;
  description: string;
}

const AlertDialog = ({ 
  isOpen, 
  onClose, 
  onConfirm, 
  title, 
  description 
}: AlertDialogProps) => {
  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black bg-opacity-50">
      <div className="bg-white rounded-lg shadow-xl max-w-sm w-full p-6">
        <div className="flex justify-between items-center mb-4">
          <h2 className="text-xl font-semibold">{title}</h2>
          <button 
            onClick={onClose} 
            className="text-gray-500 hover:text-gray-700"
          >
            <X className="h-5 w-5" />
          </button>
        </div>
        <p className="text-gray-600 mb-6">{description}</p>
        <div className="flex justify-end space-x-2">
          <Button 
            variant="outline" 
            onClick={onClose}
          >
            Cancel
          </Button>
          <Button 
            variant="destructive" 
            onClick={onConfirm}
          >
            Delete Permanently
          </Button>
        </div>
      </div>
    </div>
  );
};

export default function ConversationsPage() {
  const [conversations, setConversations] = useState<Conversation[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [tokenCount, setTokenCount] = useState<number>(0);
  const [deleteDialogId, setDeleteDialogId] = useState<string | null>(null);
  const [isPrivacyEnabled, setIsPrivacyEnabled] = useState(false);
  const { token } = useAuth();
  const router = useRouter();
  const { toast } = useToast();

  useEffect(() => {
    const loadConversations = async () => {
      if (!token) return;
      try {
        const response = await conversationService.getConversations(token);
        setConversations(response?.data?.items ?? []);
        
        try {
          const tokenData = JSON.parse(atob(token.split('.')[1]));
          
          if (tokenData.user_id) {
            const tokenResponse = await api.get<TokenResponse>(
              `/api/users/${tokenData.user_id}/tokens`,
              { headers: { Authorization: `Bearer ${token}` } }
            );
            
            if (tokenResponse?.data) {
              setTokenCount(tokenResponse.data.tokens_remaining);
            }
          }
        } catch (tokenError) {
          console.error('Failed to fetch tokens:', tokenError);
        }
      } catch (error) {
        console.error('Failed to load conversations:', error);
        setConversations([]);
      } finally {
        setIsLoading(false);
      }
    };

    loadConversations();
  }, [token]);

  const handleNewConversation = () => {
    router.push('/conversations/new');
  };

  const handlePrivacyToggle = (enabled: boolean) => {
    setIsPrivacyEnabled(enabled);
  };

  const handleDeleteConversation = async () => {
    if (!deleteDialogId || !token) return;

    try {
      await conversationService.deleteConversation(deleteDialogId, token);
    
      setConversations(prev => 
        prev.filter(conversation => conversation.id !== deleteDialogId)
      );
    
      toast({
        title: 'Conversation Deleted',
        description: 'The conversation has been permanently removed.',
        variant: 'default'
      });

      setDeleteDialogId(null);
    } catch (error) {
      console.error('Failed to delete conversation:', error);
      toast({
        title: 'Error',
        description: 'Failed to delete the conversation',
        variant: 'destructive'
      });
    }
  };

  if (isLoading) {
    return (
      <MainLayout title="Agent Framework">
        <h2 className="text-2xl font-bold text-center mb-4">Your Conversations</h2>
        <div className="text-center py-8">Loading conversations...</div>
      </MainLayout>
    );
  }

  return (
    <MainLayout title="Your Conversations">
      <div className="flex justify-between items-center mb-6">
        <div className="flex gap-4">
          <Button onClick={handleNewConversation} className="bg-green-500 hover:bg-green-600">
            <Plus className="mr-2 h-4 w-4" />
            New Conversation
          </Button>
          <TooltipProvider>
            <div className="flex gap-2">
              <GoogleDriveButton />
              <OneDriveButton />
            </div>
          </TooltipProvider>
        </div>
        <Link 
          href="/billing" 
          className="bg-blue-100 hover:bg-blue-200 text-blue-800 px-4 py-2 rounded-md transition-colors duration-200 flex items-center gap-2 cursor-pointer"
        >
          <span>Tokens Remaining: {tokenCount}</span>
          {tokenCount <= 10000 && (
            <span className="text-sm">
              {tokenCount === 0 ? '(Buy More!)' : '(Running Low - Click to Buy)'}
            </span>
          )}
        </Link>
      </div>

      <div className="grid gap-4">
        {conversations.length === 0 ? (
          <Card>
            <CardContent className="text-center py-8">
              No conversations yet. Start one to begin!
            </CardContent>
          </Card>
        ) : (
          conversations.map((conversation) => (
            <Card 
              key={conversation.id}
              className="cursor-pointer hover:shadow-md transition-shadow relative group"
            >
              <CardContent 
                className="py-4 pr-20 cursor-pointer"
                onClick={() => router.push(`/conversations/${conversation.id}?privacy=${isPrivacyEnabled}`)}
	      >
                <div className="text-sm text-gray-600 mb-2">
                  <div>
                    <span className="font-medium">Participants: </span>
                    {conversation.participants.map(p => p.email).join(', ')}
                  </div>
                  {conversation.agents.length > 0 && (
                    <div>
                      <span className="font-medium">AI Agents: </span>
                      {conversation.agents.map(a => a.agent_type).join(', ')}
                    </div>
                  )}
                </div>
                <h3 className="text-lg font-semibold mb-1">{conversation.title}</h3>
                {conversation.description && (
                  <p className="text-gray-700 mt-2">{conversation.description}</p>
                )}
              </CardContent>
              
              <div className="absolute top-2 right-2 flex items-center space-x-2 opacity-0 group-hover:opacity-100 transition-opacity duration-200">
                <PrivacyToggle 
                  conversationId={conversation.id} 
                  isEnabled={isPrivacyEnabled}
                  onToggle={handlePrivacyToggle}
                />
                <button 
                  className="text-gray-500 hover:text-red-500 p-2 rounded-full transition-colors duration-200"
                  onClick={(e) => {
                    e.stopPropagation();
                    setDeleteDialogId(conversation.id);
                  }}
                >
                  <Trash2 className="h-4 w-4" />
                </button>
              </div>
            </Card>
          ))
        )}
      </div>

      <AlertDialog 
        isOpen={deleteDialogId !== null}
        onClose={() => setDeleteDialogId(null)}
        onConfirm={handleDeleteConversation}
        title="Delete Conversation"
        description="This conversation and all its messages will be permanently deleted. This cannot be undone."
      />
    </MainLayout>
  );
}
