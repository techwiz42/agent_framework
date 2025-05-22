// src/services/voice/SpeechToTextService.ts
import { useState, useRef, useEffect, useCallback } from 'react';

/**
 * Type for STT options
 */
export interface SttOptions {
  /** Whether to auto-start when enabled */
  autoStart?: boolean;
  /** Minimum volume level to consider as speech */
  silenceThreshold?: number;
  /** Number of silent frames before processing */
  silentFramesToProcess?: number;
  /** Sample rate for audio recording */
  sampleRate?: number;
  /** Language code for speech recognition */
  languageCode?: string;
  /** API URL for the speech-to-text service */
  apiUrl?: string;
  /** Callback when transcription is received */
  onTranscription?: (text: string) => void;
  /** Callback when audio level changes */
  onAudioLevelChange?: (level: number) => void;
  /** Callback when recording status changes */
  onStatusChange?: (status: string) => void;
  /** Callback when listening state changes */
  onListeningChange?: (isListening: boolean) => void;
}

/**
 * Enhanced STT service with full lifecycle management
 */
export const useSpeechToText = (options: SttOptions = {}) => {
  // Default options - simplified for reliability
  const defaultOptions: Required<SttOptions> = {
    autoStart: false,
    silenceThreshold: 15,
    silentFramesToProcess: 6,  // Reduced from 8 to process more frequently (600ms of silence)
    sampleRate: 48000,
    languageCode: 'en-US',
    apiUrl: `${window.location.protocol}//${window.location.host}/api/voice/speech-to-text`,
    onTranscription: () => {},
    onAudioLevelChange: () => {},
    onStatusChange: () => {},
    onListeningChange: () => {},
  };

  // Merge provided options with defaults
  const opts = { ...defaultOptions, ...options };

  // States
  const [isEnabled, setIsEnabled] = useState(true);
  const [isListening, setIsListening] = useState(false);
  const [audioLevel, setAudioLevel] = useState(0);
  const [recordingStatus, setRecordingStatus] = useState('');
  const [error, setError] = useState<string | null>(null);

  // Refs
  const mediaRecorderRef = useRef<MediaRecorder | null>(null);
  const audioChunksRef = useRef<Blob[]>([]);
  const silenceDetectionRef = useRef<NodeJS.Timeout | null>(null);
  const isProcessingRef = useRef<boolean>(false);
  const audioContextRef = useRef<AudioContext | null>(null);
  const analyserRef = useRef<AnalyserNode | null>(null);
  const silentFrameCountRef = useRef<number>(0);
  const hadSpeechRef = useRef<boolean>(false);
  const streamRef = useRef<MediaStream | null>(null);
  const chunkStartTimeRef = useRef<number>(Date.now());
  const maxChunkDurationRef = useRef<number>(20000); // 20 seconds max chunk duration

  // Update the audio level and call the callback
  const updateAudioLevel = useCallback((level: number) => {
    setAudioLevel(level);
    opts.onAudioLevelChange(level);
  }, [opts]);

  // Update the status and call the callback
  const updateStatus = useCallback((status: string) => {
    setRecordingStatus(status);
    opts.onStatusChange(status);
  }, [opts]);

  // Update listening state
  const updateListeningState = useCallback((listening: boolean) => {
    setIsListening(listening);
    opts.onListeningChange(listening);
  }, [opts]);

  // Process audio data from recorder - simplified approach
  const processAudioChunks = useCallback(async () => {
    if (isProcessingRef.current || audioChunksRef.current.length === 0) {
      return;
    }
    
    isProcessingRef.current = true;
    
    // Take a snapshot of current chunks and clear immediately to prevent duplicate processing
    const chunksToProcess = [...audioChunksRef.current];
    audioChunksRef.current = [];
    
    const processingDuration = Date.now() - chunkStartTimeRef.current;
    console.log(`Starting to process ${chunksToProcess.length} audio chunks (accumulated over ${processingDuration}ms)`);
    
    let audioBlob: Blob | null = null;
    
    try {
      // Filter out very small chunks
      const validChunks = chunksToProcess.filter(chunk => chunk.size > 100);
      
      if (validChunks.length === 0) {
        console.log('No valid audio chunks to process');
        isProcessingRef.current = false;
        chunkStartTimeRef.current = Date.now();
        return;
      }
      
      // Create a blob from the audio chunks
      const mimeType = mediaRecorderRef.current?.mimeType || 'audio/webm';
      audioBlob = new Blob(validChunks, { type: mimeType });
      
      // Skip very small audio files
      if (audioBlob.size < 2000) {
        console.log(`Audio too small (${audioBlob.size} bytes), skipping`);
        isProcessingRef.current = false;
        chunkStartTimeRef.current = Date.now();
        return;
      }
      
      // Check if audio is too large (over ~50 seconds at typical bitrates)
      const maxBlobSize = 3 * 1024 * 1024; // 3MB limit (more conservative)
      if (audioBlob.size > maxBlobSize) {
        console.warn(`⚠️ Audio too large (${(audioBlob.size/1024/1024).toFixed(1)}MB), truncating to prevent API errors`);
        // Take only the first part of the audio
        const truncatedBlob = audioBlob.slice(0, maxBlobSize, mimeType);
        console.log(`✂️ Truncated to ${(truncatedBlob.size/1024/1024).toFixed(1)}MB`);
        
        // Process with truncated blob
        const fileName = `recording_${Date.now()}.webm`;
        const formData = new FormData();
        formData.append('audio_file', truncatedBlob, fileName);
        formData.append('language_code', opts.languageCode);
        formData.append('sample_rate', opts.sampleRate.toString());
        formData.append('model', 'default');
        formData.append('content_type', mimeType);
        formData.append('is_webm', mimeType.includes('webm') ? 'true' : 'false');
        
        const response = await fetch(opts.apiUrl, {
          method: 'POST',
          body: formData,
        });
        
        if (!response.ok) {
          const errorText = await response.text();
          console.error('STT Server error:', response.status, errorText);
          throw new Error(`Server responded with status ${response.status}: ${errorText}`);
        }
        
        const data = await response.json();
        console.log('STT response:', data);
        
        if (data.success && data.transcript) {
          const transcript = data.transcript.trim();
          if (transcript) {
            console.log('✅ Got transcript:', transcript);
            opts.onTranscription(transcript);
          }
        }
        
        isProcessingRef.current = false;
        silentFrameCountRef.current = 0;
        hadSpeechRef.current = false;
        chunkStartTimeRef.current = Date.now();
        return;
      }
      
      console.log(`Processing audio: ${(audioBlob.size/1024).toFixed(1)}KB from ${validChunks.length} chunks`);
      
      // Send the audio blob to the backend for STT
      const fileName = `recording_${Date.now()}.webm`;
      const formData = new FormData();
      formData.append('audio_file', audioBlob, fileName);
      formData.append('language_code', opts.languageCode);
      formData.append('sample_rate', opts.sampleRate.toString());
      formData.append('model', 'default');
      formData.append('content_type', mimeType);
      formData.append('is_webm', mimeType.includes('webm') ? 'true' : 'false');
      
      const response = await fetch(opts.apiUrl, {
        method: 'POST',
        body: formData,
      });
      
      if (!response.ok) {
        const errorText = await response.text();
        console.error('STT Server error:', response.status, errorText);
        throw new Error(`Server responded with status ${response.status}: ${errorText}`);
      }
      
      const data = await response.json();
      console.log('STT response:', data);
      
      if (data.success && data.transcript) {
        const transcript = data.transcript.trim();
        if (transcript) {
          console.log('✅ Got transcript:', transcript);
          opts.onTranscription(transcript);
        }
      } else if (data.message === "No speech detected") {
        console.log('⚠️ No speech detected in this segment');
      } else if (data.error) {
        console.warn('❌ STT processing error:', data.error);
      }
      
    } catch (error) {
      console.error('❌ Error processing audio:', error);
      
      // More specific error handling
      let errorMessage = 'Processing error: ';
      if (error instanceof Error) {
        errorMessage += error.message;
        
        // Check for specific error types
        if (error.message.includes('too long') || error.message.includes('1 min')) {
          errorMessage = 'Audio segment too long. Try speaking in shorter segments.';
          if (audioBlob) {
            console.error(`Audio was ${(audioBlob.size/1024).toFixed(0)}KB, accumulated over ${(processingDuration/1000).toFixed(1)}s`);
          }
        } else if (error.message.includes('400')) {
          errorMessage = 'Invalid audio format or parameters.';
        } else if (error.message.includes('500')) {
          errorMessage = 'Server error. Please try again.';
        }
      } else {
        errorMessage += 'Unknown error';
      }
      
      setError(errorMessage);
      
      // Clear error after 5 seconds
      setTimeout(() => setError(null), 5000);
    } finally {
      isProcessingRef.current = false;
      // Reset silence counter for next detection cycle
      silentFrameCountRef.current = 0;
      hadSpeechRef.current = false;
      chunkStartTimeRef.current = Date.now(); // Reset timer for next chunk
      console.log('✅ Processing complete. Ready for next speech...');
    }
  }, [opts]);

  // Silence detection function
  const detectSilence = useCallback(() => {
    if (!analyserRef.current) return;
    
    const bufferLength = analyserRef.current.frequencyBinCount;
    const dataArray = new Uint8Array(bufferLength);
    analyserRef.current.getByteFrequencyData(dataArray);
    
    // Calculate average volume
    let sum = 0;
    for (let i = 0; i < bufferLength; i++) {
      sum += dataArray[i];
    }
    const average = sum / bufferLength;
    
    // Update audio level for UI feedback
    updateAudioLevel(Math.min(100, Math.round(average * 2)));
    
    // Check if we've been accumulating chunks for too long
    const currentTime = Date.now();
    const chunkDuration = currentTime - chunkStartTimeRef.current;
    
    // Force processing if we've accumulated more than 20 seconds of audio
    if (chunkDuration > maxChunkDurationRef.current && 
        audioChunksRef.current.length > 0 && 
        !isProcessingRef.current) {
      console.log(`⏱️ Force processing audio after ${(chunkDuration/1000).toFixed(1)}s of accumulation (${audioChunksRef.current.length} chunks)`);
      processAudioChunks();
      return;
    }
    
    // Check if audio is silent
    const isSilent = average < opts.silenceThreshold;
    
    if (isSilent) {
      silentFrameCountRef.current++;
      
      // Process audio after enough silent frames if we had speech AND not already processing
      if (silentFrameCountRef.current >= opts.silentFramesToProcess && 
          hadSpeechRef.current && 
          audioChunksRef.current.length > 0 &&
          !isProcessingRef.current) {
        console.log(`Detected ${silentFrameCountRef.current} silent frames after speech, processing audio...`);
        processAudioChunks();
      }
    } else {
      // Reset silence counter and mark that we detected speech
      silentFrameCountRef.current = 0;
      hadSpeechRef.current = true;
    }
  }, [opts.silenceThreshold, opts.silentFramesToProcess, processAudioChunks, updateAudioLevel]);

  // Start continuous listening
  const startListening = useCallback(async () => {
    // Return early if already listening
    if (mediaRecorderRef.current && mediaRecorderRef.current.state === 'recording') {
      console.log('Already listening');
      return;
    }

    if (!isEnabled) {
      console.log('STT is disabled');
      return;
    }

    try {
      setError(null);  // Clear any previous errors
      updateStatus('Requesting microphone access...');
      
      if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) {
        throw new Error('Browser does not support microphone access');
      }
      
      const constraints = {
        audio: {
          echoCancellation: true,
          noiseSuppression: true,
          autoGainControl: true,
          channelCount: 1,
          sampleRate: opts.sampleRate,
        }
      };
      
      console.log('Requesting microphone access...');
      const stream = await navigator.mediaDevices.getUserMedia(constraints);
      streamRef.current = stream;
      
      if (stream.getAudioTracks().length === 0) {
        throw new Error('No audio tracks found in the media stream');
      }
      
      // Initialize tracking variables
      silentFrameCountRef.current = 0;
      hadSpeechRef.current = false;
      chunkStartTimeRef.current = Date.now();
      
      // Set up audio analysis
      audioContextRef.current = new AudioContext();
      const audioSource = audioContextRef.current.createMediaStreamSource(stream);
      analyserRef.current = audioContextRef.current.createAnalyser();
      analyserRef.current.fftSize = 256;
      audioSource.connect(analyserRef.current);
      
      // Determine best MIME type
      let mimeType = 'audio/webm;codecs=opus';
      if (!MediaRecorder.isTypeSupported(mimeType)) {
        const supportedTypes = ['audio/webm', 'audio/ogg;codecs=opus', 'audio/wav'];
        for (const type of supportedTypes) {
          if (MediaRecorder.isTypeSupported(type)) {
            mimeType = type;
            break;
          }
        }
      }
      
      const options = { 
        mimeType,
        audioBitsPerSecond: 96000  // Reduced from 128000 to 96000 for smaller files while maintaining quality
      };
      
      console.log('Creating MediaRecorder with options:', options);
      const mediaRecorder = new MediaRecorder(stream, options);
      mediaRecorderRef.current = mediaRecorder;
      audioChunksRef.current = [];
      
      // Handle data available
      mediaRecorder.ondataavailable = (event) => {
        if (event.data.size > 0) {
          audioChunksRef.current.push(event.data);
          console.log(`Audio chunk received: ${event.data.size} bytes, total chunks: ${audioChunksRef.current.length}`);
          
          // Safety check: if we have too many chunks (roughly 20 seconds worth), force processing
          if (audioChunksRef.current.length > 40 && !isProcessingRef.current) {
            console.warn(`⚠️ Too many chunks accumulated (${audioChunksRef.current.length}), forcing processing`);
            processAudioChunks();
          }
        }
      };
      
      mediaRecorder.onerror = (event) => {
        console.error('MediaRecorder error:', event);
        stopListening();
      };
      
      // Start recording with smaller chunks for more frequent processing
      mediaRecorder.start(500); // 500ms chunks instead of 1000ms
      
      // Start silence detection
      silenceDetectionRef.current = setInterval(detectSilence, 100);
      
      updateListeningState(true);
      updateStatus('Listening... Speak and I\'ll transcribe your words');
      
      // Clear status after a few seconds
      setTimeout(() => {
        if (isListening) {
          updateStatus('');
        }
      }, 3000);
      
    } catch (error: any) {
      console.error('Error starting listening:', error);
      updateListeningState(false);
      
      if (error.name === 'NotAllowedError') {
        setError('Microphone access denied');
        updateStatus('Microphone access denied. Please allow microphone access.');
      } else if (error.name === 'NotFoundError') {
        setError('No microphone found');
        updateStatus('No microphone found. Please connect a microphone.');
      } else if (error.name === 'NotReadableError' || error.name === 'AbortError') {
        setError('Microphone is busy');
        updateStatus('Microphone is busy. Please close other apps using the microphone.');
      } else {
        setError(error.message);
        updateStatus(`Error: ${error.message}`);
      }
      
      setTimeout(() => updateStatus(''), 5000);
    }
  }, [isListening, isEnabled, opts.sampleRate, detectSilence, updateListeningState, updateStatus]);

  // Stop continuous listening
  const stopListening = useCallback(() => {
    console.log('Stopping listening...');
    
    // Clear silence detection
    if (silenceDetectionRef.current) {
      clearInterval(silenceDetectionRef.current);
      silenceDetectionRef.current = null;
    }
    
    // Stop media recorder
    if (mediaRecorderRef.current && mediaRecorderRef.current.state === 'recording') {
      mediaRecorderRef.current.stop();
      mediaRecorderRef.current = null;
    }
    
    // Stop audio tracks
    if (streamRef.current) {
      streamRef.current.getTracks().forEach(track => track.stop());
      streamRef.current = null;
    }
    
    // Close audio context
    if (audioContextRef.current && audioContextRef.current.state !== 'closed') {
      audioContextRef.current.close();
      audioContextRef.current = null;
      analyserRef.current = null;
    }
    
    // Clear any remaining audio chunks without processing
    // (We don't want to process partial audio when manually stopping)
    audioChunksRef.current = [];
    
    // Reset state
    updateAudioLevel(0);
    updateListeningState(false);
    updateStatus('');
    silentFrameCountRef.current = 0;
    hadSpeechRef.current = false;
    isProcessingRef.current = false;
    chunkStartTimeRef.current = Date.now();
  }, [updateAudioLevel, updateListeningState, updateStatus]);

  // Reset STT state (useful after sending a message)
  const resetStt = useCallback(() => {
    console.log('🔄 Resetting STT state for next speech...');
    silentFrameCountRef.current = 0;
    hadSpeechRef.current = false;
    chunkStartTimeRef.current = Date.now();
    
    // Clear any accumulated chunks
    if (audioChunksRef.current.length > 0) {
      console.log(`🗑️ Clearing ${audioChunksRef.current.length} unprocessed audio chunks`);
      audioChunksRef.current = [];
    }
    
    // Clear any processing state
    isProcessingRef.current = false;
    
    console.log('✅ STT reset complete - ready for new speech');
  }, []);

  // Toggle listening
  const toggleListening = useCallback(async () => {
    // Check the actual MediaRecorder state instead of React state
    if (mediaRecorderRef.current && mediaRecorderRef.current.state === 'recording') {
      stopListening();
    } else {
      await startListening();
    }
  }, [startListening, stopListening]);

  // Enable/disable STT
  const setEnabled = useCallback((enabled: boolean) => {
    setIsEnabled(enabled);
    if (!enabled && isListening) {
      stopListening();
    }
  }, [isListening, stopListening]);

  // Cleanup effect
  useEffect(() => {
    return () => {
      if (silenceDetectionRef.current) {
        clearInterval(silenceDetectionRef.current);
      }
      
      if (mediaRecorderRef.current && mediaRecorderRef.current.state === 'recording') {
        mediaRecorderRef.current.stop();
      }
      
      if (streamRef.current) {
        streamRef.current.getTracks().forEach(track => track.stop());
      }
      
      if (audioContextRef.current) {
        audioContextRef.current.close();
      }
    };
  }, []);

  return {
    // States
    isEnabled,
    isListening,
    audioLevel,
    recordingStatus,
    error,
    
    // Actions
    startListening,
    stopListening,
    toggleListening,
    resetStt,
    setEnabled,
  };
};
