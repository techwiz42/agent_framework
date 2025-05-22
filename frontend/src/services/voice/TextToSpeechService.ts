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
  
  let cleaned = text
    // Remove markdown headers
    .replace(/#{1,6}\s+/g, '')
    // Remove markdown code blocks with language specification
    .replace(/```[\w]*\n[\s\S]*?```/g, ' code snippet ')
    // Remove markdown code blocks without language
    .replace(/```[\s\S]*?```/g, ' code snippet ')
    // Remove inline code
    .replace(/`([^`]+)`/g, '$1')
    // CRITICAL: Remove all asterisks and markdown formatting
    .replace(/\*\*([^*]+)\*\*/g, '$1')  // Bold
    .replace(/\*([^*]+)\*/g, '$1')      // Italic
    .replace(/\*/g, '')                 // Any remaining asterisks
    .replace(/__([^_]+)__/g, '$1')      // Bold underscores
    .replace(/_([^_]+)_/g, '$1')        // Italic underscores
    .replace(/_/g, '')                  // Any remaining underscores
    // Remove markdown bullets and lists
    .replace(/^\s*[-*+]\s+/gm, '')
    .replace(/^\s*\d+\.\s+/gm, '')
    // Remove URLs but keep linked text
    .replace(/\[([^\]]+)\]\([^\)]+\)/g, '$1')
    // Remove standalone URLs
    .replace(/https?:\/\/\S+/g, 'link')
    // Remove HTML tags
    .replace(/<[^>]*>/g, '')
    // Handle symbols that get pronounced
    .replace(/&/g, ' and ')
    .replace(/\//g, ' or ')
    .replace(/@/g, ' at ')
    .replace(/#/g, ' hash ')
    .replace(/\$/g, ' dollar ')
    .replace(/%/g, ' percent ')
    .replace(/\+/g, ' plus ')
    .replace(/=/g, ' equals ')
    .replace(/\|/g, ' ')
    .replace(/\\/g, ' ')
    .replace(/\^/g, ' ')
    .replace(/~/g, ' ')
    .replace(/`/g, '')
    // Handle common abbreviations
    .replace(/\bTL;DR\b/gi, 'T L D R')
    .replace(/\bUI\b/g, 'U I')
    .replace(/\bAPI\b/g, 'A P I')
    .replace(/\bHTML\b/g, 'H T M L')
    .replace(/\bCSS\b/g, 'C S S')
    .replace(/\bURL\b/g, 'U R L')
    .replace(/\bJSON\b/g, 'J S O N')
    .replace(/\bHTTP\b/g, 'H T T P')
    .replace(/\bSVG\b/g, 'S V G')
    .replace(/\bPDF\b/g, 'P D F')
    .replace(/\bAI\b/g, 'A I')
    .replace(/\bDB\b/g, 'database')
    .replace(/\bJS\b/g, 'JavaScript')
    .replace(/\bTS\b/g, 'TypeScript')
    // Normalize punctuation spacing
    .replace(/\s*\.\s*/g, '. ')
    .replace(/\s*,\s*/g, ', ')
    .replace(/\s*;\s*/g, '; ')
    .replace(/\s*:\s*/g, ': ')
    .replace(/\s*!\s*/g, '! ')
    .replace(/\s*\?\s*/g, '? ')
    // Remove multiple consecutive punctuation
    .replace(/[.]{2,}/g, '.')
    .replace(/[,]{2,}/g, ',')
    .replace(/[?]{2,}/g, '?')
    .replace(/[!]{2,}/g, '!')
    // Remove parentheses content that's often metadata
    .replace(/\([^)]*\)/g, '')
    .replace(/\[[^\]]*\]/g, '')
    // Fix hyphenated words
    .replace(/(\w)-(\w)/g, '$1 $2')
    // Clean up excess whitespace
    .replace(/\s+/g, ' ')
    .trim();
  
  return cleaned;
};

/**
 * Hook for using text-to-speech functionality
 */
