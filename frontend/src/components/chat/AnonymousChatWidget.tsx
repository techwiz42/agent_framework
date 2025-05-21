// src/components/chat/AnonymousChatWidget.tsx
import React, { useState, useEffect, useRef } from 'react';
import { MessageCircle, X, Send, Bot, Minimize2, Maximize2, Mic, MicOff, Volume2, VolumeX } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import SimpleBadge from '@/components/ui/SimpleBadge';
import { Toggle } from '@/components/ui/toggle';
import { formatDistanceToNow } from 'date-fns';
import { v4 as uuidv4 } from 'uuid';
import { useSpeechToText } from '@/services/voice/SpeechToTextService';
import { useTextToSpeech } from '@/services/voice/TextToSpeechService';

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
  
  // Using CUSTOMERSERVICE agent
  const agentType = 'CUSTOMERSERVICE';
  const agentDisplayName = 'Customer Support';
  
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const wsRef = useRef<WebSocket | null>(null);

  // Initialize speech to text service with callbacks
  const stt = useSpeechToText({
    onTranscription: (text) => {
      setInputValue(prev => {
        // Ensure proper spacing between existing text and new transcription
        if (!prev) return text;
        const needsSpace = !prev.endsWith(' ') && !text.startsWith(' ');
        return prev + (needsSpace ? ' ' : '') + text;
      });
    }
  });

  // Initialize text to speech service
  const tts = useTextToSpeech();

  // WebSocket connection function 
  const connectWebSocket = () => {
    // Close any existing connection first
    if (wsRef.current) {
      try {
        if (wsRef.current.readyState !== WebSocket.CLOSED && wsRef.current.readyState !== WebSocket.CLOSING) {
          console.log('Closing existing WebSocket connection before creating a new one');
          wsRef.current.close();
        }
      } catch (e) {
        console.error('Error while closing existing WebSocket:', e);
      }
    }
    
    // Determine the WebSocket URL - Use the same host as the current page
    // This requires the Nginx proxy to be configured properly
    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    const wsUrl = `${protocol}//${window.location.host}/ws/anonymous/${agentType}?session_id=${sessionId}&connection_id=${sessionId}`;
    
    console.log('Connecting to WebSocket:', wsUrl);
    
    try {
      const ws = new WebSocket(wsUrl);
      
      // Basic WebSocket setup
      ws.onopen = () => {
        console.log('WebSocket connection opened successfully');
        setIsConnected(true);
        
        // Only add welcome message if this is the first connection (no messages yet)
        if (messages.length === 0) {
          const welcomeMessage = "Hello! I'm here to help with any customer service questions you might have. How can I assist you today?";
          
          setMessages([{
            id: uuidv4(),
            content: welcomeMessage,
            sender: 'agent' as const,
            timestamp: new Date(),
            agentType: agentType
          }]);
          
          // Play welcome message
          if (tts.isEnabled) {
            tts.playAudio(welcomeMessage);
          }
        } else {
          // For reconnections, add a different message
          const reconnectMessage = "I'm connected again. How can I help you?";
          
          setMessages(prev => [...prev, {
            id: uuidv4(),
            content: reconnectMessage,
            sender: 'agent' as const,
            timestamp: new Date(),
            agentType: agentType
          }]);
          
          // Play reconnection message
          if (tts.isEnabled) {
            tts.playAudio(reconnectMessage);
          }
        }
      };
      
      ws.onmessage = (event) => {
        try {
          console.log('WebSocket message received:', event.data);
          const data = JSON.parse(event.data);
          
          if (data.type === 'message') {
            const newMessage = {
              id: data.id || uuidv4(),
              content: formatAgentResponse(data.content),
              sender: 'agent' as const,
              timestamp: new Date(data.timestamp),
              agentType: data.agent_type || agentType
            };
            
            setMessages(prev => [...prev, newMessage]);
            setIsTyping(false);
            
            // Play TTS for this complete message
            if (tts.isEnabled) {
              tts.playAudio(data.content);
            }
          } else if (data.type === 'token') {
            // Handle streaming tokens (no TTS for streaming since we wait for complete messages)
            setMessages(prev => {
              const lastMessage = prev[prev.length - 1];
              
              // Check if the last message is an agent message that's still being streamed
              if (lastMessage && lastMessage.sender === 'agent' && !lastMessage.id.includes('complete')) {
                // Update existing message with new token
                const updatedMessages = [...prev];
                updatedMessages[updatedMessages.length - 1] = {
                  ...lastMessage,
                  content: formatAgentResponse(lastMessage.content + data.token)
                };
                return updatedMessages;
              } else {
                // Create a new streaming message with a temporary ID
                const streamingId = `streaming-${Date.now()}`; // Use timestamp instead of UUID
                return [...prev, {
                  id: streamingId,
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
          console.error('Error processing WebSocket message:', error);
        }
      };
      
      ws.onerror = (error) => {
        console.error('WebSocket error:', error);
        setIsConnected(false);
      };
      
      ws.onclose = (event) => {
        console.log(`WebSocket connection closed: code=${event.code}, reason=${event.reason || 'No reason provided'}`);
        setIsConnected(false);
        wsRef.current = null;
        
        // Attempt to reconnect after a delay if we're still open
        if (isOpen) {
          console.log('Will attempt to reconnect in 3 seconds...');
          setTimeout(() => {
            if (isOpen) {
              console.log('Attempting reconnection...');
              connectWebSocket();
            }
          }, 3000);
        }
      };
      
      // Store the WebSocket reference
      wsRef.current = ws;
    } catch (error) {
      console.error('Failed to establish WebSocket connection:', error);
      setIsConnected(false);
      wsRef.current = null;
    }
  };

  // Connect to WebSocket
  useEffect(() => {
    if (isOpen) {
      // Initialize as connected to enable the input field while we attempt connection
      setIsConnected(true);
      
      // Only create a new connection if one doesn't already exist
      if (!wsRef.current || wsRef.current.readyState === WebSocket.CLOSED || wsRef.current.readyState === WebSocket.CLOSING) {
        connectWebSocket();
      } else {
        console.log('WebSocket already exists in state:', 
          wsRef.current.readyState === WebSocket.CONNECTING ? 'CONNECTING' : 
          wsRef.current.readyState === WebSocket.OPEN ? 'OPEN' : 
          wsRef.current.readyState === WebSocket.CLOSING ? 'CLOSING' : 'CLOSED');
      }
      
      // Cleanup on unmount or when closing chat
      return () => {
        if (wsRef.current) {
          try {
            wsRef.current.close();
          } catch (e) {
            console.error('Error closing WebSocket:', e);
          }
          wsRef.current = null;
        }
        
        // Also stop any audio playback
        tts.stopAudio();
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
    
    // Note: We don't stop listening here - this allows continuous transcription
    // while still sending the message
    
    console.log('Attempting to send message:', inputValue);
    
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
        console.log('WebSocket state before sending:', 
          wsRef.current.readyState === WebSocket.CONNECTING ? 'CONNECTING' : 
          wsRef.current.readyState === WebSocket.OPEN ? 'OPEN' : 
          wsRef.current.readyState === WebSocket.CLOSING ? 'CLOSING' : 'CLOSED');
        
        // Only send if the connection is open
        if (wsRef.current.readyState === WebSocket.OPEN) {
          console.log('Sending message through WebSocket');
          wsRef.current.send(JSON.stringify({
            type: 'message',
            content: inputValue,
            timestamp: new Date().toISOString()
          }));
        } else {
          console.warn('WebSocket not in OPEN state, cannot send message');
          
          // Try to reconnect if not in OPEN state
          if (wsRef.current.readyState !== WebSocket.CONNECTING) {
            console.log('Attempting to reconnect...');
            connectWebSocket();
          }
          
          // Add message about connection issue
          setTimeout(() => {
            setMessages(prev => [...prev, {
              id: uuidv4(),
              content: "Connecting to server... Your message will be sent once connected.",
              sender: 'agent' as const,
              timestamp: new Date(),
              agentType: agentType
            }]);
          }, 500);
        }
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
        }, 500);
      }
    } else {
      // If not connected, add a message indicating the connection issue
      console.error('WebSocket not connected (null reference)');
      
      setTimeout(() => {
        setMessages(prev => [...prev, {
          id: uuidv4(),
          content: "Sorry, I'm having trouble connecting to the server. Attempting to reconnect now...",
          sender: 'agent' as const,
          timestamp: new Date(),
          agentType: agentType
        }]);
      }, 500);
      
      // Try to connect
      console.log('Attempting to connect WebSocket...');
      connectWebSocket();
    }
    
    setInputValue('');
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSendMessage();
      // Don't stop speech recognition when sending with Enter key
      // This allows for continuous dictation across multiple messages
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
        
        {/* Buttons group */}
        <div className="flex items-center gap-2 ml-auto">
          {/* Text-to-speech toggle */}
          <Toggle
            aria-label="Toggle text-to-speech"
            pressed={tts.isEnabled}
            onPressedChange={(pressed) => {
              tts.setEnabled(pressed);
            }}
            className="mr-2"
          >
            {tts.isEnabled ? 
              <Volume2 size={16} className={tts.isPlaying ? 'text-green-400 animate-pulse' : ''} /> : 
              <VolumeX size={16} />
            }
          </Toggle>
          
          {/* Window controls */}
          <Button 
            variant="ghost" 
            size="icon" 
            className="h-8 w-8 text-white hover:bg-blue-700 rounded-full"
            onClick={toggleMinimize}
            aria-label="Minimize chat"
          >
            <Minimize2 size={16} />
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
        {stt.recordingStatus && (
          <div className="mb-2 text-sm text-center text-blue-600 whitespace-pre-line">
            {stt.recordingStatus}
          </div>
        )}
        
        <div className="flex gap-2 items-center">
          <Input
            className="flex-1"
            placeholder={stt.isListening ? "Speak and I'll transcribe continuously as you talk..." : "Type your message or click the mic to speak..."}
            value={inputValue}
            onChange={(e) => setInputValue(e.target.value)}
            onKeyDown={handleKeyDown}
            disabled={!isConnected}
          />
          
          {/* Microphone button with dynamic styling and volume indicator */}
          <div className="relative">
            {stt.isListening && (
              <div className="absolute -top-8 left-1/2 transform -translate-x-1/2 bg-gray-800 text-white text-xs px-2 py-1 rounded">
                {/* Volume meter */}
                <div className="w-16 h-2 bg-gray-200 rounded-full overflow-hidden">
                  <div 
                    className="h-full bg-gradient-to-r from-green-500 to-red-500" 
                    style={{ width: `${stt.audioLevel}%` }}
                  />
                </div>
              </div>
            )}
            <Button
              variant="ghost"
              size="icon"
              onClick={stt.isListening ? stt.stopListening : stt.startListening}
              className={`rounded-full h-10 w-10 ${stt.isListening ? 'bg-red-500 text-white hover:bg-red-600' : 'text-blue-600 hover:bg-blue-50'}`}
              aria-label={stt.isListening ? "Stop listening" : "Start listening"}
            >
              {stt.isListening ? 
                <Mic size={18} className="animate-pulse" /> : 
                <Mic size={18} />}
            </Button>
          </div>
          
          <Button
            type="submit"
            onClick={handleSendMessage}
            className="bg-blue-600 hover:bg-blue-700 text-white"
            aria-label="Send message"
            disabled={!inputValue.trim() || !isConnected}
          >
            <Send size={18} />
          </Button>
        </div>
      </div>
    </div>
  );
};

export default AnonymousChatWidget;
