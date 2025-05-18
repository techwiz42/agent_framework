import { useState, useEffect, useCallback, useRef } from 'react';
import { useAuth } from '@/context/AuthContext';
import { v4 as uuidv4 } from 'uuid';

interface WebSocketMessage {
  type: string;
  content?: string;
  id?: string;
  identifier?: string;
  is_owner?: boolean;
  email?: string;
  agent_type?: string;
  timestamp?: string;
  is_typing?: boolean;
  token?: string;
  message_metadata?: any;
}

export const useWebSocket = () => {
  const { user, token } = useAuth();
  const [isConnected, setIsConnected] = useState(false);
  const [lastMessage, setLastMessage] = useState<WebSocketMessage | null>(null);
  const [streamingTokens, setStreamingTokens] = useState('');
  const webSocketRef = useRef<WebSocket | null>(null);
  const conversationIdRef = useRef<string | null>(null);

  // Get WebSocket URL from environment or use default
  const getWebSocketUrl = (conversationId: string) => {
    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    const host = process.env.NEXT_PUBLIC_API_URL || window.location.origin.replace(/^https?:/, '');
    const connectionId = uuidv4();
    
    return `${protocol}//${host}/api/ws/conversations/${conversationId}?token=${encodeURIComponent(token || '')}&connection_id=${connectionId}`;
  };

  // Connect to WebSocket
  const connect = useCallback((conversationId: string) => {
    // Close existing connection if any
    if (webSocketRef.current) {
      webSocketRef.current.close();
      webSocketRef.current = null;
    }

    // Store conversation ID for reconnection
    conversationIdRef.current = conversationId;

    // Create new connection
    const ws = new WebSocket(getWebSocketUrl(conversationId));
    webSocketRef.current = ws;

    ws.onopen = () => {
      console.log('WebSocket connection established');
      setIsConnected(true);
    };

    ws.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data);
        
        // Handle streaming tokens
        if (data.type === 'token') {
          setStreamingTokens(prev => prev + data.token);
          return;
        }
        
        // Handle other message types
        setLastMessage(data);
      } catch (error) {
        console.error('Error parsing WebSocket message:', error);
      }
    };

    ws.onclose = (event) => {
      console.log(`WebSocket connection closed: ${event.code} - ${event.reason}`);
      setIsConnected(false);
      
      // Auto-reconnect if closed unexpectedly
      if (event.code !== 1000 && event.code !== 1001) {
        setTimeout(() => {
          if (conversationIdRef.current) {
            connect(conversationIdRef.current);
          }
        }, 3000); // Reconnect after 3 seconds
      }
    };

    ws.onerror = (error) => {
      console.error('WebSocket error:', error);
    };
  }, [token]);

  // Disconnect WebSocket
  const disconnect = useCallback(() => {
    if (webSocketRef.current) {
      webSocketRef.current.close(1000, 'Client disconnected');
      webSocketRef.current = null;
      setIsConnected(false);
      setStreamingTokens('');
      conversationIdRef.current = null;
    }
  }, []);

  // Clear streaming tokens
  const clearStreamingTokens = useCallback(() => {
    setStreamingTokens('');
  }, []);

  // Send message
  const sendMessage = useCallback((content: string, metadata?: any) => {
    if (webSocketRef.current && webSocketRef.current.readyState === WebSocket.OPEN) {
      const messageData = {
        type: 'message',
        content,
        message_metadata: metadata
      };
      webSocketRef.current.send(JSON.stringify(messageData));
    }
  }, []);

  // Send typing status
  const sendTypingStatus = useCallback((isTyping: boolean) => {
    if (webSocketRef.current && webSocketRef.current.readyState === WebSocket.OPEN) {
      const typingData = {
        type: 'typing_status',
        is_typing: isTyping
      };
      webSocketRef.current.send(JSON.stringify(typingData));
    }
  }, []);

  // Set privacy mode
  const setPrivacy = useCallback((isPrivate: boolean) => {
    if (webSocketRef.current && webSocketRef.current.readyState === WebSocket.OPEN) {
      const privacyData = {
        type: 'set_privacy',
        is_private: isPrivate
      };
      webSocketRef.current.send(JSON.stringify(privacyData));
    }
  }, []);

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      if (webSocketRef.current) {
        webSocketRef.current.close(1000, 'Component unmounted');
        webSocketRef.current = null;
      }
    };
  }, []);

  return {
    isConnected,
    connect,
    disconnect,
    sendMessage,
    sendTypingStatus,
    setPrivacy,
    lastMessage,
    streamingTokens,
    clearStreamingTokens
  };
};