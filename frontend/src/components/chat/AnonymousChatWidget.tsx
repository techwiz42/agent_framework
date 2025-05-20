// src/components/chat/AnonymousChatWidget.tsx
import React, { useState, useEffect, useRef } from 'react';
import { MessageCircle, X, Send, Bot, Minimize2, Maximize2, Mic, MicOff, Volume2, VolumeX } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import SimpleBadge from '@/components/ui/SimpleBadge';
import { Toggle } from '@/components/ui/toggle';
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
  
  // Text-to-speech states
  const [isTtsEnabled, setIsTtsEnabled] = useState(false);
  const [isPlayingAudio, setIsPlayingAudio] = useState(false);
  const [ttsVoice, setTtsVoice] = useState('en-US-Neural2-C'); // Default voice
  
  // Speech-to-text refs
  const mediaRecorderRef = useRef<MediaRecorder | null>(null);
  const audioChunksRef = useRef<Blob[]>([]);
  const audioPlayerRef = useRef<HTMLAudioElement | null>(null);
  
  // Using CUSTOMERSERVICE agent
  const agentType = 'CUSTOMERSERVICE';
  const agentDisplayName = 'Customer Support';
  
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const wsRef = useRef<WebSocket | null>(null);

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
          if (isTtsEnabled) {
            playMessageAudio(welcomeMessage);
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
          if (isTtsEnabled) {
            playMessageAudio(reconnectMessage);
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
            if (isTtsEnabled) {
              playMessageAudio(data.content);
            }
          } else if (data.type === 'token') {
            // Handle streaming tokens (no TTS for streaming since we wait for complete messages)
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
        if (audioPlayerRef.current) {
          audioPlayerRef.current.pause();
          audioPlayerRef.current = null;
        }
      };
    }
  }, [isOpen, sessionId, agentType]);

  // Auto-scroll to bottom when new messages arrive
  useEffect(() => {
    if (messagesEndRef.current) {
      messagesEndRef.current.scrollIntoView({ behavior: 'smooth' });
    }
  }, [messages]);

  // Text-to-speech functions
  const playMessageAudio = async (message: string) => {
    if (!isTtsEnabled || !message.trim()) return;
    
    try {
      setIsPlayingAudio(true);
      const apiUrl = `${window.location.protocol}//${window.location.host}/api/voice/text-to-speech`;
      
      console.log('Converting message to speech:', message.substring(0, 50) + (message.length > 50 ? '...' : ''));
      
      const response = await fetch(apiUrl, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          text: message,
          voice_id: ttsVoice,
          return_base64: true,
          speaking_rate: 1.0,
          preprocess_text: true
        }),
      });
      
      if (!response.ok) {
        const errorText = await response.text();
        console.error('TTS error:', response.status, errorText);
        setIsPlayingAudio(false);
        return;
      }
      
      const data = await response.json();
      
      if (data.success && data.audio_base64) {
        // Create a URL for the audio
        const audioBlob = base64ToBlob(data.audio_base64, data.mime_type);
        const audioUrl = URL.createObjectURL(audioBlob);
        
        // Create or use existing audio element
        if (!audioPlayerRef.current) {
          audioPlayerRef.current = new Audio();
        }
        
        // Set up event handlers
        audioPlayerRef.current.onended = () => {
          setIsPlayingAudio(false);
        };
        
        audioPlayerRef.current.onerror = (error) => {
          console.error('Audio playback error:', error);
          setIsPlayingAudio(false);
        };
        
        // Set source and play
        audioPlayerRef.current.src = audioUrl;
        await audioPlayerRef.current.play();
      } else {
        console.error('TTS response missing audio data:', data);
        setIsPlayingAudio(false);
      }
    } catch (error) {
      console.error('Error playing TTS audio:', error);
      setIsPlayingAudio(false);
    }
  };

  // Function to stop audio playback
  const stopAudioPlayback = () => {
    if (audioPlayerRef.current) {
      audioPlayerRef.current.pause();
      audioPlayerRef.current.currentTime = 0;
      setIsPlayingAudio(false);
    }
  };

  // Helper function to convert base64 to Blob
  const base64ToBlob = (base64: string, mimeType: string) => {
    const byteCharacters = atob(base64);
    const byteArrays = [];
    
    for (let offset = 0; offset < byteCharacters.length; offset += 512) {
      const slice = byteCharacters.slice(offset, offset + 512);
      
      const byteNumbers = new Array(slice.length);
      for (let i = 0; i < slice.length; i++) {
        byteNumbers[i] = slice.charCodeAt(i);
      }
      
      const byteArray = new Uint8Array(byteNumbers);
      byteArrays.push(byteArray);
    }
    
    return new Blob(byteArrays, { type: mimeType });
  };

  // Cleanup effect for audio playback
  useEffect(() => {
    return () => {
      // Cleanup function to stop audio and release resources when component unmounts
      if (audioPlayerRef.current) {
        audioPlayerRef.current.pause();
        audioPlayerRef.current = null;
      }
    };
  }, []);

  // Handle sending a message
  const handleSendMessage = () => {
    if (!inputValue.trim()) return;
    
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
    }
  };
  
  // Speech-to-text functions
  const startRecording = async () => {
    try {
      setRecordingStatus('Requesting microphone access...');
      
      // Check if mediaDevices is supported
      if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) {
        console.error('Browser does not support mediaDevices API');
        throw new Error('Browser does not support microphone access');
      }
      
      console.log('Requesting microphone access with constraints...');
      
      // Request microphone access with detailed constraints optimized for Google STT
      // Google STT works best with LINEAR16 encoding (PCM) for non-WEBM files
      // For WEBM files, OPUS codec is preferred
      const constraints = {
        audio: {
          echoCancellation: true,
          noiseSuppression: true,
          autoGainControl: true,
          channelCount: 1,         // Mono audio
          sampleRate: 16000        // 16 kHz sample rate (Google STT preferred)
        }
      };
      
      console.log('Audio constraints:', JSON.stringify(constraints));
      const stream = await navigator.mediaDevices.getUserMedia(constraints);
      
      console.log('Microphone access granted, stream tracks:', stream.getAudioTracks().length);
      
      // Check if we actually got audio tracks
      if (stream.getAudioTracks().length === 0) {
        throw new Error('No audio tracks found in the media stream');
      }
      
      // Log audio track settings
      const audioTrack = stream.getAudioTracks()[0];
      console.log('Audio track settings:', audioTrack.getSettings());
      console.log('Audio track constraints:', audioTrack.getConstraints());
      
      // Set up the MediaRecorder with the audio stream
      // Use the best format for Google STT - prefer WEBM with Opus codec
      let mimeType = 'audio/webm;codecs=opus';
      
      if (!MediaRecorder.isTypeSupported(mimeType)) {
        // Fallback options
        const supportedMimeTypes = [
          'audio/webm',
          'audio/ogg;codecs=opus',
          'audio/wav',
          'audio/mp4'
        ];
        
        for (const type of supportedMimeTypes) {
          if (MediaRecorder.isTypeSupported(type)) {
            mimeType = type;
            console.log(`Fallback to supported MIME type: ${mimeType}`);
            break;
          }
        }
      } else {
        console.log(`Using optimal MIME type for Google STT: ${mimeType}`);
      }
      
      // Create MediaRecorder with options
      const options = { 
        mimeType,
        audioBitsPerSecond: 16000  // Match Google STT expectations
      };
      console.log('Creating MediaRecorder with options:', options);
      const mediaRecorder = new MediaRecorder(stream, options);
      mediaRecorderRef.current = mediaRecorder;
      audioChunksRef.current = [];
      
      // Event handler for data available
      mediaRecorder.ondataavailable = (event) => {
        console.log(`Data available event: ${event.data.size} bytes`);
        if (event.data.size > 0) {
          audioChunksRef.current.push(event.data);
          console.log(`Added audio chunk, total chunks: ${audioChunksRef.current.length}`);
        } else {
          console.warn('Received empty data chunk');
        }
      };
      
      // Event handler for recording start
      mediaRecorder.onstart = () => {
        console.log('MediaRecorder started');
        setRecordingStatus('Recording audio... (Click stop when done)');
      };
      
      // Event handler for recording stop
      mediaRecorder.onstop = async () => {
        console.log('MediaRecorder stopped, processing audio...');
        setRecordingStatus('Processing audio...');
        
        // Create a blob from the recorded audio chunks
        console.log(`Creating blob from ${audioChunksRef.current.length} chunks`);
        
        // Make sure we got some audio data
        if (audioChunksRef.current.length === 0 || audioChunksRef.current.every(chunk => chunk.size === 0)) {
          setRecordingStatus('No audio was recorded. Please try again and speak clearly.');
          console.error('No audio chunks were recorded');
          
          // Clean up
          stream.getTracks().forEach(track => track.stop());
          return;
        }
        
        const audioBlob = new Blob(audioChunksRef.current, { type: mimeType });
        console.log(`Audio blob created: ${audioBlob.size} bytes, type: ${audioBlob.type}`);
        
        // Check if the blob is suspiciously small
        if (audioBlob.size < 1000) {
          console.warn('Audio blob is very small, may not contain speech');
        }
        
        // Send the audio blob to the backend for speech-to-text processing
        await sendAudioForSTT(audioBlob);
        
        // Clean up
        console.log('Stopping audio tracks');
        stream.getTracks().forEach(track => track.stop());
        console.log('Audio tracks stopped');
        setRecordingStatus('');
      };
      
      // Event handler for errors
      mediaRecorder.onerror = (event) => {
        console.error('MediaRecorder error:', event);
        setRecordingStatus(`Recording error: ${event.error}`);
      };
      
      // Start recording with smaller time slices for more frequent ondataavailable events
      console.log('Starting MediaRecorder...');
      mediaRecorder.start(500); // Collect data every 500ms
      setIsRecording(true);
      
      // Record for at least 2 seconds to ensure we get a valid audio file
      setTimeout(() => {
        console.log('Reminder: Click stop when you finish speaking');
      }, 2000);
      
    } catch (error: any) {
      console.error('Error starting recording:', error, error.name, error.message);
      setIsRecording(false);
      
      // Provide more helpful error messages based on the error
      if (error.name === 'NotAllowedError') {
        setRecordingStatus('Microphone access denied. Please check your browser permissions.');
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
    console.log('Stop recording called');
    
    if (mediaRecorderRef.current && isRecording) {
      try {
        console.log('MediaRecorder state before stopping:', mediaRecorderRef.current.state);
        
        if (mediaRecorderRef.current.state === 'recording') {
          console.log('Stopping MediaRecorder');
          mediaRecorderRef.current.stop();
          console.log('MediaRecorder stopped');
        } else {
          console.log('MediaRecorder not in recording state:', mediaRecorderRef.current.state);
        }
      } catch (error) {
        console.error('Error stopping recording:', error);
      }
      
      setIsRecording(false);
    } else {
      console.log('No active MediaRecorder to stop:', 
        mediaRecorderRef.current ? `Exists but not recording: ${mediaRecorderRef.current.state}` : 'No recorder');
    }
  };
  
  const sendAudioForSTT = async (audioBlob: Blob) => {
    try {
      // Log the audio blob details for debugging
      console.log('Audio blob to send:', audioBlob.type, audioBlob.size, 'bytes');
      
      // For debugging, save and log the file name that would be sent
      const fileName = `recording_${Date.now()}.${audioBlob.type.split('/')[1] || 'webm'}`;
      console.log('File name will be:', fileName);
      
      // Create form data to send the audio file
      const formData = new FormData();
      
      // Important: Use the exact field name expected by the backend
      formData.append('audio_file', audioBlob, fileName);
      
      // Default language code
      formData.append('language_code', 'en-US');
      
      // Explicitly set the encoding to match what we're sending
      // This helps Google STT know how to process the audio
      if (audioBlob.type.includes('webm')) {
        // WebM uses Opus codec, which is supported by Google STT
        console.log('Using WEBM audio format');
      } else {
        // If not using WebM, we should specify the sample rate
        // as it might not be included in the audio metadata
        console.log('Using non-WEBM audio format, adding sample rate');
        formData.append('sample_rate', '16000');
      }
      
      // Use the correct API URL that we know works
      const apiUrl = `${window.location.protocol}//${window.location.host}/api/voice/speech-to-text`;
      
      console.log('Sending fetch request with FormData');
      const response = await fetch(apiUrl, {
        method: 'POST',
        body: formData,
      });
      
      console.log('Received response:', response.status, response.statusText);
      
      if (!response.ok) {
        const errorText = await response.text();
        console.error('Server error:', response.status, errorText);
        throw new Error(`Server responded with status ${response.status}: ${errorText}`);
      }
      
      const data = await response.json();
      console.log('STT response data:', data);
      
      if (data.success && data.transcript) {
        // Set the transcribed text as the input value
        console.log('Setting transcript:', data.transcript);
        setInputValue(prev => prev + (prev ? ' ' : '') + data.transcript);
        setRecordingStatus('');
      } else if (data.error) {
        console.error('STT error:', data.error, data.details || '');
        
        // Check for common Google STT errors
        if (data.details && typeof data.details === 'string' && data.details.includes('sample_rate_hertz')) {
          setRecordingStatus('Audio format error: sample rate mismatch. Trying again may help.');
        } else if (data.error.includes('No speech detected')) {
          setRecordingStatus('No speech detected. Please try again and speak clearly.');
        } else if (data.error.includes('Unexpected API response')) {
          setRecordingStatus('Speech recognition service error. This could be a temporary issue with Google STT.');
        } else {
          setRecordingStatus(`Error: ${data.error}`);
        }
        
        // Clear error status after a few seconds
        setTimeout(() => {
          setRecordingStatus('');
        }, 8000);
      } else {
        console.log('No transcript found in response');
        setRecordingStatus('No speech detected or recognized. Please try again and speak clearly.');
        
        // Clear status after a few seconds
        setTimeout(() => {
          setRecordingStatus('');
        }, 5000);
      }
    } catch (error: any) {
      console.error('Error sending audio for STT:', error);
      
      // Provide more user-friendly error message
      if (error.message && error.message.includes('Failed to fetch')) {
        setRecordingStatus('Network error: Cannot connect to API server');
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
        
        {/* Text-to-speech toggle */}
        <div className="ml-auto mr-2">
          <Toggle
            aria-label="Toggle text-to-speech"
            pressed={isTtsEnabled}
            onPressedChange={(pressed) => {
              setIsTtsEnabled(pressed);
              if (!pressed && isPlayingAudio) {
                stopAudioPlayback();
              }
            }}
          >
            {isTtsEnabled ? 
              <Volume2 size={16} className={isPlayingAudio ? 'text-green-400 animate-pulse' : ''} /> : 
              <VolumeX size={16} />
            }
          </Toggle>
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
        
        <div className="flex gap-2 items-center">
          <Button
            variant={isRecording ? "destructive" : "outline"}
            size="icon"
            onClick={isRecording ? stopRecording : startRecording}
            className={isRecording ? "bg-red-500 hover:bg-red-600 text-white" : ""}
            aria-label={isRecording ? "Stop recording" : "Start recording"}
          >
            {isRecording ? <MicOff size={18} /> : <Mic size={18} />}
          </Button>
          
          <Input
            className="flex-1"
            placeholder="Type your message..."
            value={inputValue}
            onChange={(e) => setInputValue(e.target.value)}
            onKeyDown={handleKeyDown}
            disabled={!isConnected}
          />
          
          <Button
            type="submit"
            onClick={handleSendMessage}
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