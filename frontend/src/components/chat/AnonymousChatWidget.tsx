// src/components/chat/AnonymousChatWidget.tsx
import React, { useState, useEffect, useRef } from 'react';
import { MessageCircle, X, Send, Bot, Minimize2, Maximize2, Mic, MicOff } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import SimpleBadge from '@/components/ui/SimpleBadge';
import { formatDistanceToNow } from 'date-fns';
import { v4 as uuidv4 } from 'uuid';

// Define message type
interface ChatMessage {
  id: string;
  content: string;
  sender: 'user' | 'agent';
  timestamp: Date;
  agentType?: string;
}

// Function to format text with proper paragraphs
const formatAgentResponse = (text: string): string => {
  if (!text) return '';
  
  // Ensure double line breaks are preserved as paragraph breaks
  const formattedText = text
    .replace(/\n\s*\n/g, '\n\n')  // Normalize multiple line breaks to exactly two
    .replace(/\n\n+/g, '\n\n');   // Replace 3+ line breaks with just two
    
  return formattedText;
};

// Main component
export const AnonymousChatWidget: React.FC = () => {
  // State
  const [isOpen, setIsOpen] = useState(false);
  const [isMinimized, setIsMinimized] = useState(false);
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [inputValue, setInputValue] = useState('');
  const [isTyping, setIsTyping] = useState(false);
  const [isConnected, setIsConnected] = useState(true);
  const [sessionId] = useState(uuidv4());
  
  // Speech-to-text states
  const [isRecording, setIsRecording] = useState(false);
  const [recordingStatus, setRecordingStatus] = useState('');
  
  // Speech-to-text refs
  const mediaRecorderRef = useRef<MediaRecorder | null>(null);
  const audioChunksRef = useRef<Blob[]>([]);
  
  // Using CUSTOMERSERVICE agent
  const agentType = 'CUSTOMERSERVICE';
  const agentDisplayName = 'Customer Support';
  
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const wsRef = useRef<WebSocket | null>(null);

  // Connect to WebSocket
  useEffect(() => {
    if (isOpen && !wsRef.current) {
      // Initialize as connected to enable the input field while we attempt connection
      setIsConnected(true);
      
      // Determine the WebSocket URL
      // First try environment variable, fallback to relative URL, then absolute URL
      let wsUrl;
      if (process.env.NEXT_PUBLIC_WS_URL) {
        wsUrl = `${process.env.NEXT_PUBLIC_WS_URL}/anonymous/${agentType}?session_id=${sessionId}&connection_id=${sessionId}`;
      } else {
        // Try to construct a relative WebSocket URL based on current location
        const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
        const host = window.location.host;
        wsUrl = `${protocol}//${host}/ws/anonymous/${agentType}?session_id=${sessionId}&connection_id=${sessionId}`;
      }
      
      console.log('Connecting to WebSocket:', wsUrl);
      
      try {
        const ws = new WebSocket(wsUrl);
        
        ws.onopen = () => {
          setIsConnected(true);
          // Add welcome message on connection
          const welcomeMessage = "Hello! I'm here to help with any customer service questions you might have. How can I assist you today?";
            
          setTimeout(() => {
            setMessages([{
              id: uuidv4(),
              content: welcomeMessage,
              sender: 'agent' as const,
              timestamp: new Date(),
              agentType: agentType
            }]);
          }, 500);
        };
        
        ws.onmessage = (event) => {
          try {
            const data = JSON.parse(event.data);
            
            if (data.type === 'message') {
              setMessages(prev => [...prev, {
                id: data.id || uuidv4(),
                content: formatAgentResponse(data.content),
                sender: 'agent' as const,
                timestamp: new Date(data.timestamp),
                agentType: data.agent_type || agentType
              }]);
              setIsTyping(false);
            } else if (data.type === 'token') {
              // Handle streaming tokens
              setMessages(prev => {
                const lastMessage = prev[prev.length - 1];
                
                if (lastMessage && lastMessage.sender === 'agent' && !lastMessage.id.includes('complete')) {
                  const updatedMessages = [...prev];
                  updatedMessages[updatedMessages.length - 1] = {
                    ...lastMessage,
                    content: formatAgentResponse(lastMessage.content + data.token)
                  };
                  return updatedMessages;
                } else {
                  return [...prev, {
                    id: `streaming-${uuidv4()}`,
                    content: data.token,
                    sender: 'agent' as const,
                    timestamp: new Date(),
                    agentType: agentType
                  }];
                }
              });
            } else if (data.type === 'typing_status') {
              setIsTyping(data.is_typing);
            }
          } catch (error) {
            console.error('Error processing message:', error);
          }
        };
        
        ws.onerror = (error) => {
          console.error('WebSocket error:', error);
          // Keep input enabled regardless of connection status
          // setIsConnected(false);
        };
        
        ws.onclose = () => {
          console.log('WebSocket connection closed');
          // Keep input enabled regardless of connection status
          // setIsConnected(false);
          wsRef.current = null;
        };
        
        wsRef.current = ws;
      } catch (error) {
        console.error('Failed to establish WebSocket connection:', error);
        // Keep input enabled anyway - we don't want to block the user from typing
        // setIsConnected(false);
      }
      
      // Cleanup on unmount or when closing chat
      return () => {
        if (wsRef.current) {
          wsRef.current.close();
          wsRef.current = null;
        }
        
        // Also stop recording if active
        stopRecording();
      };
    }
  }, [isOpen, sessionId, agentType]);

  // Auto-scroll to bottom when new messages arrive
  useEffect(() => {
    if (messagesEndRef.current) {
      messagesEndRef.current.scrollIntoView({ behavior: 'smooth' });
    }
  }, [messages]);

  // Handle sending a message
  const handleSendMessage = () => {
    if (!inputValue.trim()) return;
    
    const newMessage = {
      id: uuidv4(),
      content: inputValue,
      sender: 'user' as const,
      timestamp: new Date()
    };
    
    setMessages(prev => [...prev, newMessage]);
    
    // Send to WebSocket if connected
    if (wsRef.current) {
      try {
        wsRef.current.send(JSON.stringify({
          type: 'message',
          content: inputValue,
          timestamp: new Date().toISOString()
        }));
      } catch (error) {
        console.error('Failed to send message:', error);
        // Add a system message about connection issues
        setTimeout(() => {
          setMessages(prev => [...prev, {
            id: uuidv4(),
            content: "There seems to be a connection issue. Your message may not have been received. Please try again later.",
            sender: 'agent' as const,
            timestamp: new Date(),
            agentType: agentType
          }]);
        }, 1000);
      }
    } else {
      // If not connected, add a message indicating the connection issue
      setTimeout(() => {
        setMessages(prev => [...prev, {
          id: uuidv4(),
          content: "Sorry, I'm having trouble connecting to the server. Your message couldn't be sent. Please try again later.",
          sender: 'agent' as const,
          timestamp: new Date(),
          agentType: agentType
        }]);
      }, 1000);
    }
    
    setInputValue('');
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSendMessage();
    }
  };
  
  // Speech-to-text functions
  const startRecording = async () => {
    try {
      setRecordingStatus('Requesting microphone access...');
      
      // Check if mediaDevices is supported
      if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) {
        throw new Error('Browser does not support microphone access');
      }
      
      // Show warning for non-secure context but still try to access microphone
      // Note: This will likely fail in most browsers but we'll try anyway
      if (window.location.protocol !== 'https:' && window.location.hostname !== 'localhost' && window.location.hostname !== '127.0.0.1') {
        console.warn('Warning: Attempting to access microphone on non-secure origin. This may fail in most browsers.');
        setRecordingStatus('Warning: Non-secure connection may prevent microphone access');
      }
      
      // Request microphone access with explicit constraints
      const stream = await navigator.mediaDevices.getUserMedia({
        audio: {
          echoCancellation: true,
          noiseSuppression: true,
          autoGainControl: true
        }
      });
      
      // If we get here, we successfully accessed the microphone
      
      // Set up the MediaRecorder with the audio stream
      // Check for browser compatibility with different MIME types
      let mimeType = 'audio/webm';
      if (MediaRecorder.isTypeSupported('audio/webm;codecs=opus')) {
        mimeType = 'audio/webm;codecs=opus';
      }
      
      const mediaRecorder = new MediaRecorder(stream, { mimeType });
      mediaRecorderRef.current = mediaRecorder;
      audioChunksRef.current = [];
      
      // Event handler for data available
      mediaRecorder.ondataavailable = (event) => {
        if (event.data.size > 0) {
          audioChunksRef.current.push(event.data);
        }
      };
      
      // Event handler for recording stop
      mediaRecorder.onstop = async () => {
        setRecordingStatus('Processing audio...');
        
        // Create a blob from the recorded audio chunks
        const audioBlob = new Blob(audioChunksRef.current, { type: mimeType });
        
        // Send the audio blob to the backend for speech-to-text processing
        await sendAudioForSTT(audioBlob);
        
        // Clean up
        stream.getTracks().forEach(track => track.stop());
        setRecordingStatus('');
      };
      
      // Start recording
      mediaRecorder.start(1000); // Collect data every second
      setIsRecording(true);
      setRecordingStatus('Recording audio...');
    } catch (error: any) {
      console.error('Error starting recording:', error);
      setIsRecording(false);
      
      // Provide more helpful error messages based on the error
      if (error.name === 'NotAllowedError') {
        if (window.location.protocol !== 'https:' && window.location.hostname !== 'localhost') {
          setRecordingStatus('Microphone access denied: HTTP connections require HTTPS for microphone access. Try one of these options:\n1. Use HTTPS\n2. Deploy to localhost\n3. Use a service like ngrok');
        } else {
          setRecordingStatus('Microphone access denied. Please check your browser permissions.');
        }
      } else if (error.name === 'NotFoundError') {
        setRecordingStatus('No microphone found. Please connect a microphone and try again.');
      } else if (error.name === 'NotReadableError' || error.name === 'AbortError') {
        setRecordingStatus('Cannot access microphone. It may be in use by another application.');
      } else if (error.message) {
        setRecordingStatus(`Error: ${error.message}`);
      } else {
        setRecordingStatus('Failed to access microphone');
      }
      
      // Show error message for longer since this is important
      setTimeout(() => {
        setRecordingStatus('');
      }, 10000);
    }
  };
  
  const stopRecording = () => {
    if (mediaRecorderRef.current && isRecording) {
      mediaRecorderRef.current.stop();
      setIsRecording(false);
    }
  };
  
  const sendAudioForSTT = async (audioBlob: Blob) => {
    try {
      // Log the audio blob details for debugging
      console.log('Audio blob:', audioBlob.type, audioBlob.size, 'bytes');
      
      // Create form data to send the audio file
      const formData = new FormData();
      formData.append('audio_file', audioBlob, 'recording.webm');
      formData.append('language_code', 'en-US');
      
      // Don't specify sample rate for WEBM files (let Google auto-detect)
      // This matches your backend implementation for WEBM files
      
      // Determine the API endpoint (use environment variable or fallback)
      const apiUrl = process.env.NEXT_PUBLIC_API_URL 
        ? `${process.env.NEXT_PUBLIC_API_URL}/speech-to-text`
        : '/api/speech-to-text'; // Fallback to relative URL
      
      console.log('Sending audio to:', apiUrl);
      
      // Send the request to the backend
      const response = await fetch(apiUrl, {
        method: 'POST',
        body: formData,
      });
      
      if (!response.ok) {
        const errorText = await response.text();
        console.error('Server error:', response.status, errorText);
        throw new Error(`Server responded with status ${response.status}: ${errorText}`);
      }
      
      const data = await response.json();
      console.log('STT response:', data);
      
      if (data.success && data.transcript) {
        // Set the transcribed text as the input value
        setInputValue(prev => prev + (prev ? ' ' : '') + data.transcript);
        setRecordingStatus('');
      } else if (data.error) {
        console.error('STT error:', data.error, data.details || '');
        
        // Check for common Google STT errors
        if (data.details && data.details.includes('sample_rate_hertz')) {
          setRecordingStatus('Audio format error: sample rate mismatch');
        } else if (data.error.includes('No speech detected')) {
          setRecordingStatus('No speech detected. Please try again.');
        } else {
          setRecordingStatus(`Error: ${data.error}`);
        }
        
        // Clear error status after a few seconds
        setTimeout(() => {
          setRecordingStatus('');
        }, 5000);
      } else {
        setRecordingStatus('No speech detected');
        
        // Clear status after a few seconds
        setTimeout(() => {
          setRecordingStatus('');
        }, 5000);
      }
    } catch (error: any) {
      console.error('Error sending audio for STT:', error);
      
      // Provide more user-friendly error message
      if (error.message && error.message.includes('Failed to fetch')) {
        setRecordingStatus('Network error: Please check your connection');
      } else if (error.message) {
        setRecordingStatus(error.message);
      } else {
        setRecordingStatus('Failed to process speech');
      }
      
      // Clear error status after a few seconds
      setTimeout(() => {
        setRecordingStatus('');
      }, 5000);
    }
  };

  // Toggle chat open/closed state
  const toggleChat = () => {
    setIsOpen(!isOpen);
    if (!isOpen) {
      setIsMinimized(false);
    }
  };

  // Toggle minimized state
  const toggleMinimize = () => {
    setIsMinimized(!isMinimized);
  };

  // Only show the chat button when chat is closed
  if (!isOpen) {
    return (
      <div className="fixed bottom-4 right-4 flex flex-col items-end gap-2 z-40">
        <div className="bg-blue-600 text-white text-sm rounded-lg shadow-md px-3 py-1 mr-2 relative after:content-[''] after:absolute after:top-full after:right-4 after:border-8 after:border-transparent after:border-t-blue-600">
          Chat with AI
        </div>
        <Button 
          onClick={toggleChat}
          className="rounded-full w-16 h-16 bg-blue-600 hover:bg-blue-700 shadow-lg text-white animate-pulse-subtle"
          aria-label="Open chat with AI assistant"
        >
          <MessageCircle size={28} />
        </Button>
      </div>
    );
  }
  
  // Show minimized header when minimized
  if (isMinimized) {
    return (
      <div className="fixed bottom-4 right-4 w-128 bg-blue-600 text-white rounded-t-lg shadow-lg z-40">
        <div className="p-3 flex justify-between items-center">
          <div className="flex items-center gap-2">
            <Bot size={20} />
            <div className="font-medium">{agentDisplayName}</div>
          </div>
          <div className="flex gap-2">
            <Button
              variant="ghost"
              size="icon"
              className="h-8 w-8 text-white hover:bg-blue-700 rounded-full"
              onClick={toggleMinimize}
              aria-label="Maximize chat"
            >
              <Maximize2 size={16} />
            </Button>
            <Button
              variant="ghost"
              size="icon"
              className="h-8 w-8 text-white hover:bg-blue-700 rounded-full"
              onClick={toggleChat}
              aria-label="Close chat"
            >
              <X size={16} />
            </Button>
          </div>
        </div>
      </div>
    );
  }

  // Full chat window
  return (
    <div className="fixed bottom-4 right-4 w-128 h-[500px] bg-white rounded-lg shadow-xl flex flex-col z-40">
      {/* Header */}
      <div className="bg-blue-600 text-white p-3 rounded-t-lg flex justify-between items-center">
        <div className="flex items-center gap-2">
          <Bot size={20} />
          <div>
            <h3 className="font-medium">{agentDisplayName}</h3>
            <div className="text-xs opacity-80">
              {isConnected ? 'Connected' : 'Connecting...'}
            </div>
          </div>
        </div>
        <div className="flex gap-2">
          <Button 
            variant="ghost" 
            size="icon" 
            className="h-8 w-8 text-white hover:bg-blue-700 rounded-full"
            onClick={toggleMinimize}
          >
            <Minimize2 size={16} />
          </Button>
          <Button 
            variant="ghost" 
            size="icon" 
            className="h-8 w-8 text-white hover:bg-blue-700 rounded-full"
            onClick={toggleChat}
          >
            <X size={16} />
          </Button>
        </div>
      </div>
      
      {/* Messages */}
      <div className="flex-1 overflow-y-auto p-3 space-y-3 bg-gray-50">
        {messages.map(message => (
          <div 
            key={message.id}
            className={`flex ${message.sender === 'user' ? 'justify-end' : 'justify-start'}`}
          >
            <div 
              className={`max-w-[80%] rounded-lg p-3 ${
                message.sender === 'user' 
                  ? 'bg-blue-600 text-white' 
                  : 'bg-white border border-gray-200 shadow-sm'
              }`}
            >
              {message.agentType && message.sender === 'agent' && (
                <div className="mb-1">
                  <SimpleBadge variant="outline" className="text-xs">
                    {agentDisplayName}
                  </SimpleBadge>
                </div>
              )}
              <div className="whitespace-pre-wrap">{message.content}</div>
              <div 
                className={`text-xs mt-1 ${
                  message.sender === 'user' ? 'text-blue-100' : 'text-gray-400'
                }`}
              >
                {formatDistanceToNow(message.timestamp, { addSuffix: true })}
              </div>
            </div>
          </div>
        ))}
        
        {isTyping && (
          <div className="flex items-center gap-2 text-gray-500">
            <div className="bg-gray-200 p-2 rounded-full w-2 h-2 animate-pulse"></div>
            <div className="text-sm">Typing...</div>
          </div>
        )}
        
        <div ref={messagesEndRef} />
      </div>
      
      {/* Input */}
      <div className="border-t p-3">
        {recordingStatus && (
          <div className="mb-2 text-sm text-center text-blue-600 whitespace-pre-line">
            {recordingStatus}
          </div>
        )}
        
        <div className="flex gap-2 mb-2">
          {/* Add warning message for HTTP development */}
          {window.location.protocol !== 'https:' && window.location.hostname !== 'localhost' && (
            <div className="bg-yellow-100 text-yellow-800 text-xs p-2 rounded w-full">
              Using HTTP: Microphone access may be blocked. Consider using HTTPS or <a href="#" className="underline font-bold" onClick={(e) => {
                e.preventDefault();
                alert("To use ngrok:\n1. Install: npm install -g ngrok\n2. Run: ngrok http <your-port-number>\n3. Use the HTTPS URL provided by ngrok");
              }}>ngrok</a> for development.
            </div>
          )}
        </div>
        
        <div className="flex gap-2">
          <Input
            value={inputValue}
            onChange={(e) => setInputValue(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder="Type a message..."
            className="flex-1"
          />
          
          {/* Mic Button */}
          <Button
            onClick={isRecording ? stopRecording : startRecording}
            className={`${
              isRecording 
                ? 'bg-red-600 hover:bg-red-700' 
                : 'bg-blue-600 hover:bg-blue-700'
            } text-white`}
            title={isRecording ? 'Stop recording' : 'Start recording'}
          >
            {isRecording ? <MicOff size={16} /> : <Mic size={16} />}
          </Button>
          
          {/* Send Button */}
          <Button 
            onClick={handleSendMessage}
            disabled={!inputValue.trim()}
            className="bg-blue-600 hover:bg-blue-700 text-white"
          >
            <Send size={16} />
          </Button>
        </div>
        <div className="mt-2 text-xs text-gray-400 text-center">
          Chat is anonymous and not stored
        </div>
      </div>
    </div>
  );
};

export default AnonymousChatWidget;
