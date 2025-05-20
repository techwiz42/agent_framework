// hooks/useCollaborativeEditor.ts
import { useState, useEffect, useCallback, useRef } from 'react';
import { websocketService } from '@/services/websocket';
import { useToast } from '@/components/ui/use-toast';
import { participantStorage } from '@/lib/participantStorage';
import { EditorTab, CollaborativeEditorState } from '../types';
import { WebSocketMessage, EditorChangeEvent, EditorOpenEvent, EditorCloseEvent } from '@/types/websocket.types';

export function useCollaborativeEditor(
  sessionId: string | null,
  tabs: EditorTab[],
  activeTabIndex: number, 
  conversationId?: string
) {
  const { toast } = useToast();
  const [collaborativeState] = useState<CollaborativeEditorState>({
    sessionId: sessionId || '',
    conversationId: conversationId || '',
    participants: [],
  });
  const [isCollaborationEnabled, setIsCollaborationEnabled] = useState(!!conversationId);
  const [lastChangeBy, setLastChangeBy] = useState<string | null>(null);
  
  // Reference to track if we're currently applying a remote change
  // This prevents infinite loops where applying a remote change triggers a local change event
  const isApplyingRemoteChange = useRef(false);

  // Initialize WebSocket connection when collaboration is enabled
  useEffect(() => {
    const initializeWebSocketConnection = async () => {
      if (!conversationId) return;
      
      try {
        // First try to get token from URL parameters (works for both users & participants)
        const urlParams = new URLSearchParams(window.location.search);
        let token = urlParams.get('token');
        let email = urlParams.get('email');
        let name = urlParams.get('name');
        
        // If URL has token, store it in participantStorage (for both users & participants)
        // This ensures the token is available for future use
        if (token && email && conversationId) {
          console.log('Storing token from URL in participantStorage');
          participantStorage.setSession(conversationId, {
            token,
            email,
            name: name || undefined,
            conversationId
          });
        } 
        // If not found in URL, check participantStorage as fallback
        else {
          const participantSession = participantStorage.getSession(conversationId);
          if (participantSession) {
            token = participantSession.token;
            email = participantSession.email;
            name = participantSession.name || null;
            console.log('Using token from participantStorage');
          }
        }

        if (!token) {
          console.error('No token available for WebSocket connection');
          toast({
            title: "Authentication Error",
            description: "Unable to establish collaborative editing session - missing authentication token",
            variant: "destructive",
            duration: 5000
          });
          setIsCollaborationEnabled(false);
          return;
        }
        
        // Now use the token to connect to WebSocket
        const connectionId = `editor-${sessionId || Date.now()}-${Math.random().toString(36).substring(2, 9)}`;
        
        await websocketService.connect(conversationId, token, connectionId);
        console.log('WebSocket connection established for collaborative editing');
        setIsCollaborationEnabled(true);
      } catch (error) {
        console.error('Failed to initialize WebSocket connection:', error);
        setIsCollaborationEnabled(false);
        
        // Show toast to inform user
        toast({
          title: "Collaboration Error",
          description: "Failed to connect to collaborative editing mode. Changes will not be synchronized.",
          variant: "destructive",
          duration: 5000,
        });
      }
    };
    
    if (conversationId) {
      initializeWebSocketConnection();
    }
    
    // Clean up WebSocket connection when unmounting
    return () => {
      // Only disconnect if this was the connection that initialized it
      if (conversationId && websocketService.isConnected) {
        websocketService.disconnect();
      }
    };
  }, [conversationId, sessionId, toast]);

  // Handle incoming editor changes
  const handleIncomingChange = useCallback((message: WebSocketMessage) => {
    if (!isCollaborationEnabled) return null;
    
    // Track sender identity to prevent self-updates
    const currentUserEmail = participantStorage.getSession(collaborativeState.conversationId)?.email;
    let messageSenderEmail: string | undefined;
    
    // Check message type and extract sender email appropriately
    if (message.type === 'editor_change' || message.type === 'editor_open' || message.type === 'editor_close') {
      messageSenderEmail = (message as EditorChangeEvent | EditorOpenEvent | EditorCloseEvent).sender?.email;
    }
    
    // Add debug logging to track message flow
    console.log('Editor message received:', {
      type: message.type,
      fileName: message.type === 'editor_change' ? (message as EditorChangeEvent).fileName : undefined,
      senderEmail: messageSenderEmail,
      currentUserEmail: currentUserEmail,
      isSameSender: currentUserEmail?.toLowerCase() === messageSenderEmail?.toLowerCase()
    });
    
    // Check if this is our own message to prevent loops
    // Only filter out exact matches (case insensitive)
    if (currentUserEmail && 
        messageSenderEmail && 
        currentUserEmail.toLowerCase() === messageSenderEmail.toLowerCase()) {
      console.log('Ignoring own editor message:', message.type);
      return null;
    }
    
    // Handle different message types
    if (message.type === 'editor_change') {
      const changeEvent = message as EditorChangeEvent;
      
      // Find the tab by filename
      const tabIndex = tabs.findIndex(tab => tab.fileName === changeEvent.fileName);
      
      if (tabIndex >= 0) {
        // Only update if the content is different
        if (tabs[tabIndex].content !== changeEvent.content) {
          const senderName = changeEvent.sender?.name || changeEvent.sender?.email || 'Unknown user';
          setLastChangeBy(senderName);
          
          // Set flag to prevent update loops
          isApplyingRemoteChange.current = true;
          
          // Return the updated tab for the parent to update
          return {
            tabIndex,
            newContent: changeEvent.content,
            sender: changeEvent.sender
          };
        }
      }
    } 
    else if (message.type === 'editor_open') {
      const openEvent = message as EditorOpenEvent;
      
      // Find the tab by filename
      const tabIndex = tabs.findIndex(tab => tab.fileName === openEvent.fileName);
      
      // Tab already exists, update it
      if (tabIndex >= 0) {
        // Check if content is different before updating
        if (tabs[tabIndex].content !== openEvent.content) {
          
          // Set flag to prevent update loops
          isApplyingRemoteChange.current = true;
          
          return {
            tabIndex,
            newContent: openEvent.content,
            sender: openEvent.sender
          };
        }
      }
      // Tab doesn't exist yet - we'll need to create it
      // This will need to be handled in the parent component
    }
    else if (message.type === 'editor_close') {
      // Handle editor close event if needed
      const closeEvent = message as EditorCloseEvent;
      if (closeEvent.sender) {
        const senderName = closeEvent.sender.name || closeEvent.sender.email || 'Unknown user';
        console.log(`${senderName} closed ${closeEvent.fileName}`);
        
        // You could notify the user here if desired
        // toast({
        //   title: "Editor Closed",
        //   description: `${senderName} has closed ${closeEvent.fileName}`,
        //   duration: 2000
        // });
      }
    }
    
    return null;
  }, [tabs, isCollaborationEnabled, toast, collaborativeState.conversationId]);

  // Reset the remote change flag after updates
  useEffect(() => {
    if (isApplyingRemoteChange.current) {
      // Use a short timeout to ensure the state update completes
      const timer = setTimeout(() => {
        isApplyingRemoteChange.current = false;
      }, 50);
      
      return () => clearTimeout(timer);
    }
  }, [tabs]);

  // Send editor change to other participants
  const sendEditorChange = useCallback((tab: EditorTab) => {
    if (!isCollaborationEnabled || !conversationId || isApplyingRemoteChange.current) {
      console.log('Not sending editor change - conditions not met:', {
        isCollaborationEnabled,
        hasConversationId: !!conversationId,
        isApplyingRemoteChange: isApplyingRemoteChange.current
      });
      return;
    }
    
    console.log('Sending editor change:', tab.fileName);
    websocketService.sendEditorChange(tab);
  }, [conversationId, isCollaborationEnabled]);

  // Send editor open event when a participant opens the editor
  const sendEditorOpen = useCallback((tab: EditorTab) => {
    if (!isCollaborationEnabled || !conversationId) {
      console.log('Not sending editor open - conditions not met:', {
        isCollaborationEnabled,
        hasConversationId: !!conversationId
      });
      return;
    }
    
    console.log('Sending editor open:', tab.fileName);
    websocketService.sendEditorOpen(tab);
  }, [conversationId, isCollaborationEnabled]);

  // Send editor close event when a participant closes the editor
  const sendEditorClose = useCallback((fileName: string) => {
    if (!isCollaborationEnabled || !conversationId) {
      return;
    }
    
    console.log('Sending editor close:', fileName);
    websocketService.sendEditorClose(fileName);
  }, [conversationId, isCollaborationEnabled]);

  // Subscribe to websocket for editor events when collaboration is enabled
  useEffect(() => {
    if (!isCollaborationEnabled || !conversationId) {
      console.log('Not setting up WebSocket subscription - collaboration disabled or no conversation ID');
      return;
    }

    console.log('Setting up editor websocket subscription');
    
    // Subscribe to websocket messages for editor changes
    const unsubscribe = websocketService.subscribe((message) => {
      // Only process editor-specific messages in this hook
      if (message.type === 'editor_change' || 
          message.type === 'editor_open' || 
          message.type === 'editor_close') {
        return handleIncomingChange(message);
      }
      return null;
    });

    return () => {
      console.log('Cleaning up editor websocket subscription');
      unsubscribe();
    };
  }, [conversationId, isCollaborationEnabled, handleIncomingChange]);

  // Send initial editor state when the component mounts
  useEffect(() => {
    if (!isCollaborationEnabled || !conversationId || !tabs.length) {
      console.log('Not broadcasting initial tab state - conditions not met:', {
        isCollaborationEnabled, 
        hasConversationId: !!conversationId,
        tabsLength: tabs.length
      });
      return;
    }
    
    // Send the current active tab state
    const currentTab = tabs[activeTabIndex];
    if (currentTab) {
      // Small delay to ensure connection is fully established
      const timer = setTimeout(() => {
        console.log('Broadcasting initial tab state:', currentTab.fileName);
        sendEditorOpen(currentTab);
      }, 500);
      
      return () => clearTimeout(timer);
    }
  }, [activeTabIndex, conversationId, isCollaborationEnabled, sendEditorOpen, tabs]);
  
  // Setup closing signal when window closes
  useEffect(() => {
    if (!isCollaborationEnabled || !conversationId || !tabs.length) return;
    
    const currentTab = tabs[activeTabIndex];
    
    const handleBeforeUnload = () => {
      if (currentTab) {
        sendEditorClose(currentTab.fileName);
      }
    };
    
    window.addEventListener('beforeunload', handleBeforeUnload);
    
    return () => {
      window.removeEventListener('beforeunload', handleBeforeUnload);
      if (currentTab) {
        sendEditorClose(currentTab.fileName);
      }
    };
  }, [activeTabIndex, conversationId, isCollaborationEnabled, sendEditorClose, tabs]);

  return {
    collaborativeState,
    isCollaborationEnabled,
    lastChangeBy,
    handleIncomingChange,
    sendEditorChange,
    sendEditorOpen,
    sendEditorClose,
    isApplyingRemoteChange: () => isApplyingRemoteChange.current
  };
}
