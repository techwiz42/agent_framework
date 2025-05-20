'use client';

import React, { useCallback, useEffect, useState, useMemo, useRef } from 'react';
import { useParams, useRouter, useSearchParams } from 'next/navigation';
import { useAuth } from '@/context/AuthContext';
import { MainLayout } from '@/components/layout/MainLayout';
import { Card, CardContent } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Loader2 } from 'lucide-react';

import { 
  MessageList, 
  MessageInput, 
  TypingIndicator,
  StreamingIndicator
} from './components';
import { 
  useMessageLoader, 
  useWebSocket, 
  useScrollManager,
  useConversation,
  useStreamingTokens
} from './hooks';
import { Message, MessageMetadata } from './types/message.types';
import { TypingStatusMessage, TokenMessage } from './types/websocket.types';
import { participantStorage } from '@/lib/participantStorage';
import { ChevronLeft, UserPlus } from 'lucide-react';
import { useToast } from '@/components/ui/use-toast';
import { conversationService } from '@/services/conversations';

interface TypingState {
  [identifier: string]: {
    isTyping: boolean;
    agentType?: string;
    name?: string;
    email?: string;
    isAgent: boolean;
  };
}

export default function ConversationPage() {
  const params = useParams();
  const router = useRouter();
  const searchParams = useSearchParams();
  const { token, user } = useAuth();
  const { toast } = useToast();
  const conversationId = params.id as string;
  const [typingStates, setTypingStates] = useState<TypingState>({});
  const [hideAwaitingMessage, setHideAwaitingMessage] = useState<boolean>(false);
  const [typingUsers, setTypingUsers] = useState<Set<string>>(new Set());
  const [email, setEmail] = useState('');
  const isPrivacyEnabled: boolean = searchParams.get('privacy') === 'true';
  
  // Streaming tokens handling
  const { streamingState, handleToken, resetStreamingForAgent } = useStreamingTokens();
  
  const messageQueueRef = useRef<Message[]>([]);
  const isProcessingRef = useRef(false);
  const awaitingInputTimeoutRef = useRef<NodeJS.Timeout>();

  const { conversation, error, isLoading } = useConversation(conversationId, token);

  const {
    messages,
    isLoading: messagesLoading,
    addMessage
  } = useMessageLoader({
    conversationId,
    token: token || ''
  });

  const { 
    scrollContainerRef,
    messagesEndRef, 
    scrollToBottom
  } = useScrollManager(messages);
  
  // Auto-scroll when new streaming content arrives
  useEffect(() => {
    // If any agent is actively streaming, scroll to bottom
    const hasActiveStreaming = Object.values(streamingState).some(state => state.active);
    if (hasActiveStreaming) {
      // Use a small delay to allow the DOM to update
      const timeoutId = setTimeout(() => {
        scrollToBottom(false);
      }, 100);
      return () => clearTimeout(timeoutId);
    }
  }, [streamingState, scrollToBottom]);

  useEffect(() => {
    const checkAuth = async () => {
      const participantSession = participantStorage.getSession(conversationId);
      const hasAuth = !!token || !!participantSession;
      if (!hasAuth) {
        router.replace('/login');
      }
    };

    checkAuth();
  }, [conversationId, token, router]);

  const handleAddParticipant = async () => {
    if (!email) {
      toast({
        title: "Invalid Email",
        description: "Please enter a valid email address",
        variant: "destructive"
      });
      return;
    }

    if (!token) {
      toast({
        title: "Authentication Error",
        description: "You must be logged in to add participants",
        variant: "destructive"
      });
      return;
    }

    try {
      const response = await conversationService.addParticipant(conversationId, { email }, token);
    
      toast({
        title: "Participant Management",
        description: response.message,
        variant: response.message.includes('already') ? "default" : undefined
      });
    
      setEmail('');
    } catch (error) {
      toast({
        title: "Add Participant Error",
        description: error instanceof Error 
          ? error.message 
          : "Failed to add participant",
        variant: "destructive"
      });
    }
  };

  const handleMessage = useCallback((message: Message) => {
    if (!message.sender.is_owner) {
      setHideAwaitingMessage(true);
      if (awaitingInputTimeoutRef.current) {
        clearTimeout(awaitingInputTimeoutRef.current);
      }
      
      // When a complete message arrives from an agent, clear any streaming indicators for that agent
      if (message.sender.type === 'agent' && message.sender.name) {
        // Special handling for moderator agent since it might use a synthetic response
        if (message.sender.name.toLowerCase() === 'moderator') {
          // Reset all streaming states as the moderator response completes the collaboration
          Object.keys(streamingState).forEach(agent => {
            resetStreamingForAgent(agent, message.id);
          });
        } else {
          // Just reset the specific agent
          resetStreamingForAgent(message.sender.name, message.id);
        }
        
        // Force a small delay to ensure the UI updates correctly
        setTimeout(() => {
          requestAnimationFrame(() => {
            scrollToBottom(true);
          });
        }, 150);
      }
    } else {
      if (typingUsers.size === 0) {
        setHideAwaitingMessage(false);
      }
    }
    
    messageQueueRef.current.push(message);
    if (!isProcessingRef.current) {
      isProcessingRef.current = true;
      requestAnimationFrame(() => {
        const messagesToAdd = [...messageQueueRef.current];
        messageQueueRef.current = [];
        isProcessingRef.current = false;
        
        messagesToAdd.forEach(msg => {
          addMessage(msg);
        });
        
        scrollToBottom(true);
      });
    }
  }, [addMessage, resetStreamingForAgent, scrollToBottom, typingUsers.size, streamingState]);

  const handleTypingStatus = useCallback((status: TypingStatusMessage) => {
    setTypingUsers(prev => {
      const next = new Set(prev);
      if (status.is_typing) {
        next.add(status.identifier);
        setHideAwaitingMessage(true);
      } else {
        next.delete(status.identifier);
        if (next.size === 0) {
          setHideAwaitingMessage(false);
        }
      }
      return next;
    });

    setTypingStates(prev => {
      const next = { ...prev };
      if (status.is_typing) {
        next[status.identifier] = {
          isTyping: true,
          agentType: status.agent_type,
          name: status.name,
          email: status.email,
          isAgent: !!status.agent_type
        };
      } else {
        delete next[status.identifier];
      }
      return next;
    });
  }, []);

  // Handle streaming tokens
  const handleTokenMessage = useCallback((tokenMessage: TokenMessage) => {
    if (tokenMessage.token) {
      handleToken(tokenMessage);
    }
  }, [handleToken]);

  const wsConfig = useMemo(() => ({
    conversationId,
    token,
    userId: user?.id,
    userEmail: user?.email,
    onMessage: handleMessage,
    onTypingStatus: handleTypingStatus,
    onToken: handleTokenMessage
  }), [conversationId, token, user?.id, user?.email, handleMessage, handleTypingStatus, handleTokenMessage]);

  const { sendMessage, sendTypingStatus, isConnected } = useWebSocket(wsConfig);

  if (isLoading || messagesLoading) {
    return (
      <MainLayout>
        <div className="text-center py-8">Loading conversation...</div>
      </MainLayout>
    );
  }

  if (error || !conversation) {
    return (
      <MainLayout>
        <div className="text-red-500 py-8">
          {error || 'Conversation not found'}
        </div>
      </MainLayout>
    );
  }

  return (
    <MainLayout title={conversation.title}>
      <div className="container mx-auto p-4 space-y-4">
       {conversation.owner_id === user?.id && (
        <div className="flex items-center space-x-4 w-full">
          <Button
            variant="outline"
            onClick={() => router.push('/conversations')}
            className="flex items-center"
          >
            <ChevronLeft className="mr-2 h-4 w-4" />
            Back to Conversations
          </Button>

          <div className="flex space-x-2 flex-grow">
            <Input
              type="email"
              placeholder="Enter participant email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              className="flex-grow"
            />
            <Button onClick={handleAddParticipant}>
              <UserPlus className="mr-2 h-4 w-4" />
              Invite Participant
            </Button>
          </div>
        </div>
        )}
        <div className="h-[calc(100vh-200px)]">
          <Card className="h-full">
            <CardContent className="h-full p-0">
              <div className="flex flex-col h-full">
                <div
                  ref={scrollContainerRef}
                  className="flex-1 min-h-0 overflow-y-auto scroll-smooth"
                >
                  <MessageList messages={messages} />
                  <div ref={messagesEndRef} />
                </div>

                <div className="flex-shrink-0 p-4 border-t">
                  {!hideAwaitingMessage && (
                    <div className="text-sm text-gray-500 mb-2 flex items-center">
                      <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                      Awaiting input...
                    </div>
                  )}

                  <TypingIndicator
                    typingStates={typingStates}
                  />
                  
                  {/* Render streaming indicators for each agent that is streaming */}
                  {Object.entries(streamingState).map(([agentType, state]) => (
                    state.active && (
                      <StreamingIndicator
                        key={agentType}
                        agentType={agentType}
                        streamingContent={state.tokens}
                        isActive={state.active}
                      />
                    )
                  ))}
                  
                  <MessageInput
                    onSendMessage={(content: string, metadata?: MessageMetadata) => {
                      console.log('MessageInput sending message:', { content, metadata });
                      sendMessage(content, metadata);
                      requestAnimationFrame(() => scrollToBottom(true));
                    }}
                    onTypingStatus={sendTypingStatus}
                    disabled={!isConnected || (!user && !participantStorage.getSession(conversationId))}
                    conversationId={conversationId}
                    isPrivacyEnabled={isPrivacyEnabled}
                  />
		  </div>
              </div>
            </CardContent>
          </Card>
        </div>
      </div>
    </MainLayout>
  );
}
