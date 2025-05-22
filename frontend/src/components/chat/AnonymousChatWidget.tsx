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
  const [sttEnabled, setSttEnabled] = useState(true); // Enable STT by default
  const [isWaitingForResponse, setIsWaitingForResponse] = useState(false);
  
  // Using CHATBOT agent
  const agentType = 'CHATBOT';
  const agentDisplayName = 'Friendly Disembodied Robot';
  
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const wsRef = useRef<WebSocket | null>(null);
  const messageBeingBuiltRef = useRef<boolean>(false);
  const fullMessageRef = useRef<string>('');  // Track the full message as it's built
  
  // Initialize speech to text service with callbacks
  const stt = useSpeechToText({
    sampleRate: 48000,
    silenceThreshold: 15, // Increased for better noise handling
    silentFramesToProcess: 8, // More conservative processing
    onTranscription: (text) => {
      // Only accept transcriptions when not waiting for a response
      if (!isWaitingForResponse) {
        console.log('STT transcription received:', text);
        setInputValue(prev => {
          // Ensure proper spacing between existing text and new transcription
          if (!prev) return text;
          const needsSpace = !prev.endsWith(' ') && !text.startsWith(' ');
          return prev + (needsSpace ? ' ' : '') + text;
        });
      } else {
        console.log('Ignoring transcription while waiting for response:', text);
      }
    },
    onAudioLevelChange: (level) => {
      // Audio level change handled in the component via stt.audioLevel
    },
    onStatusChange: (status) => {
      console.log('STT status change:', status);
    }
  });

  // Initialize text to speech service with smart buffering
  const tts = useTextToSpeech({
    preprocessText: true,           // Clean markdown and formatting
    useSmartBuffering: true,        // Use smart buffering for streaming
    minChunkSize: 30,               // Minimum characters to speak at once
    chunkPause: 100,                // Small pause between chunks (ms)
    onPlaybackStart: () => {
      console.log("TTS playback started");
    },
    onPlaybackEnd: () => {
      console.log("TTS playback ended");
    },
    onPlaybackError: (error) => {
      console.error("TTS playback error:", error);
    }
  });

  // Auto-start STT when chat opens if enabled
  useEffect(() => {
    if (isOpen && sttEnabled && !stt.isListening && !isWaitingForResponse) {
      console.log('Auto-starting STT since chat is open and STT is enabled');
      setTimeout(() => {
        stt.startListening();
      }, 1000); // Small delay to ensure UI is ready
    }
  }, [isOpen, sttEnabled]);

  // Handle STT based on waiting state
  useEffect(() => {
    if (isWaitingForResponse && stt.isListening) {
      console.log('Pausing STT while waiting for response');
      stt.stopListening();
    } else if (!isWaitingForResponse && sttEnabled && isOpen && !stt.isListening) {
      console.log('Resuming STT after response received');
      // Add a small delay to ensure smooth transition
      setTimeout(() => {
        stt.startListening();
      }, 500);
    }
  }, [isWaitingForResponse, sttEnabled, isOpen]);

  // Handle STT toggle
  const handleSttToggle = () => {
    const newEnabled = !sttEnabled;
    setSttEnabled(newEnabled);
    
    if (newEnabled && isOpen && !isWaitingForResponse) {
      // Start listening when enabled
      stt.startListening();
    } else if (stt.isListening) {
      // Stop listening when disabled
      stt.stopListening();
    }
  };

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
          const welcomeMessage = "Hello! How can I help you today?";
          
          setMessages([{
            id: uuidv4(),
            content: welcomeMessage,
            sender: 'agent' as const,
            timestamp: new Date(),
            agentType: agentType
          }]);
          
          // Speak the welcome message
          if (tts.isEnabled) {
            console.log("Playing welcome message via TTS");
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
          
          // Speak the reconnection message
          if (tts.isEnabled) {
            tts.playAudio(reconnectMessage);
          }
        }
      };
      
      ws.onmessage = (event) => {
        try {
          // Check for non-JSON messages
          if (typeof event.data === 'string' && (event.data === 'ping' || event.data.trim() === 'ping')) {
            ws.send('pong');
            return;
          }
          
          console.log('WebSocket message received:', event.data);
          let data;
          try {
            data = JSON.parse(event.data);
          } catch (e) {
            console.error('Error parsing message as JSON:', e);
            return;
          }
          
          if (data.type === 'message') {
            // Complete message from agent - rare case as it usually comes token by token
            const messageContent = formatAgentResponse(data.content);
            
            // Reset the message building state
            messageBeingBuiltRef.current = false;
            fullMessageRef.current = '';
            
            // Create a new message
            const newMessage = {
              id: data.id || uuidv4(),
              content: messageContent,
              sender: 'agent' as const,
              timestamp: new Date(data.timestamp || new Date()),
              agentType: data.agent_type || agentType
            };
            
            setMessages(prev => [...prev, newMessage]);
            setIsTyping(false);
            setIsWaitingForResponse(false);
            
            // Speak the full message (not streamed)
            if (tts.isEnabled) {
              console.log("Playing complete message via TTS");
              tts.playAudio(messageContent);
            }
          } else if (data.type === 'token') {
            // Handle streaming tokens
            const token = data.token || '';
            
            // Add to the full message
            fullMessageRef.current += token;
            
            // If this is the first token of a new message
            if (!messageBeingBuiltRef.current) {
              messageBeingBuiltRef.current = true;
              
              // Reset TTS before starting a new message
              if (tts.isEnabled) {
                console.log("Starting new streaming message - resetting TTS");
                tts.resetSpeech();
              }
              
              // Add a new streaming message
              setMessages(prev => [...prev, {
                id: uuidv4(),
                content: token,
                sender: 'agent' as const,
                timestamp: new Date(),
                agentType: agentType
              }]);
              
              // Start streaming the token
              if (tts.isEnabled) {
                console.log("Streaming first token:", token);
                tts.streamSpeech(token);
              }
            } else {
              // Update the last message with the accumulated tokens
              setMessages(prev => {
                const updatedMessages = [...prev];
                if (updatedMessages.length > 0) {
                  const lastIndex = updatedMessages.length - 1;
                  if (updatedMessages[lastIndex].sender === 'agent') {
                    updatedMessages[lastIndex] = {
                      ...updatedMessages[lastIndex],
                      content: fullMessageRef.current
                    };
                  }
                }
                return updatedMessages;
              });
              
              // Stream the token for speech
              if (tts.isEnabled) {
                tts.streamSpeech(token);
              }
            }
          } else if (data.type === 'typing_status') {
            // Agent typing indicator
            setIsTyping(data.is_typing);
            
            // If agent stops typing and we were building a message, wrap it up
            if (!data.is_typing && messageBeingBuiltRef.current) {
              messageBeingBuiltRef.current = false;
              console.log("Agent finished typing message:", fullMessageRef.current.substring(0, 50) + (fullMessageRef.current.length > 50 ? '...' : ''));
              
              // Clear waiting state when agent finishes
              setIsWaitingForResponse(false);
              
              // Finish speech processing
              if (tts.isEnabled) {
                console.log("Finishing TTS speech for complete message");
                tts.finishSpeech();
              }
            }
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
        
        // Stop any audio playback and STT
        tts.stopAudio();
        if (stt.isListening) {
          stt.stopListening();
        }
      };
    } else {
      // Stop STT when chat is closed
      if (stt.isListening) {
        stt.stopListening();
      }
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
    if (!inputValue.trim() || isWaitingForResponse) return;
    
    console.log('Attempting to send message:', inputValue);
    
    // CRITICAL: Reset STT state immediately to prevent processing old audio
    console.log('Resetting STT state before sending message');
    stt.resetStt();
    
    // Stop STT temporarily while sending
    if (stt.isListening) {
      console.log('Stopping STT while sending message');
      stt.stopListening();
    }
    
    const newMessage = {
      id: uuidv4(),
      content: inputValue,
      sender: 'user' as const,
      timestamp: new Date()
    };
    
    setMessages(prev => [...prev, newMessage]);
    
    // Set waiting state
    setIsWaitingForResponse(true);
    
    // Reset state for new conversation
    fullMessageRef.current = '';
    messageBeingBuiltRef.current = false;
    
    // Stop any current speech
    tts.stopAudio();
    
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
          
          // Create conversation history for context
          const conversationHistory = messages.map(msg => ({
            role: msg.sender === 'user' ? 'user' : 'assistant',
            content: msg.content,
            timestamp: msg.timestamp.toISOString()
          }));
          
          // Add the current message to history
          conversationHistory.push({
            role: 'user',
            content: inputValue,
            timestamp: new Date().toISOString()
          });
          
          // Send message with full conversation context
          wsRef.current.send(JSON.stringify({
            type: 'message',
            content: inputValue,
            conversation_history: conversationHistory,
            timestamp: new Date().toISOString()
          }));
        } else {
          console.warn('WebSocket not in OPEN state, cannot send message');
          setIsWaitingForResponse(false);
          
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
        setIsWaitingForResponse(false);
        
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
      setIsWaitingForResponse(false);
      
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
          Chat with AI (Voice Enabled)
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
            {sttEnabled && stt.isListening && (
              <div className="w-2 h-2 bg-red-400 rounded-full animate-pulse"></div>
            )}
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
            <div className="text-xs opacity-80 flex items-center gap-2">
              <span>{isConnected ? 'Connected' : 'Connecting...'}</span>
              {sttEnabled && stt.isListening && (
                <span className="flex items-center gap-1">
                  <div className="w-2 h-2 bg-red-400 rounded-full animate-pulse"></div>
                  Listening
                </span>
              )}
              {isWaitingForResponse && (
                <span className="text-yellow-200">Waiting for response...</span>
              )}
            </div>
          </div>
        </div>
        
        {/* Buttons group */}
        <div className="flex items-center gap-2 ml-auto">
          {/* Speech-to-text toggle */}
          <Button
            variant="ghost"
            size="icon"
            className={`h-8 w-8 text-white hover:bg-blue-700 rounded-full ${sttEnabled && stt.isListening ? 'bg-red-500 hover:bg-red-600' : ''}`}
            onClick={handleSttToggle}
            aria-label={sttEnabled ? (stt.isListening ? "Disable voice input" : "Enable voice input") : "Enable voice input"}
            disabled={isWaitingForResponse}
          >
            {sttEnabled && stt.isListening ? 
              <Mic size={16} className="text-white animate-pulse" /> : 
              sttEnabled ? <Mic size={16} /> : <MicOff size={16} />}
          </Button>

          {/* Text-to-speech toggle */}
          <Toggle
            aria-label="Toggle text-to-speech"
            pressed={tts.isEnabled}
            onPressedChange={(pressed) => {
              console.log("TTS toggle changed to:", pressed);
              tts.setEnabled(pressed);
              
              // Clear speech buffer when disabled
              if (!pressed) {
                tts.stopAudio();
              } else {
                // Play a confirmation sound when enabled
                tts.playAudio("Text to speech is now on");
              }
            }}
            className={`mr-2 ${tts.isEnabled ? 'bg-blue-700 hover:bg-blue-800' : ''}`}
          >
            {tts.isEnabled ? 
              <Volume2 size={16} className={tts.isPlaying ? 'text-green-400 animate-pulse' : 'text-white'} /> : 
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
            placeholder={
              isWaitingForResponse 
                ? "Waiting for response..." 
                : sttEnabled && stt.isListening 
                  ? "Speak and I'll transcribe continuously..." 
                  : "Type your message or enable voice input..."
            }
            value={inputValue}
            onChange={(e) => setInputValue(e.target.value)}
            onKeyDown={handleKeyDown}
            disabled={!isConnected || isWaitingForResponse}
          />
          
          {/* Voice input status indicator */}
          {sttEnabled && stt.isListening && (
            <div className="relative">
              <div className="absolute -top-8 left-1/2 transform -translate-x-1/2 bg-gray-800 text-white text-xs px-2 py-1 rounded">
                <div className="w-16 h-2 bg-gray-200 rounded-full overflow-hidden">
                  <div 
                    className="h-full bg-gradient-to-r from-green-500 to-red-500" 
                    style={{ width: `${stt.audioLevel}%` }}
                  />
                </div>
              </div>
            </div>
          )}
          
          <Button
            type="submit"
            onClick={handleSendMessage}
            className="bg-blue-600 hover:bg-blue-700 text-white"
            aria-label="Send message"
            disabled={!inputValue.trim() || !isConnected || isWaitingForResponse}
          >
            <Send size={18} />
          </Button>
        </div>
      </div>
    </div>
  );
};

export default AnonymousChatWidget;
