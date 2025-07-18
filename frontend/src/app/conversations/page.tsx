// src/app/conversations/page.tsx - Updated layout section
'use client';

import React, { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import Link from 'next/link';
import { useAuth } from '@/contexts/AuthContext';
import { conversationService } from '@/services/conversations';
import { Conversation } from '@/types/conversation';
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Loader2, MessageSquare, Plus, Users, Calendar, Trash2, RotateCcw } from 'lucide-react';
import { useToast } from '@/components/ui/use-toast';

export default function ConversationsPage() {
  const router = useRouter();
  const { token, user } = useAuth();
  const { toast } = useToast();
  const [conversations, setConversations] = useState<Conversation[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [deletingId, setDeletingId] = useState<string | null>(null);

  useEffect(() => {
    if (!token) {
      router.push('/login');
      return;
    }

    fetchConversations();
  }, [token, router]);

  // Refresh conversations when the page comes into focus
  useEffect(() => {
    const handleFocus = () => {
      if (token) {
        console.log('Page focused, refreshing conversations...');
        fetchConversations();
      }
    };

    window.addEventListener('focus', handleFocus);
    return () => window.removeEventListener('focus', handleFocus);
  }, [token]);

  const fetchConversations = async () => {
    if (!token) return;

    try {
      setIsLoading(true);
      console.log('Fetching conversations with token:', token?.substring(0, 10) + '...');
      
      const response = await conversationService.getConversations(token);
      console.log('Conversations response:', response);
      
      // Backend returns array directly, not wrapped in { conversations: [...] }
      const conversationsList = Array.isArray(response) ? response : [];
      console.log('Setting conversations:', conversationsList);
      
      // Convert API response to Conversation objects with required fields
      const conversationsWithRequiredFields = conversationsList.map(conv => {
        // Type assertion to any to handle potential property mismatches
        const apiConv = conv as any;
        
        // Create a properly typed Conversation object with all required fields
        const typedConversation: Conversation = {
          id: apiConv.id,
          title: apiConv.title,
          description: apiConv.description,
          created_at: apiConv.created_at,
          updated_at: apiConv.updated_at || apiConv.created_at, // Ensure updated_at is never undefined
          owner_id: apiConv.owner_id || '',
          organization_id: apiConv.organization_id || '',
          is_privacy_enabled: apiConv.is_privacy_enabled || false,
          participant_count: apiConv.participant_count
        };
        return typedConversation;
      });
      
      setConversations(conversationsWithRequiredFields);
    } catch (error) {
      console.error('Error fetching conversations:', error);
      toast({
        title: 'Error',
        description: 'Failed to load conversations',
        variant: 'destructive',
      });
    } finally {
      setIsLoading(false);
    }
  };

  const handleDeleteConversation = async (conversationId: string) => {
    if (!token) return;

    // Simple confirmation using browser's confirm dialog
    if (!window.confirm('Are you sure you want to delete this conversation? This action cannot be undone.')) {
      return;
    }

    try {
      setDeletingId(conversationId);
      await conversationService.deleteConversation(conversationId, token);
      toast({
        title: 'Success',
        description: 'Conversation deleted successfully',
      });
      // Remove from local state
      setConversations(conversations.filter(conv => conv.id !== conversationId));
    } catch (error) {
      console.error('Error deleting conversation:', error);
      toast({
        title: 'Error',
        description: 'Failed to delete conversation',
        variant: 'destructive',
      });
    } finally {
      setDeletingId(null);
    }
  };

  const formatDate = (dateString: string) => {
    const date = new Date(dateString);
    return date.toLocaleDateString('en-US', {
      month: 'short',
      day: 'numeric',
      year: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
    });
  };

  if (isLoading) {
    return (
      <div className="flex items-center justify-center py-8">
        <Loader2 className="h-8 w-8 animate-spin text-gray-500" />
        <span className="ml-2 text-gray-600">Loading conversations...</span>
      </div>
    );
  }

  return (
    <div className="container mx-auto p-4">
      <div className="flex justify-between items-center mb-6">
        <div>
          <h1 className="text-3xl font-bold">{user?.username || 'My'} Conversations</h1>
          <p className="text-sm text-gray-500 mt-1">
            {conversations.length} conversation{conversations.length !== 1 ? 's' : ''} found
          </p>
        </div>
        <div className="flex gap-2">
          <Button 
            onClick={fetchConversations}
            variant="outline"
            className="flex items-center gap-2"
            disabled={isLoading}
          >
            <RotateCcw className={`h-4 w-4 ${isLoading ? 'animate-spin' : ''}`} />
            Refresh
          </Button>
          <Button 
            onClick={() => router.push('/conversations/new')}
            className="flex items-center gap-2"
          >
            <Plus className="h-4 w-4" />
            New Conversation
          </Button>
        </div>
      </div>

      {conversations.length === 0 ? (
        <Card>
          <CardContent className="text-center py-12">
            <MessageSquare className="h-12 w-12 text-gray-400 mx-auto mb-4" />
            <h3 className="text-lg font-semibold mb-2">No conversations yet</h3>
            <p className="text-gray-600 mb-4">Start a new conversation to get started</p>
            <Button 
              onClick={() => router.push('/conversations/new')}
              className="flex items-center gap-2 mx-auto"
            >
              <Plus className="h-4 w-4" />
              Create Your First Conversation
            </Button>
          </CardContent>
        </Card>
      ) : (
        // CHANGED: Single column layout instead of multi-column grid
        <div className="max-w-4xl mx-auto space-y-4">
          {conversations.map((conversation) => (
            <Card key={conversation.id} className="hover:shadow-lg transition-shadow">
              <CardHeader>
                <div className="flex justify-between items-start">
                  <div className="flex-1">
                    <CardTitle className="text-lg line-clamp-1">
                      {conversation.title}
                    </CardTitle>
                    {conversation.description && (
                      <CardDescription className="mt-1 line-clamp-2">
                        {conversation.description}
                      </CardDescription>
                    )}
                  </div>
                  {conversation.owner_id === user?.id && (
                    <Button
                      variant="ghost"
                      size="sm"
                      onClick={(e) => {
                        e.preventDefault();
                        e.stopPropagation();
                        handleDeleteConversation(conversation.id);
                      }}
                      disabled={deletingId === conversation.id}
                      className="ml-2 text-red-500 hover:text-red-700 hover:bg-red-50"
                    >
                      {deletingId === conversation.id ? (
                        <Loader2 className="h-4 w-4 animate-spin" />
                      ) : (
                        <Trash2 className="h-4 w-4" />
                      )}
                    </Button>
                  )}
                </div>
              </CardHeader>
              <CardContent>
                <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
                  <div className="flex flex-col gap-2 text-sm text-gray-600">
                    <div className="flex items-center gap-2">
                      <Calendar className="h-4 w-4" />
                      <span>{formatDate(conversation.created_at)}</span>
                    </div>
                    {conversation.participant_count !== undefined && (
                      <div className="flex items-center gap-2">
                        <Users className="h-4 w-4" />
                        <span>{conversation.participant_count} participant{conversation.participant_count !== 1 ? 's' : ''}</span>
                      </div>
                    )}
                  </div>
                  <Link href={`/conversations/${conversation.id}`}>
                    <Button variant="outline" className="w-full sm:w-auto">
                      Open Conversation
                    </Button>
                  </Link>
                </div>
              </CardContent>
            </Card>
          ))}
        </div>
      )}
    </div>
  );
}
