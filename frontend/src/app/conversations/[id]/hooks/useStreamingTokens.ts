import { useState, useRef, useCallback, useEffect, useMemo } from 'react';
import { TokenMessage } from '../types/websocket.types';

interface StreamingState {
  [agentType: string]: {
    tokens: string;
    active: boolean;
    lastUpdated: number;
    messageId?: string;
  };
}

export function useStreamingTokens() {
  const [streamingState, setStreamingState] = useState<StreamingState>({});
  const streamBuffer = useRef<{[key: string]: string}>({});
  const streamTimeouts = useRef<{[key: string]: NodeJS.Timeout}>({});
  // Track completed message IDs to prevent duplicate rendering
  const completedMessageIds = useRef<Set<string>>(new Set());
  // Track special agent tokens to correctly identify end of message
  const endTokens = useMemo(() => 
    ['[DONE]', '[END]', '[AGENT_COMPLETE]', '[Synthesizing collaborative response...]'], 
    []); // Added all message patterns

  // Reset the streaming state for a specific agent
  const resetStreamingForAgent = useCallback((agentType: string, messageId?: string) => {
    // Clear any pending timeouts
    if (streamTimeouts.current[agentType]) {
      clearTimeout(streamTimeouts.current[agentType]);
      delete streamTimeouts.current[agentType];
    }
    
    // If we have a message ID, add it to the completed list
    if (messageId) {
      completedMessageIds.current.add(messageId);
    }
    
    // Clear the buffer
    delete streamBuffer.current[agentType];
    
    // Update state
    setStreamingState(prevState => {
      const newState = { ...prevState };
      delete newState[agentType];
      return newState;
    });
  }, []);

  // Clean up streaming state for agents that have stopped sending tokens
  useEffect(() => {
    const cleanupInterval = setInterval(() => {
      const now = Date.now();
      let hasUpdates = false;

      setStreamingState(prevState => {
        const newState = { ...prevState };
        
        // Check for streaming states that haven't been updated in 10 seconds (increased from 3 seconds)
        // to accommodate potential longer gaps between tokens during collaboration
        Object.keys(newState).forEach(agentType => {
          if (newState[agentType].active && now - newState[agentType].lastUpdated > 10000) {
            newState[agentType].active = false;
            hasUpdates = true;
          }
        });
        
        return hasUpdates ? newState : prevState;
      });
    }, 2000); // Check less frequently (increased from 1000ms)

    return () => clearInterval(cleanupInterval);
  }, []);

  // Handle incoming token messages
  const handleToken = useCallback((message: TokenMessage) => {
    const agentType = message.agent_type || 'UNKNOWN';
    const token = message.token || '';
    const messageId = message.message_id;
    
    // If we have a message ID and it's in the completed list, ignore this token
    if (messageId && completedMessageIds.current.has(messageId)) {
      return;
    }
    
    // Check for timeout or error notifications
    if (token.includes('[TIMEOUT]') || token.includes('took too long to respond')) {
      console.log(`Detected timeout notification for ${agentType}`);
      
      // Add a clear timeout message
      streamBuffer.current[agentType] = token;
      
      // Immediately update state with timeout message
      setStreamingState(prevState => ({
        ...prevState,
        [agentType]: {
          tokens: token,
          active: false, // Mark as inactive immediately
          lastUpdated: Date.now(),
          messageId
        }
      }));
      
      // Clear any existing timeout
      if (streamTimeouts.current[agentType]) {
        clearTimeout(streamTimeouts.current[agentType]);
        delete streamTimeouts.current[agentType];
      }
      
      return;
    }
    
    // Check for end of message tokens
    if (endTokens.some(endToken => token.includes(endToken)) || 
        token.includes(`[${agentType} has completed]`)) {
      console.log(`Detected end token for ${agentType}`);
      
      // Format the streamed content before clearing
      if (streamBuffer.current[agentType]) {
        const formattedContent = streamBuffer.current[agentType]
          .replace(/\[\w+ is thinking\.\.\.\]/g, '') // Remove thinking indicators
          .replace(/\[\w+ has completed\]/g, '')     // Remove completion indicators
          .replace(/\[Synthesizing collaborative response\.\.\.\]/g, '') // Remove synthesis indicators
          .replace(/\[TIMEOUT\]/g, '')               // Remove timeout markers
          .replace(/\[ERROR\]/g, '')                 // Remove error markers
          .replace(/\[DONE\]/g, '')                  // Remove done markers
          .replace(/\[END\]/g, '')                   // Remove end markers
          .replace(/\[AGENT_COMPLETE\]/g, '')        // Remove completion markers
          .replace(/\n{3,}/g, '\n\n')                // Normalize excessive newlines
          .trim();
        
        // Update state one last time with formatted content
        setStreamingState(prevState => ({
          ...prevState,
          [agentType]: {
            tokens: formattedContent,
            active: false, // Mark as inactive 
            lastUpdated: Date.now(),
            messageId
          }
        }));
      }
      
      // Clear streaming state for this agent after a short delay to let the UI update
      setTimeout(() => {
        resetStreamingForAgent(agentType, messageId);
      }, 500);
      return;
    }
    
    // Normal token handling
    // Add to buffer first
    streamBuffer.current[agentType] = (streamBuffer.current[agentType] || '') + token;
    
    // Clear any existing timeout
    if (streamTimeouts.current[agentType]) {
      clearTimeout(streamTimeouts.current[agentType]);
    }
    
    // Set a new timeout to update the state
    streamTimeouts.current[agentType] = setTimeout(() => {
      setStreamingState(prevState => ({
        ...prevState,
        [agentType]: {
          tokens: streamBuffer.current[agentType] || '',
          active: true,
          lastUpdated: Date.now(),
          messageId
        }
      }));
    }, 50); // Small delay to batch tokens
  }, [resetStreamingForAgent, endTokens]);

  // Reset all streaming state
  const resetAllStreaming = useCallback(() => {
    // Clear all timeouts
    Object.values(streamTimeouts.current).forEach(timeout => clearTimeout(timeout));
    streamTimeouts.current = {};
    
    // Clear all buffers
    streamBuffer.current = {};
    
    // Reset state
    setStreamingState({});
  }, []);

  return {
    streamingState,
    handleToken,
    resetStreamingForAgent,
    resetAllStreaming
  };
}