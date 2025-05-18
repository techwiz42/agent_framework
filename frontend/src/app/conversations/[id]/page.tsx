'use client'
import React, { useEffect, useState, useRef } from 'react';
import { useRouter } from 'next/navigation';
import { useAuth } from '@/context/AuthContext';
import MessageList from '@/components/conversations/MessageList';
import MessageInput from '@/components/conversations/MessageInput';
import { getConversation, getConversationMessages } from '@/services/api';
import { useWebSocket } from '@/hooks/useWebSocket';

interface Message {
  id: string;
  content: string;
  created_at: string;
  participant_id?: string;
  agent_id?: string;
  message_info?: {
    participant_name?: string;
    participant_email?: string;
    is_owner?: boolean;
    source?: string;
    file_name?: string;
    file_type?: string;
    programming_language?: string;
  };
}

interface Conversation {
  id: string;
  title: string;
  description?: string;
  participants: any[];
  agents: any[];
}

export default function ConversationPage({ params }: { params: { id: string } }) {
  const { id } = params;
  const router = useRouter();
  const { user, isLoading } = useAuth();
  const [conversation, setConversation] = useState<Conversation | null>(null);
  const [messages, setMessages] = useState<Message[]>([]);
  const [isLoadingData, setIsLoadingData] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  // Real-time typing status tracking
  const [typingUsers, setTypingUsers] = useState<Record<string, { name?: string, timestamp: number }>>({});
  
  // Connect to WebSocket
  const { 
    connect, 
    disconnect, 
    sendMessage, 
    sendTypingStatus, 
    lastMessage,
    streamingTokens, 
    clearStreamingTokens
  } = useWebSocket();

  // Handle incoming WebSocket messages
  useEffect(() => {
    if (lastMessage) {
      if (lastMessage.type === 'message') {
        setMessages(prev => {
          // Check if message already exists
          if (prev.some(msg => msg.id === lastMessage.id)) {
            return prev;
          }
          return [...prev, {
            id: lastMessage.id,
            content: lastMessage.content,
            created_at: new Date(lastMessage.timestamp).toISOString(),
            participant_id: lastMessage.identifier,
            agent_id: lastMessage.agent_type ? lastMessage.identifier : undefined,
            message_info: {
              participant_name: lastMessage.agent_type || lastMessage.name,
              participant_email: lastMessage.email,
              is_owner: lastMessage.is_owner,
              source: lastMessage.agent_type || 'user',
              ...(lastMessage.message_metadata || {})
            }
          }];
        });
        clearStreamingTokens();
      } else if (lastMessage.type === 'typing_status') {
        handleTypingStatus(lastMessage);
      }
    }
  }, [lastMessage, clearStreamingTokens]);

  // Handle typing status updates
  const handleTypingStatus = (data: any) => {
    const { identifier, is_typing, timestamp } = data;
    const now = Date.now();
    
    setTypingUsers(prev => {
      // If user stopped typing or it's the current user, remove from typing list
      if (!is_typing || (user && identifier === user.email)) {
        const { [identifier]: _, ...rest } = prev;
        return rest;
      }
      
      // Otherwise, add/update typing status
      return {
        ...prev,
        [identifier]: { 
          name: data.participant_name || data.agent_type || identifier,
          timestamp: now
        }
      };
    });
  };

  // Clean up expired typing indicators
  useEffect(() => {
    const interval = setInterval(() => {
      const now = Date.now();
      setTypingUsers(prev => {
        const updated = { ...prev };
        let changed = false;
        
        // Remove typing indicators older than 3 seconds
        Object.entries(updated).forEach(([key, value]) => {
          if (now - value.timestamp > 3000) {
            delete updated[key];
            changed = true;
          }
        });
        
        return changed ? updated : prev;
      });
    }, 1000);
    
    return () => clearInterval(interval);
  }, []);

  // Scroll to bottom when messages change
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, streamingTokens]);

  // Load conversation data
  useEffect(() => {
    if (!isLoading && !user) {
      router.push('/login');
      return;
    }

    if (user && id) {
      const loadData = async () => {
        try {
          setIsLoadingData(true);
          setError(null);

          // Fetch conversation details
          const conversationData = await getConversation(id);
          setConversation(conversationData);

          // Fetch messages
          const messagesData = await getConversationMessages(id);
          setMessages(messagesData || []);

          // Connect to WebSocket
          connect(id);
        } catch (err) {
          console.error('Error loading conversation:', err);
          setError('Failed to load conversation data');
        } finally {
          setIsLoadingData(false);
        }
      };

      loadData();
    }

    // Disconnect WebSocket when component unmounts
    return () => {
      disconnect();
    };
  }, [id, user, isLoading, router, connect, disconnect]);

  // Handle message submission
  const handleSendMessage = (content: string, metadata?: any) => {
    if (content.trim()) {
      sendMessage(content, metadata);
    }
  };

  // Handle typing status
  const handleTyping = (isTyping: boolean) => {
    sendTypingStatus(isTyping);
  };

  if (isLoading || isLoadingData) {
    return (
      <div className="flex justify-center items-center min-h-screen">
        <div className="animate-spin rounded-full h-12 w-12 border-t-2 border-b-2 border-blue-500"></div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="container mx-auto px-4 py-8 text-center">
        <div className="bg-red-50 text-red-700 p-4 rounded-md mb-4">
          {error}
        </div>
        <button 
          onClick={() => router.push('/conversations')}
          className="text-blue-600 hover:underline"
        >
          Back to conversations
        </button>
      </div>
    );
  }

  return (
    <div className="flex flex-col h-screen">
      {/* Header */}
      <div className="flex items-center border-b px-4 py-3">
        <div className="flex-1">
          <h1 className="text-xl font-semibold">{conversation?.title}</h1>
          {conversation?.description && (
            <p className="text-sm text-gray-500">{conversation.description}</p>
          )}
        </div>
      </div>

      {/* Messages */}
      <div className="flex-1 overflow-auto p-4">
        <MessageList 
          messages={messages} 
          currentUser={user}
          streamingContent={streamingTokens}
          typingUsers={Object.entries(typingUsers).map(([id, data]) => ({
            id,
            name: data.name || id
          }))}
        />
        <div ref={messagesEndRef} />
      </div>

      {/* Input */}
      <div className="border-t p-4">
        <MessageInput onSendMessage={handleSendMessage} onTyping={handleTyping} />
      </div>
    </div>
  );
}