export const useTextToSpeech = (options: TtsOptions = {}) => {
  // Default options - optimized for natural speech
  const defaultOptions: Required<TtsOptions> = {
    voiceId: 'en-US-Neural2-C',
    speakingRate: 1.0,
    preprocessText: true,
    useSmartBuffering: true,
    apiUrl: `${window.location.protocol}//${window.location.host}/api/voice/text-to-speech`,
    onPlaybackStart: () => {},
    onPlaybackEnd: () => {},
    onPlaybackError: () => {},
    minChunkSize: 30,    // Minimum for clause boundaries (not used for sentence boundaries)
    chunkPause: 50       // Short pause between chunks
  };

  // Merge provided options with defaults
  const opts = { ...defaultOptions, ...options };

  // States
  const [isEnabled, setIsEnabled] = useState(true);
  const [isPlaying, setIsPlaying] = useState(false);
  const [isSpeakingComplete, setIsSpeakingComplete] = useState(true);

  // Refs
  const audioPlayerRef = useRef<HTMLAudioElement | null>(null);
  const speechBufferRef = useRef<string>('');
  const audioQueueRef = useRef<string[]>([]);
  const processingTimeoutRef = useRef<NodeJS.Timeout | null>(null);
  const isProcessingRef = useRef<boolean>(false);
  
  // Natural sentence boundaries
  const sentenceEnders = ['.', '!', '?'];
  const clauseEnders = [':', ';', ','];

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
        
        if (audioQueueRef.current.length > 0) {
          setTimeout(() => processNextInQueue(), opts.chunkPause);
        } else {
          setIsSpeakingComplete(true);
        }
        return;
      }
      
      console.log('Converting to speech:', processedText.substring(0, 100) + (processedText.length > 100 ? '...' : ''));
      
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
        
        if (audioQueueRef.current.length > 0) {
          setTimeout(() => processNextInQueue(), opts.chunkPause);
        } else {
          setIsSpeakingComplete(true);
        }
        return;
      }
      
      const data = await response.json();
      
      if (data.success && data.audio_base64) {
        const audioBlob = base64ToBlob(data.audio_base64, data.mime_type);
        const audioUrl = URL.createObjectURL(audioBlob);
        
        if (!audioPlayerRef.current) {
          audioPlayerRef.current = new Audio();
        }
        
        audioPlayerRef.current.onended = () => {
          setIsPlaying(false);
          isProcessingRef.current = false;
          opts.onPlaybackEnd();
          
          URL.revokeObjectURL(audioUrl);
          
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
          
          URL.revokeObjectURL(audioUrl);
          
          if (audioQueueRef.current.length > 0) {
            setTimeout(() => processNextInQueue(), opts.chunkPause);
          } else {
            setIsSpeakingComplete(true);
          }
        };
        
        audioPlayerRef.current.src = audioUrl;
        await audioPlayerRef.current.play();
      } else {
        console.error('TTS response missing audio data:', data);
        setIsPlaying(false);
        isProcessingRef.current = false;
        opts.onPlaybackError(new Error('Missing audio data in response'));
        
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
      
      if (audioQueueRef.current.length > 0) {
        setTimeout(() => processNextInQueue(), opts.chunkPause);
      } else {
        setIsSpeakingComplete(true);
      }
    }
  };

  // Chunk text at natural punctuation boundaries for better speech flow
  const createNaturalChunks = (text: string): string[] => {
    if (!text.trim()) return [];
    
    const chunks: string[] = [];
    
    // Split by paragraphs first (double line breaks)
    const paragraphs = text.split(/\n\s*\n/);
    
    for (const paragraph of paragraphs) {
      if (!paragraph.trim()) continue;
      
      // Split at sentence boundaries (.!?) - these create the most natural pauses
      const sentences = paragraph.split(/([.!?]+\s*)/).filter(s => s.trim());
      
      let currentChunk = '';
      
      for (const part of sentences) {
        // If this is a sentence ender, add it to current chunk and finalize
        if (/[.!?]+\s*$/.test(part.trim())) {
          currentChunk += part;
          if (currentChunk.trim()) {
            chunks.push(currentChunk.trim());
            currentChunk = '';
          }
        } else {
          // This is sentence content - check for clause boundaries
          const clauses = part.split(/([;:,]\s*)/).filter(s => s.trim());
          
          for (const clause of clauses) {
            // If adding this clause would be reasonable, add it
            const testChunk = currentChunk + clause;
            
            // If this is a clause ender or we have a reasonable length, consider chunking
            if (/[;:,]\s*$/.test(clause.trim())) {
              currentChunk += clause;
              // Only chunk at commas/semicolons if we have substantial content (30+ chars)
              if (currentChunk.length > 30) {
                chunks.push(currentChunk.trim());
                currentChunk = '';
              }
            } else {
              currentChunk += clause;
            }
          }
        }
      }
      
      // Add any remaining content from this paragraph
      if (currentChunk.trim()) {
        chunks.push(currentChunk.trim());
      }
    }
    
    return chunks.filter(chunk => chunk.trim().length > 0);
  };

  // Process the speech buffer
  const processSpeechBuffer = () => {
    if (!isEnabled || !opts.useSmartBuffering || !speechBufferRef.current.trim()) {
      return;
    }

    const textToProcess = speechBufferRef.current;
    speechBufferRef.current = '';
    
    const chunks = createNaturalChunks(textToProcess);
    
    chunks.forEach(chunk => {
      if (chunk.trim()) {
        audioQueueRef.current.push(chunk);
      }
    });
    
    if (chunks.length > 0) {
      setIsSpeakingComplete(false);
      
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
    
    speechBufferRef.current += text;
    
    if (processingTimeoutRef.current) {
      clearTimeout(processingTimeoutRef.current);
    }
    
    // Check for sentence endings - these are the best natural break points
    const hasSentenceEnd = /[.!?]\s*$/.test(speechBufferRef.current.trim());
    
    // Check for clause endings if we have enough content
    const hasClauseEnd = /[;:,]\s*$/.test(speechBufferRef.current.trim()) && 
                        speechBufferRef.current.length > opts.minChunkSize;
    
    if (hasSentenceEnd || hasClauseEnd) {
      // Natural break point found - process immediately
      processSpeechBuffer();
    } else {
      // No natural break yet - set timeout for processing
      processingTimeoutRef.current = setTimeout(() => {
        if (speechBufferRef.current.trim()) {
          processSpeechBuffer();
        }
      }, 1500);
    }
  };

  // Stream tokens of text for speech
  const streamSpeech = (text: string) => {
    if (!isEnabled) return;
    
    if (opts.useSmartBuffering) {
      addToSpeechBuffer(text);
    } else {
      playAudio(text);
    }
  };

  // Finish streaming speech
  const finishSpeech = () => {
    if (!isEnabled) return;
    
    if (opts.useSmartBuffering && speechBufferRef.current.trim()) {
      processSpeechBuffer();
    }
  };

  // Reset speech state
  const resetSpeech = () => {
    speechBufferRef.current = '';
    
    if (processingTimeoutRef.current) {
      clearTimeout(processingTimeoutRef.current);
      processingTimeoutRef.current = null;
    }
  };

  // Play a complete message
  const playAudio = async (text: string) => {
    if (!isEnabled || !text.trim()) return;
    
    stopAudio();
    resetSpeech();
    
    audioQueueRef.current = [];
    audioQueueRef.current.push(text);
    setIsSpeakingComplete(false);
    
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
    
    audioQueueRef.current = [];
    speechBufferRef.current = '';
    
    if (processingTimeoutRef.current) {
      clearTimeout(processingTimeoutRef.current);
      processingTimeoutRef.current = null;
    }
    
    setIsSpeakingComplete(true);
  };

  // Cleanup effect
  useEffect(() => {
    return () => {
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
    playAudio,
    streamSpeech,
    finishSpeech,
    resetSpeech,
    stopAudio
  };
};
