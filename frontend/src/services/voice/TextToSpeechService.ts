// src/services/voice/TextToSpeechService.ts
import { useState, useRef, useEffect } from 'react';

/**
 * Type for TTS options
 */
export interface TtsOptions {
  /** Voice ID to use for text-to-speech */
  voiceId?: string;
  /** Speaking rate (0.5 to 2.0) */
  speakingRate?: number;
  /** Whether to preprocess text for better speech */
  preprocessText?: boolean;
  /** Whether to use smart buffering for streaming speech */
  useSmartBuffering?: boolean;
  /** API URL for the text-to-speech service */
  apiUrl?: string;
  /** Callback when audio playback starts */
  onPlaybackStart?: () => void;
  /** Callback when audio playback ends */
  onPlaybackEnd?: () => void;
  /** Callback when audio playback errors */
  onPlaybackError?: (error: any) => void;
  /** Minimum size of text chunks to speak (for smart buffering) */
  minChunkSize?: number;
  /** Pause between speech chunks (ms) */
  chunkPause?: number;
}

/**
 * Prepares text for speech by removing markdown formatting and other elements
 * that shouldn't be spoken aloud
 */
export const cleanTextForSpeech = (text: string): string => {
  if (!text) return '';
  
  // Remove markdown headers, bullets, code blocks, etc.
  let cleaned = text
    // Remove markdown headers
    .replace(/#{1,6}\s+/g, '')
    // Remove markdown code blocks with language specification
    .replace(/```[\w]*\n[\s\S]*?```/g, 'code snippet. ')
    // Remove markdown code blocks without language
    .replace(/```[\s\S]*?```/g, 'code snippet. ')
    // Remove inline code
    .replace(/`([^`]+)`/g, '$1')
    // Remove markdown bold/italic
    .replace(/\*\*([^*]+)\*\*/g, '$1')
    .replace(/\*([^*]+)\*/g, '$1')
    .replace(/__([^_]+)__/g, '$1')
    .replace(/_([^_]+)_/g, '$1')
    // Remove markdown bullets
    .replace(/^\s*[-*+]\s+/gm, '')
    // Remove markdown numbered lists
    .replace(/^\s*\d+\.\s+/gm, '')
    // Remove URLs but keep linked text
    .replace(/\[([^\]]+)\]\([^\)]+\)/g, '$1')
    // Remove standalone URLs
    .replace(/https?:\/\/\S+/g, 'URL')
    // Remove HTML tags
    .replace(/<[^>]*>/g, '')
    // Fix common spoken oddities
    .replace(/(\w)-(\w)/g, '$1 $2')  // Hyphenated words
    .replace(/&/g, ' and ')
    .replace(/\//g, ' or ')
    // Handle common abbreviations
    .replace(/\bTL;DR\b/g, 'T L D R')
    .replace(/\bUI\b/g, 'U I')
    .replace(/\bAPI\b/g, 'A P I')
    .replace(/\bHTML\b/g, 'H T M L')
    .replace(/\bCSS\b/g, 'C S S')
    .replace(/\bURL\b/g, 'U R L')
    .replace(/\bJSON\b/g, 'J S O N')
    .replace(/\bHTTP\b/g, 'H T T P')
    .replace(/\bSVG\b/g, 'S V G')
    .replace(/\bPDF\b/g, 'P D F')
    // Remove excess punctuation
    .replace(/\.{2,}/g, '.')
    .replace(/\,{2,}/g, ',')
    .replace(/\?{2,}/g, '?')
    .replace(/\!{2,}/g, '!')
    // Remove excess whitespace
    .replace(/\s+/g, ' ')
    .trim();
  
  return cleaned;
};

/**
 * Hook for using text-to-speech functionality
 */
export const useTextToSpeech = (options: TtsOptions = {}) => {
  // Default options
  const defaultOptions: Required<TtsOptions> = {
    voiceId: 'en-US-Neural2-C',
    speakingRate: 1.0,
    preprocessText: true,
    useSmartBuffering: true,
    apiUrl: `${window.location.protocol}//${window.location.host}/api/voice/text-to-speech`,
    onPlaybackStart: () => {},
    onPlaybackEnd: () => {},
    onPlaybackError: () => {},
    minChunkSize: 20,    // Minimum characters to speak
    chunkPause: 100      // Slight pause between chunks
  };

  // Merge provided options with defaults
  const opts = { ...defaultOptions, ...options };

  // States
  const [isEnabled, setIsEnabled] = useState(false);
  const [isPlaying, setIsPlaying] = useState(false);
  const [isSpeakingComplete, setIsSpeakingComplete] = useState(true);
  const [lastTokenTime, setLastTokenTime] = useState(0);

  // Refs
  const audioPlayerRef = useRef<HTMLAudioElement | null>(null);
  const speechBufferRef = useRef<string>('');
  const audioQueueRef = useRef<string[]>([]);
  const processingTimeoutRef = useRef<NodeJS.Timeout | null>(null);
  const typingPauseTimeoutRef = useRef<NodeJS.Timeout | null>(null);
  const isProcessingRef = useRef<boolean>(false);
  
  // List of common sentence delimiters
  const sentenceDelimiters = ['.', '!', '?', ':', ';', '\n'];

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

  // Process the next audio in the queue
  const processNextInQueue = async () => {
    if (audioQueueRef.current.length === 0 || isProcessingRef.current) {
      return;
    }
    
    isProcessingRef.current = true;
    const text = audioQueueRef.current.shift() || '';
    
    if (!text.trim()) {
      isProcessingRef.current = false;
      if (audioQueueRef.current.length > 0) {
        processNextInQueue();
      } else {
        setIsSpeakingComplete(true);
      }
      return;
    }
    
    try {
      setIsPlaying(true);
      opts.onPlaybackStart();
      
      // Process the text if needed
      const processedText = opts.preprocessText ? cleanTextForSpeech(text) : text;
      
      // Skip if nothing to speak
      if (!processedText.trim()) {
        setIsPlaying(false);
        isProcessingRef.current = false;
        opts.onPlaybackEnd();
        
        // Process the next item in the queue
        if (audioQueueRef.current.length > 0) {
          setTimeout(() => processNextInQueue(), opts.chunkPause);
        } else {
          setIsSpeakingComplete(true);
        }
        return;
      }
      
      console.log('Converting to speech:', processedText.substring(0, 50) + (processedText.length > 50 ? '...' : ''));
      
      const response = await fetch(opts.apiUrl, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          text: processedText,
          voice_id: opts.voiceId,
          return_base64: true,
          speaking_rate: opts.speakingRate,
          preprocess_text: false // We've already preprocessed
        }),
      });
      
      if (!response.ok) {
        const errorText = await response.text();
        console.error('TTS error:', response.status, errorText);
        setIsPlaying(false);
        isProcessingRef.current = false;
        opts.onPlaybackError(new Error(errorText));
        
        // Try next item in the queue
        if (audioQueueRef.current.length > 0) {
          setTimeout(() => processNextInQueue(), opts.chunkPause);
        } else {
          setIsSpeakingComplete(true);
        }
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
          setIsPlaying(false);
          isProcessingRef.current = false;
          opts.onPlaybackEnd();
          
          // Release the URL to prevent memory leaks
          URL.revokeObjectURL(audioUrl);
          
          // Process the next item in the queue with a short pause
          if (audioQueueRef.current.length > 0) {
            setTimeout(() => processNextInQueue(), opts.chunkPause);
          } else {
            setIsSpeakingComplete(true);
          }
        };
        
        audioPlayerRef.current.onerror = (error) => {
          console.error('Audio playback error:', error);
          setIsPlaying(false);
          isProcessingRef.current = false;
          opts.onPlaybackError(error);
          
          // Release the URL
          URL.revokeObjectURL(audioUrl);
          
          // Try next item in the queue
          if (audioQueueRef.current.length > 0) {
            setTimeout(() => processNextInQueue(), opts.chunkPause);
          } else {
            setIsSpeakingComplete(true);
          }
        };
        
        // Set source and play
        audioPlayerRef.current.src = audioUrl;
        await audioPlayerRef.current.play();
      } else {
        console.error('TTS response missing audio data:', data);
        setIsPlaying(false);
        isProcessingRef.current = false;
        opts.onPlaybackError(new Error('Missing audio data in response'));
        
        // Try next item in the queue
        if (audioQueueRef.current.length > 0) {
          setTimeout(() => processNextInQueue(), opts.chunkPause);
        } else {
          setIsSpeakingComplete(true);
        }
      }
    } catch (error) {
      console.error('Error playing TTS audio:', error);
      setIsPlaying(false);
      isProcessingRef.current = false;
      opts.onPlaybackError(error);
      
      // Try next item in the queue
      if (audioQueueRef.current.length > 0) {
        setTimeout(() => processNextInQueue(), opts.chunkPause);
      } else {
        setIsSpeakingComplete(true);
      }
    }
  };

  // Process the speech buffer 
  const processSpeechBuffer = () => {
    if (!isEnabled || !opts.useSmartBuffering || !speechBufferRef.current) {
      return;
    }

    // Get text from the buffer and clear it
    const textToSpeak = speechBufferRef.current;
    speechBufferRef.current = '';
    
    // Add to the queue
    if (textToSpeak.trim()) {
      audioQueueRef.current.push(textToSpeak);
      setIsSpeakingComplete(false);
      
      // Start processing the queue if not already processing
      if (!isProcessingRef.current && !isPlaying) {
        processNextInQueue();
      }
    }
  };

  // Add text to the speech buffer
  const addToSpeechBuffer = (text: string) => {
    if (!isEnabled || !opts.useSmartBuffering) {
      return;
    }
    
    // Update the last token time
    setLastTokenTime(Date.now());
    
    // Add to buffer
    speechBufferRef.current += text;
    
    // Clear any pending timeout
    if (processingTimeoutRef.current) {
      clearTimeout(processingTimeoutRef.current);
    }
    
    // Check if we have a complete sentence or significant content
    const hasCompletePhrase = sentenceDelimiters.some(d => speechBufferRef.current.includes(d));
    
    // Process the buffer if we have a complete phrase or enough text
    if (hasCompletePhrase || speechBufferRef.current.length >= opts.minChunkSize) {
      processSpeechBuffer();
    } else {
      // Set a timeout to process buffer even if we don't get a complete phrase
      processingTimeoutRef.current = setTimeout(() => {
        if (speechBufferRef.current.trim()) {
          processSpeechBuffer();
        }
      }, 1000); // Wait a second to collect more text
    }
    
    // Set a timeout to detect when typing has paused
    if (typingPauseTimeoutRef.current) {
      clearTimeout(typingPauseTimeoutRef.current);
    }
    
    typingPauseTimeoutRef.current = setTimeout(() => {
      // If there's still text in the buffer, process it
      if (speechBufferRef.current.trim()) {
        processSpeechBuffer();
      }
    }, 500); // 500ms typing pause detection
  };

  // Stream tokens of text for speech - call this as tokens arrive
  const streamSpeech = (text: string) => {
    if (!isEnabled) return;
    
    if (opts.useSmartBuffering) {
      addToSpeechBuffer(text);
    } else {
      // If not using smart buffering, speak each chunk directly
      playAudio(text);
    }
  };

  // Finish streaming speech - call this when message is complete
  const finishSpeech = () => {
    if (!isEnabled) return;
    
    // Process any remaining text in the buffer
    if (opts.useSmartBuffering && speechBufferRef.current.trim()) {
      processSpeechBuffer();
    }
  };

  // Reset speech state - call this before starting a new message
  const resetSpeech = () => {
    // Clear the buffer
    speechBufferRef.current = '';
    
    // Clear any pending timeouts
    if (processingTimeoutRef.current) {
      clearTimeout(processingTimeoutRef.current);
      processingTimeoutRef.current = null;
    }
    
    if (typingPauseTimeoutRef.current) {
      clearTimeout(typingPauseTimeoutRef.current);
      typingPauseTimeoutRef.current = null;
    }
  };

  // Play a complete message all at once
  const playAudio = async (text: string) => {
    if (!isEnabled || !text.trim()) return;
    
    // For complete messages, we stop any current playback
    stopAudio();
    resetSpeech();
    
    // Clear the queue
    audioQueueRef.current = [];
    
    // Add the complete message to the queue
    audioQueueRef.current.push(text);
    setIsSpeakingComplete(false);
    
    // Process the queue
    processNextInQueue();
  };

  // Stop audio playback
  const stopAudio = () => {
    if (audioPlayerRef.current) {
      audioPlayerRef.current.pause();
      audioPlayerRef.current.currentTime = 0;
      
      setIsPlaying(false);
      isProcessingRef.current = false;
      opts.onPlaybackEnd();
    }
    
    // Clear the queue
    audioQueueRef.current = [];
    
    // Clear the buffer
    speechBufferRef.current = '';
    
    // Clear timeouts
    if (processingTimeoutRef.current) {
      clearTimeout(processingTimeoutRef.current);
      processingTimeoutRef.current = null;
    }
    
    if (typingPauseTimeoutRef.current) {
      clearTimeout(typingPauseTimeoutRef.current);
      typingPauseTimeoutRef.current = null;
    }
    
    setIsSpeakingComplete(true);
  };

  // Cleanup effect
  useEffect(() => {
    return () => {
      // Cleanup audio element on unmount
      stopAudio();
      
      if (audioPlayerRef.current) {
        audioPlayerRef.current = null;
      }
    };
  }, []);

  return {
    isEnabled,
    isPlaying,
    isSpeakingComplete,
    setEnabled: (enabled: boolean) => {
      setIsEnabled(enabled);
      if (!enabled && isPlaying) {
        stopAudio();
      }
    },
    playAudio,         // For complete messages
    streamSpeech,      // For streaming tokens
    finishSpeech,      // Call when message is complete
    resetSpeech,       // Call before starting a new message
    stopAudio
  };
};
