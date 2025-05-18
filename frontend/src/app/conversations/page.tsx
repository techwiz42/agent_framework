'use client'
import React, { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import { useAuth } from '@/context/AuthContext';
import Link from 'next/link';
import { Button } from '@/components/ui/button';
import { Plus, MessageCircle, Users, Bot } from 'lucide-react';
import { formatDistanceToNow } from 'date-fns';
import { getConversations } from '@/services/api';

interface Participant {
  email: string;
  name?: string;
}

interface Agent {
  agent_type: string;
}

interface Conversation {
  id: string;
  title: string;
  description?: string;
  updated_at: string;
  created_at: string;
  participants: Participant[];
  agents: Agent[];
}

export default function ConversationsPage() {
  const router = useRouter();
  const { user, isLoading } = useAuth();
  const [conversations, setConversations] = useState<Conversation[]>([]);
  const [isLoadingConversations, setIsLoadingConversations] = useState(true);

  useEffect(() => {
    if (!isLoading && !user) {
      router.push('/login');
    }
  }, [isLoading, user, router]);

  useEffect(() => {
    if (user) {
      const fetchConversations = async () => {
        try {
          setIsLoadingConversations(true);
          const { conversations: fetchedConversations } = await getConversations();
          // Ensure fetched conversations match the required interface with participants and agents
          const typedConversations = (fetchedConversations || []).map(conv => ({
            ...conv,
            participants: conv.participants || [],
            agents: conv.agents || []
          }));
          setConversations(typedConversations);
        } catch (error) {
          console.error('Failed to fetch conversations:', error);
        } finally {
          setIsLoadingConversations(false);
        }
      };

      fetchConversations();
    }
  }, [user]);

  if (isLoading || isLoadingConversations) {
    return (
      <div className="flex justify-center items-center min-h-screen">
        <div className="animate-spin rounded-full h-12 w-12 border-t-2 border-b-2 border-blue-500"></div>
      </div>
    );
  }

  return (
    <div className="container mx-auto px-4 py-8">
      <div className="flex justify-between items-center mb-8">
        <h1 className="text-2xl font-bold">My Conversations</h1>
        <Button
          onClick={() => router.push('/conversations/new')}
          className="flex items-center gap-2"
        >
          <Plus size={16} />
          New Conversation
        </Button>
      </div>

      {conversations.length === 0 ? (
        <div className="text-center py-12 bg-gray-50 rounded-lg border border-gray-200">
          <MessageCircle className="mx-auto h-12 w-12 text-gray-400 mb-4" />
          <h3 className="text-lg font-medium text-gray-900 mb-2">No conversations yet</h3>
          <p className="text-gray-500 mb-6">Start a new conversation with AI agents and teammates</p>
          <Button
            onClick={() => router.push('/conversations/new')}
            className="flex items-center gap-2 mx-auto"
          >
            <Plus size={16} />
            Start Conversation
          </Button>
        </div>
      ) : (
        <div className="grid gap-4">
          {conversations.map((conversation) => (
            <Link href={`/conversations/${conversation.id}`} key={conversation.id}>
              <div className="p-4 border border-gray-200 rounded-lg hover:bg-gray-50 transition-colors">
                <div className="flex justify-between items-start">
                  <h2 className="font-medium text-lg">{conversation.title}</h2>
                  <span className="text-sm text-gray-500">
                    {formatDistanceToNow(new Date(conversation.updated_at), { addSuffix: true })}
                  </span>
                </div>
                
                {conversation.description && (
                  <p className="text-gray-600 mt-1 mb-3 line-clamp-2">{conversation.description}</p>
                )}
                
                <div className="flex flex-wrap gap-4 mt-3">
                  <div className="flex items-center gap-1 text-sm text-gray-500">
                    <Bot size={16} />
                    <span>{conversation.agents.length} Agents</span>
                  </div>
                  <div className="flex items-center gap-1 text-sm text-gray-500">
                    <Users size={16} />
                    <span>{conversation.participants.length} Participants</span>
                  </div>
                </div>
              </div>
            </Link>
          ))}
        </div>
      )}
    </div>
  );
}