// src/services/voice/SpeechToTextService.ts
import { useState, useRef, useEffect } from 'react';

/**
 * Type for STT options
 */
export interface SttOptions {
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
}

/**
 * Hook for using speech-to-text functionality
 */
export const useSpeechToText = (options: SttOptions = {}) => {
  // Default options - reverted to working values
  const defaultOptions: Required<SttOptions> = {
    silenceThreshold: 15,
    silentFramesToProcess: 8,
    sampleRate: 48000,
    languageCode: 'en-US',
    apiUrl: `${window.location.protocol}//${window.location.host}/api/voice/speech-to-text`,
    onTranscription: () => {},
    onAudioLevelChange: () => {},
    onStatusChange: () => {},
  };

  // Merge provided options with defaults
  const opts = { ...defaultOptions, ...options };

  // States
  const [isListening, setIsListening] = useState(false);
  const [audioLevel, setAudioLevel] = useState(0);
  const [recordingStatus, setRecordingStatus] = useState('');

  // Refs
  const mediaRecorderRef = useRef<MediaRecorder | null>(null);
  const audioChunksRef = useRef<Blob[]>([]);
  const silenceDetectionRef = useRef<NodeJS.Timeout | null>(null);
  const isProcessingRef = useRef<boolean>(false);
  const audioContextRef = useRef<AudioContext | null>(null);
  const analyserRef = useRef<AnalyserNode | null>(null);
  const silentFrameCountRef = useRef<number>(0);
  const hadSpeechRef = useRef<boolean>(false);

  // Update the audio level and call the callback
  const updateAudioLevel = (level: number) => {
    setAudioLevel(level);
    opts.onAudioLevelChange(level);
  };

  // Update the status and call the callback
  const updateStatus = (status: string) => {
    setRecordingStatus(status);
    opts.onStatusChange(status);
  };

  // Process audio data from recorder
  const processAudioChunks = async () => {
    if (isProcessingRef.current || audioChunksRef.current.length === 0) {
      return;
    }
    
    isProcessingRef.current = true;
    
    try {
      // Filter out very small chunks
      const validChunks = audioChunksRef.current.filter(chunk => chunk.size > 100);
      
      if (validChunks.length === 0) {
        console.log('No valid audio chunks to process');
        // Don't clear chunks here - let them accumulate
        isProcessingRef.current = false;
        return;
      }
      
      // Create a blob from the audio chunks
      const mimeType = mediaRecorderRef.current?.mimeType || 'audio/webm';
      const audioBlob = new Blob(validChunks, { type: mimeType });
      
      // Skip very small audio files
      if (audioBlob.size < 1000) {
        console.log(`Audio too small (${audioBlob.size} bytes), skipping`);
        // Don't clear chunks here - let them accumulate
        isProcessingRef.current = false;
        return;
      }
      
      console.log(`Processing audio: ${audioBlob.size} bytes, ${validChunks.length} chunks`);
      
      // CRITICAL FIX: Only clear chunks AFTER we create the blob but BEFORE processing
      // This ensures the MediaRecorder can continue adding new chunks while we process
      const chunksToProcess = [...audioChunksRef.current];
      audioChunksRef.current = []; // Clear for new chunks
      
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
          console.log('Got transcript:', transcript);
          opts.onTranscription(transcript);
        }
      } else if (data.message === "No speech detected") {
        console.log('No speech detected in this segment, continuing to listen');
      } else if (data.error) {
        console.warn('STT processing error:', data.error);
      }
      
    } catch (error) {
      console.error('Error processing audio:', error);
    } finally {
      isProcessingRef.current = false;
      // Reset speech detection flags to prepare for next utterance
      hadSpeechRef.current = false;
      silentFrameCountRef.current = 0;
      
      console.log(`Audio processing complete. Continuing to listen for more speech...`);
    }
  };

  // Silence detection function
  const detectSilence = () => {
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
    
    // Check if audio is silent
    const isSilent = average < opts.silenceThreshold;
    
    if (isSilent) {
      silentFrameCountRef.current++;
      
      // Process audio after enough silent frames if we had speech
      if (silentFrameCountRef.current >= opts.silentFramesToProcess && 
          hadSpeechRef.current && 
          audioChunksRef.current.length > 0) {
        console.log(`Detected silence after speech, processing audio...`);
        processAudioChunks();
        // Note: processAudioChunks will reset these flags
      }
    } else {
      // Reset silence counter and mark that we detected speech
      silentFrameCountRef.current = 0;
      hadSpeechRef.current = true;
    }
  };

  // Start continuous listening
  const startListening = async () => {
    try {
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
      
      if (stream.getAudioTracks().length === 0) {
        throw new Error('No audio tracks found in the media stream');
      }
      
      // Initialize tracking variables
      silentFrameCountRef.current = 0;
      hadSpeechRef.current = false;
      
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
        audioBitsPerSecond: 128000
      };
      
      console.log('Creating MediaRecorder with options:', options);
      const mediaRecorder = new MediaRecorder(stream, options);
      mediaRecorderRef.current = mediaRecorder;
      audioChunksRef.current = [];
      
      // Handle data available
      mediaRecorder.ondataavailable = (event) => {
        if (event.data.size > 0) {
          audioChunksRef.current.push(event.data);
          console.log(`Audio chunk received: ${event.data.size} bytes`);
        }
      };
      
      mediaRecorder.onerror = (event) => {
        console.error('MediaRecorder error:', event);
        stopListening();
      };
      
      // Start recording in chunks
      mediaRecorder.start(1000); // 1 second chunks
      
      // Start silence detection
      silenceDetectionRef.current = setInterval(detectSilence, 100);
      
      setIsListening(true);
      updateStatus('Listening continuously... Speak and I\'ll transcribe your words');
      
      // Clear status after a few seconds
      setTimeout(() => {
        if (isListening) {
          updateStatus('');
        }
      }, 3000);
      
    } catch (error: any) {
      console.error('Error starting listening:', error);
      setIsListening(false);
      
      if (error.name === 'NotAllowedError') {
        updateStatus('Microphone access denied. Please allow microphone access.');
      } else if (error.name === 'NotFoundError') {
        updateStatus('No microphone found. Please connect a microphone.');
      } else if (error.name === 'NotReadableError' || error.name === 'AbortError') {
        updateStatus('Microphone is busy. Please close other apps using the microphone.');
      } else {
        updateStatus(`Error: ${error.message}`);
      }
      
      setTimeout(() => updateStatus(''), 5000);
    }
  };

  // Stop continuous listening
  const stopListening = () => {
    console.log('Stopping listening...');
    
    // Clear silence detection
    if (silenceDetectionRef.current) {
      clearInterval(silenceDetectionRef.current);
      silenceDetectionRef.current = null;
    }
    
    // Stop media recorder
    if (mediaRecorderRef.current && mediaRecorderRef.current.state === 'recording') {
      mediaRecorderRef.current.stop();
    }
    
    // Stop audio tracks
    if (mediaRecorderRef.current?.stream) {
      mediaRecorderRef.current.stream.getTracks().forEach(track => track.stop());
    }
    
    // Close audio context
    if (audioContextRef.current) {
      audioContextRef.current.close();
      audioContextRef.current = null;
      analyserRef.current = null;
    }
    
    // Process any remaining audio chunks
    if (audioChunksRef.current.length > 0) {
      console.log('Processing remaining audio chunks before stopping');
      processAudioChunks();
    }
    
    // Reset state
    updateAudioLevel(0);
    setIsListening(false);
    updateStatus('');
    silentFrameCountRef.current = 0;
    hadSpeechRef.current = false;
  };

  // Toggle listening
  const toggleListening = () => {
    if (isListening) {
      stopListening();
    } else {
      startListening();
    }
  };

  // Cleanup effect
  useEffect(() => {
    return () => {
      if (silenceDetectionRef.current) {
        clearInterval(silenceDetectionRef.current);
      }
      
      if (mediaRecorderRef.current && mediaRecorderRef.current.state === 'recording') {
        mediaRecorderRef.current.stop();
        if (mediaRecorderRef.current.stream) {
          mediaRecorderRef.current.stream.getTracks().forEach(track => track.stop());
        }
      }
      
      if (audioContextRef.current) {
        audioContextRef.current.close();
      }
    };
  }, []);

  return {
    isListening,
    audioLevel,
    recordingStatus,
    startListening,
    stopListening,
    toggleListening
  };
};
