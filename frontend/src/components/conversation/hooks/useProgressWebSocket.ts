// src/hooks/useProgressWebSocket.ts
import { useState, useEffect } from 'react';

interface ProgressDetails {
  totalFiles: number;
  processedFiles: number;
  currentFile: string;
  totalCharacters: number;
  processedCharacters: number;
  status: 'idle' | 'started' | 'completed' | 'error';
  errors?: string[];
}

export const useProgressWebSocket = (threadId: string) => {
  const [progressDetails, setProgressDetails] = useState<ProgressDetails>({
    totalFiles: 0,
    processedFiles: 0,
    currentFile: '',
    totalCharacters: 0,
    processedCharacters: 0,
    status: 'idle',
    errors: []
  });

  const [socket, setSocket] = useState<WebSocket | null>(null);

  useEffect(() => {
    if (!threadId) return;

    // Create WebSocket connection
    const newSocket = new WebSocket(`wss://your-domain.com/ws/progress/${threadId}`);

    newSocket.onopen = () => {
      console.log('WebSocket connection established');
    };

    newSocket.onmessage = (event) => {
      const data = JSON.parse(event.data);
      
      switch(data.type) {
        case 'progress_start':
          setProgressDetails(prev => ({
            ...prev,
            totalFiles: data.total_files,
            status: 'started'
          }));
          break;

        case 'file_processing_start':
          setProgressDetails(prev => ({
            ...prev,
            currentFile: data.filename
          }));
          break;

        case 'chunk_processed':
          setProgressDetails(prev => ({
            ...prev,
            processedCharacters: data.processed_characters,
            totalCharacters: data.total_characters
          }));
          break;

        case 'file_processing_complete':
          setProgressDetails(prev => ({
            ...prev,
            processedFiles: data.processed_files,
            currentFile: ''
          }));
          break;

        case 'progress_complete':
          setProgressDetails(prev => ({
            ...prev,
            status: 'completed'
          }));
          break;

        case 'file_processing_failed':
          setProgressDetails(prev => ({
            ...prev,
            status: 'error',
            errors: [...(prev.errors || []), data.error]
          }));
          break;
      }
    };

    newSocket.onerror = (error) => {
      console.error('WebSocket error:', error);
      setProgressDetails(prev => ({
        ...prev,
        status: 'error'
      }));
    };

    newSocket.onclose = () => {
      console.log('WebSocket connection closed');
    };

    setSocket(newSocket);

    // Cleanup on unmount or thread change
    return () => {
      newSocket.close();
    };
  }, [threadId]);

  return { progressDetails, socket };
};
