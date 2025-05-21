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
  /** API URL for the text-to-speech service */
  apiUrl?: string;
  /** Callback when audio playback starts */
  onPlaybackStart?: () => void;
  /** Callback when audio playback ends */
  onPlaybackEnd?: () => void;
  /** Callback when audio playback errors */
  onPlaybackError?: (error: any) => void;
}

/**
 * Hook for using text-to-speech functionality
 */
export const useTextToSpeech = (options: TtsOptions = {}) => {
  // Default options
  const defaultOptions: Required<TtsOptions> = {
    voiceId: 'en-US-Neural2-C',
    speakingRate: 1.0,
    preprocessText: true,
    apiUrl: `${window.location.protocol}//${window.location.host}/api/voice/text-to-speech`,
    onPlaybackStart: () => {},
    onPlaybackEnd: () => {},
    onPlaybackError: () => {},
  };

  // Merge provided options with defaults
  const opts = { ...defaultOptions, ...options };

  // States
  const [isEnabled, setIsEnabled] = useState(false);
  const [isPlaying, setIsPlaying] = useState(false);

  // Refs
  const audioPlayerRef = useRef<HTMLAudioElement | null>(null);

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

  // Play message audio
  const playAudio = async (text: string) => {
    if (!isEnabled || !text.trim()) return;
    
    try {
      setIsPlaying(true);
      opts.onPlaybackStart();
      
      console.log('Converting message to speech:', text.substring(0, 50) + (text.length > 50 ? '...' : ''));
      
      const response = await fetch(opts.apiUrl, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          text: text,
          voice_id: opts.voiceId,
          return_base64: true,
          speaking_rate: opts.speakingRate,
          preprocess_text: opts.preprocessText
        }),
      });
      
      if (!response.ok) {
        const errorText = await response.text();
        console.error('TTS error:', response.status, errorText);
        setIsPlaying(false);
        opts.onPlaybackError(new Error(errorText));
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
          opts.onPlaybackEnd();
        };
        
        audioPlayerRef.current.onerror = (error) => {
          console.error('Audio playback error:', error);
          setIsPlaying(false);
          opts.onPlaybackError(error);
        };
        
        // Set source and play
        audioPlayerRef.current.src = audioUrl;
        await audioPlayerRef.current.play();
      } else {
        console.error('TTS response missing audio data:', data);
        setIsPlaying(false);
        opts.onPlaybackError(new Error('Missing audio data in response'));
      }
    } catch (error) {
      console.error('Error playing TTS audio:', error);
      setIsPlaying(false);
      opts.onPlaybackError(error);
    }
  };

  // Stop audio playback
  const stopAudio = () => {
    if (audioPlayerRef.current) {
      audioPlayerRef.current.pause();
      audioPlayerRef.current.currentTime = 0;
      setIsPlaying(false);
      opts.onPlaybackEnd();
    }
  };

  // Cleanup effect
  useEffect(() => {
    return () => {
      // Cleanup audio element on unmount
      if (audioPlayerRef.current) {
        audioPlayerRef.current.pause();
        audioPlayerRef.current = null;
      }
    };
  }, []);

  return {
    isEnabled,
    isPlaying,
    setEnabled: (enabled: boolean) => {
      setIsEnabled(enabled);
      if (!enabled && isPlaying) {
        stopAudio();
      }
    },
    playAudio,
    stopAudio
  };
};
