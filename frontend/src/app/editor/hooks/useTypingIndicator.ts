// hooks/useTypingIndicator.ts
import { useState, useEffect, useRef, useCallback } from 'react';
import { websocketService } from '@/services/websocket';
import { TypingUser } from '../components/TypingIndicator';
import { TypingStatusMessage } from '@/types/websocket.types';

interface UseTypingIndicatorOptions {
  conversationId?: string;
  currentUserEmail: string;
  isCollaborationEnabled: boolean;
}

export function useTypingIndicator({
  conversationId,
  currentUserEmail,
  isCollaborationEnabled
}: UseTypingIndicatorOptions) {
  // Store typing users with their timestamps
  const [typingUsers, setTypingUsers] = useState<TypingUser[]>([]);
  
  // Track current user's typing status
  const [isTyping, setIsTyping] = useState(false);
  
  // Use a timer to stop typing indicator after user stops typing
  const typingTimerRef = useRef<NodeJS.Timeout | null>(null);
  
  // Track when we last sent a typing indicator to avoid flooding
  const lastTypingEventRef = useRef<number>(0);
  
  // Parse email to extract name
  const parseNameFromEmail = (email: string): string => {
    try {
      const name = email.split('@')[0];
      // Convert john.doe or john_doe to John Doe
      return name
        .replace(/[._]/g, ' ')
        .replace(/\b\w/g, (l) => l.toUpperCase());
    } catch {
      return email;
    }
  };
  
  // Send typing status
  const sendTypingStatus = useCallback((isTyping: boolean) => {
    if (!isCollaborationEnabled || !conversationId) return;
    
    // Rate limit sending typing events (not more than once every 1 second)
    const now = Date.now();
    if (now - lastTypingEventRef.current < 1000 && isTyping) {
      return;
    }
    
    lastTypingEventRef.current = now;
    websocketService.sendTypingStatus(isTyping, currentUserEmail);
  }, [conversationId, currentUserEmail, isCollaborationEnabled]);
  
  // Update typing status when user is typing
  const handleTyping = useCallback(() => {
    const wasTyping = isTyping;
    
    if (!wasTyping) {
      setIsTyping(true);
      sendTypingStatus(true);
    }
    
    // Clear existing timer
    if (typingTimerRef.current) {
      clearTimeout(typingTimerRef.current);
    }
    
    // Set a timer to clear typing status after inactivity
    typingTimerRef.current = setTimeout(() => {
      setIsTyping(false);
      sendTypingStatus(false);
    }, 3000);
  }, [isTyping, sendTypingStatus]);
  
  // Process incoming typing status messages
  const handleTypingStatusMessage = useCallback((message: TypingStatusMessage) => {
    const timestamp = new Date(message.timestamp);
    const typingUserId = message.identifier;
    
    // Skip if this is our own typing status
    if (typingUserId === currentUserEmail) return;
    
    if (message.is_typing) {
      // Add or update typing user
      setTypingUsers(prev => {
        // Check if user is already in the list
        const existingIndex = prev.findIndex(u => u.email === typingUserId);
        
        if (existingIndex >= 0) {
          // Update existing entry
          const updated = [...prev];
          updated[existingIndex] = {
            ...updated[existingIndex],
            timestamp
          };
          return updated;
        } else {
          // Add new entry
          const name = message.participant_name || message.name || parseNameFromEmail(typingUserId);
          return [...prev, { email: typingUserId, name, timestamp }];
        }
      });
    } else {
      // Remove user from typing list
      setTypingUsers(prev => prev.filter(user => user.email !== typingUserId));
    }
  }, [currentUserEmail]);
  
  // Set up event listener for typing
  useEffect(() => {
    if (!isCollaborationEnabled || !conversationId) return;
    
    // Listen for WebSocket messages related to typing status
    const unsubscribe = websocketService.subscribe((message) => {
      if (message.type === 'typing_status') {
        handleTypingStatusMessage(message as TypingStatusMessage);
      }
      return null;
    });
    
    return unsubscribe;
  }, [isCollaborationEnabled, conversationId, handleTypingStatusMessage]);
  
  // Clean up typing indicator timers
  useEffect(() => {
    return () => {
      if (typingTimerRef.current) {
        clearTimeout(typingTimerRef.current);
      }
      
      // Send a final "stopped typing" message when component unmounts
      if (isTyping) {
        sendTypingStatus(false);
      }
    };
  }, [isTyping, sendTypingStatus]);
  
  // Periodically clean up stale typing indicators (older than 5 seconds)
  useEffect(() => {
    if (!isCollaborationEnabled) return;
    
    const interval = setInterval(() => {
      const now = new Date();
      setTypingUsers(prev => 
        prev.filter(user => {
          const age = now.getTime() - user.timestamp.getTime();
          return age < 5000; // Remove if older than 5 seconds
        })
      );
    }, 2000);
    
    return () => clearInterval(interval);
  }, [isCollaborationEnabled]);
  
  return {
    typingUsers,
    isTyping,
    handleTyping
  };
}
