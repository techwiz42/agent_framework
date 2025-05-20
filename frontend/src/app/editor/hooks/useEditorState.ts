// hooks/useEditorState.ts
import { useState, useEffect, useCallback } from 'react';
import { EditorTab } from '../types';

// Import the EditorMessage type or define it here
export interface EditorMessage {
  id: string;
  type: 'info' | 'warning' | 'error' | 'success';
  content: string;
  timestamp: Date;
}

export function useEditorState(sessionId: string | null) {
  const [tabs, setTabs] = useState<EditorTab[]>([]);
  const [activeTab, setActiveTab] = useState(0);
  const [error, setError] = useState<string | null>(null);
  const [messages, setMessages] = useState<EditorMessage[]>([]);
  
  // Tab operations
  const handleNewTab = useCallback((newTab: EditorTab) => {
    console.log("Processing new tab:", newTab);
    
    // Find if tab already exists with same name
    const existingTabIndex = tabs.findIndex(tab => 
      tab.fileName === newTab.fileName
    );
    
    if (existingTabIndex >= 0) {
      console.log("Updating existing tab at index:", existingTabIndex);
      // Update existing tab
      setTabs(prevTabs => {
        const updatedTabs = [...prevTabs];
        updatedTabs[existingTabIndex] = newTab;
        return updatedTabs;
      });
      // Switch to the existing tab
      setActiveTab(existingTabIndex);
    } else {
      console.log("Adding new tab at index:", tabs.length);
      // Add as new tab
      setTabs(prevTabs => [...prevTabs, newTab]);
      // Switch to the new tab (will be at the end)
      setActiveTab(tabs.length);
    }
  }, [tabs]);
  
  const handleAddTab = () => {
    const newTabName = `Untitled-${tabs.length + 1}.txt`;
    const newTab: EditorTab = {
      content: '',
      fileName: newTabName,
      fileType: 'txt'
    };
    
    setTabs(prevTabs => [...prevTabs, newTab]);
    setActiveTab(tabs.length);
  };
  
  const handleCloseTab = (index: number, e: React.MouseEvent) => {
    e.stopPropagation(); // Prevent tab activation when clicking the X
    
    if (tabs.length <= 1) {
      alert("Cannot close the last tab.");
      return;
    }
    
    setTabs(prevTabs => {
      const newTabs = prevTabs.filter((_, i) => i !== index);
      return newTabs;
    });
    
    // Adjust active tab if needed
    if (activeTab >= index && activeTab > 0) {
      setActiveTab(activeTab - 1);
    }
  };

  const handleRenameTab = (index: number, newName: string) => {
    setTabs(prevTabs => {
      const newTabs = [...prevTabs];
      if (newTabs[index]) {
        // Preserve extension if there was one
        const oldExtension = newTabs[index].fileName.split('.').pop();
        const fileName = newName.includes('.') ? newName : `${newName}.${oldExtension}`;
        newTabs[index].fileName = fileName;
        
        // Update fileType if extension changed
        const newExtension = fileName.split('.').pop()?.toLowerCase() || '';
        if (newExtension !== oldExtension) {
          newTabs[index].fileType = newExtension;
        }
      }
      return newTabs;
    });
  };
  
  const handleTabContentChange = (newContent: string) => {
    setTabs(prevTabs => {
      const newTabs = [...prevTabs];
      if (newTabs[activeTab]) {
        newTabs[activeTab].content = newContent;
      }
      return newTabs;
    });
  };
  
  // Load initial tabs from session
  useEffect(() => {
    console.log('Editor loaded, session ID:', sessionId);
    
    if (!sessionId) {
      setError("No session ID provided");
      return;
    }
    
    try {
      const sessionData = localStorage.getItem(sessionId);
      if (sessionData) {
        const parsed = JSON.parse(sessionData);
        console.log("Parsed session data:", parsed);
        
        if (parsed?.tabs?.length > 0) {
          setTabs(parsed.tabs);
          console.log("Loaded initial tabs:", parsed.tabs);
        } else {
          setError("No valid tabs found in session data");
        }
      } else {
        setError(`No data found for session ID: ${sessionId}`);
      }
    } catch (error) {
      console.error('Failed to load session data:', error);
      setError(`Error: ${error instanceof Error ? error.message : String(error)}`);
    }
  }, [sessionId]);
  
  // Setup message listener
  useEffect(() => {
    const handleMessage = (event: MessageEvent) => {
      // Convert incoming messages to EditorMessage format
      const newMessage: EditorMessage = {
        id: `message-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`,
	type: 'info',
        content: JSON.stringify(event.data),
        timestamp: new Date()
      };
      
      // Record all messages for debugging
      setMessages(prev => [...prev, newMessage]);
      
      console.log("Received message:", event.data);
      
      if (event.data.type === 'ADD_NEW_TAB' && event.data.payload) {
        handleNewTab(event.data.payload);
      }
    };

    // Register message listener
    window.addEventListener('message', handleMessage);
    
    // Notify parent that we're ready to receive messages
    if (window.opener) {
      console.log("Notifying parent window that editor is ready");
      window.opener.postMessage({
        type: 'EDITOR_READY',
        sessionId
      }, window.location.origin);
    }
    
    return () => {
      window.removeEventListener('message', handleMessage);
    };
  }, [sessionId, handleNewTab]);
  
  // Get the current tab
  const getCurrentTab = () => tabs[activeTab] || null;
  
  return {
    tabs,
    activeTab,
    error,
    messages,
    getCurrentTab,
    setTabs,
    setActiveTab,
    handleNewTab,
    handleAddTab,
    handleCloseTab,
    handleRenameTab,
    handleTabContentChange,
  };
}
