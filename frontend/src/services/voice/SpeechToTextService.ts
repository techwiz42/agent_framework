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
  /** Number of speaking frames before forcing processing */
  speakingFramesToProcess?: number;
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

// Add hadSpeech and justProcessedAudio to Window interface
declare global {
  interface Window {
    silentFrameCount: number;
    speakingFrameCount: number;
    hadSpeech: boolean;
    justProcessedAudio: boolean;
  }
}

/**
 * Hook for using speech-to-text functionality
 */
export const useSpeechToText = (options: SttOptions = {}) => {
  // Default options
  const defaultOptions: Required<SttOptions> = {
    silenceThreshold: 10, // Lower threshold to detect more subtle sounds
    silentFramesToProcess: 6, // Process audio sooner when silence is detected
    speakingFramesToProcess: 20, // Process audio sooner when speaking
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
  const audioProcessorIntervalRef = useRef<NodeJS.Timeout | null>(null);
  const silenceTimerRef = useRef<NodeJS.Timeout | null>(null);

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
  const processContinuousAudio = async () => {
    if (!mediaRecorderRef.current || audioChunksRef.current.length === 0) {
      return;
    }
    
    try {
      // Filter out tiny chunks that are likely empty, but use a lower threshold
      // to ensure we don't lose speech with quiet beginnings
      const validChunks = audioChunksRef.current.filter(chunk => chunk.size > 50);
      
      if (validChunks.length === 0) {
        console.log('No valid audio chunks to process');
        audioChunksRef.current = []; // Clear chunks for next segment
        return;
      }
      
      // Create a blob from the filtered audio chunks
      const mimeType = mediaRecorderRef.current.mimeType;
      const audioBlob = new Blob(validChunks, { type: mimeType });
      
      // Process even small audio chunks for faster response
      if (audioBlob.size < 500) {
        console.log(`Small audio (${audioBlob.size} bytes), might be brief utterance`);
        // Continue processing anyway for better responsiveness
      }
      
      // Don't show processing status - this improves perceived performance
      // We'll let transcription appear as it happens without UI changes
      
      // Log audio info for debugging
      console.log(`Processing audio: size=${audioBlob.size} bytes, type=${mimeType}`);
      
      // Keep a copy of the current chunks before clearing
      const currentChunks = [...audioChunksRef.current];
      // Clear chunks for next recording immediately to allow parallel processing
      audioChunksRef.current = []; 
      
      // Send the audio blob to the backend for STT
      const fileName = `recording_${Date.now()}.${mimeType.split('/')[1] || 'webm'}`;
      const formData = new FormData();
      formData.append('audio_file', audioBlob, fileName);
      formData.append('language_code', opts.languageCode);
      
      // For WebM/Opus, always send 48000 Hz as sample rate
      if (mimeType.includes('webm') || mimeType.includes('opus')) {
        formData.append('sample_rate', '48000');
      } else {
        formData.append('sample_rate', '16000');
      }
      
      // Add parameters for real-time transcription optimization
      formData.append('model', 'default');
      formData.append('content_type', mimeType);
      formData.append('is_webm', mimeType.includes('webm') ? 'true' : 'false');
      formData.append('partial_results', 'true'); // Request partial results if supported
      
      console.log(`Sending audio for processing: ${audioBlob.size} bytes, ${validChunks.length} chunks`);
      const response = await fetch(opts.apiUrl, {
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
      
      if (data.success) {
        if (data.transcript) {
          // Return transcribed text immediately without delay
          const transcript = data.transcript.trim();
          if (transcript) {
            console.log('Got transcript:', transcript);
            opts.onTranscription(transcript);
          }
        } else if (data.message === "No speech detected") {
          console.log('No speech detected in continuous mode, but handled gracefully');
          // Continue listening since this is expected for silent periods
          window.hadSpeech = false; // Reset speech detection flag
        }
      } else if (data.error) {
        console.log('STT error, but continuing to listen:', data.error);
      }
      
    } catch (error) {
      console.error('Error processing audio segment:', error);
    }
  };

  // Start continuous listening
  const startListening = async () => {
    try {
      updateStatus('Requesting microphone access...');
      
      // Check if mediaDevices is supported
      if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) {
        console.error('Browser does not support mediaDevices API');
        throw new Error('Browser does not support microphone access');
      }
      
      // Use higher quality audio settings with improved noise cancellation
      const constraints = {
        audio: {
          echoCancellation: true,
          noiseSuppression: true,
          autoGainControl: true,
          channelCount: 1,
          sampleRate: opts.sampleRate,
          advanced: [
            { echoCancellation: { exact: true } },
            { noiseSuppression: { exact: true } },
            { autoGainControl: { ideal: true } }
          ]
        }
      };
      
      console.log('Requesting microphone access for continuous listening...');
      const stream = await navigator.mediaDevices.getUserMedia(constraints);
      
      if (stream.getAudioTracks().length === 0) {
        throw new Error('No audio tracks found in the media stream');
      }
      
      // Initialize tracking variables for better audio processing
      window.silentFrameCount = 0;
      window.speakingFrameCount = 0;
      window.hadSpeech = false;
      window.justProcessedAudio = false;
      
      // Log actual audio track settings to verify sample rate
      const audioTrack = stream.getAudioTracks()[0];
      const trackSettings = audioTrack.getSettings();
      console.log('Actual audio settings:', trackSettings);
      console.log(`Actual sample rate: ${trackSettings.sampleRate}, requested: ${opts.sampleRate}`);
      
      // Use the best format for Google STT - prefer WEBM with Opus codec
      let mimeType = 'audio/webm;codecs=opus';
      
      if (!MediaRecorder.isTypeSupported(mimeType)) {
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
      }
      
      // Use higher audioBitsPerSecond for better audio quality
      const options = { 
        mimeType,
        audioBitsPerSecond: 256000
      };
      
      console.log('Creating MediaRecorder with options:', options);
      const mediaRecorder = new MediaRecorder(stream, options);
      mediaRecorderRef.current = mediaRecorder;
      audioChunksRef.current = [];
      
      // Set up silence detection using AudioContext
      const audioContext = new AudioContext();
      const audioSource = audioContext.createMediaStreamSource(stream);
      const analyser = audioContext.createAnalyser();
      analyser.fftSize = 256;
      audioSource.connect(analyser);
      
      const bufferLength = analyser.frequencyBinCount;
      const dataArray = new Uint8Array(bufferLength);
      
      // Function to detect if audio is silent
      const detectSilence = () => {
        analyser.getByteFrequencyData(dataArray);
        
        // Calculate average volume
        let sum = 0;
        for (let i = 0; i < bufferLength; i++) {
          sum += dataArray[i];
        }
        const average = sum / bufferLength;
        
        // Update audio level for UI feedback (0-100 scale)
        updateAudioLevel(Math.min(100, Math.round(average * 2)));
        
        // Track silent frames for more reliable silence detection
        if (!window.silentFrameCount) {
          window.silentFrameCount = 0;
          window.speakingFrameCount = 0;
        }
        
        // Check if audio is silent based on threshold
        const isSilent = average < opts.silenceThreshold;
        
        if (isSilent) {
          window.silentFrameCount++;
          window.speakingFrameCount = 0;
          
          // Process audio after fewer silent frames for faster response
          // Process as soon as we detect a brief pause
          if (window.silentFrameCount >= Math.min(3, opts.silentFramesToProcess) && 
              silenceTimerRef.current === null && 
              audioChunksRef.current.length > 2 && 
              window.hadSpeech) {
            console.log(`Detected ${window.silentFrameCount} silent frames, processing audio...`);
            
            // Process audio immediately
            processContinuousAudio();
            window.silentFrameCount = 0;
            // Don't reset hadSpeech flag - this maintains context between utterances
            
            // Set marker to avoid double-processing but with shorter delay
            window.justProcessedAudio = true;
            setTimeout(() => {
              window.justProcessedAudio = false;
            }, 200); // Reduced from 500ms to 200ms
          }
        } else {
          window.speakingFrameCount++;
          window.silentFrameCount = 0;
          window.hadSpeech = true; // Mark that we detected speech
          
          // Force process after fewer consecutive speaking frames for faster feedback
          if (window.speakingFrameCount >= Math.min(10, opts.speakingFramesToProcess) && 
              audioChunksRef.current.length >= 3 && 
              !window.justProcessedAudio) {
            console.log(`Detected ${window.speakingFrameCount} speaking frames, force processing audio...`);
            processContinuousAudio();
            window.speakingFrameCount = 0;
            
            // Set marker that we just processed audio with shorter delay
            window.justProcessedAudio = true;
            setTimeout(() => {
              window.justProcessedAudio = false;
            }, 100); // Reduced from 500ms to 100ms
          }
          
          // If we detect sound, clear any pending silence timer
          if (silenceTimerRef.current !== null) {
            clearTimeout(silenceTimerRef.current);
            silenceTimerRef.current = null;
          }
        }
        
        // Log volume levels occasionally for debugging
        if (Math.random() < 0.01) {
          console.log(`Audio level: ${average.toFixed(2)}, silent: ${isSilent}, ` +
                     `silent frames: ${window.silentFrameCount}, speaking frames: ${window.speakingFrameCount}`);
        }
      };
      
      // Set up interval to periodically check for silence at a faster rate
      const processorInterval = setInterval(detectSilence, 50); // Increased from 100ms to 50ms
      audioProcessorIntervalRef.current = processorInterval;
      
      // Event handler for data available - process data more frequently
      mediaRecorder.ondataavailable = (event) => {
        if (event.data.size > 0) {
          audioChunksRef.current.push(event.data);
          console.log(`Received audio chunk: ${event.data.size} bytes, type: ${event.data.type}`);
          
          // Process audio more aggressively for real-time transcription
          // Only process if we have enough chunks to make it worthwhile
          if (audioChunksRef.current.length >= 2) {
            processContinuousAudio();
          }
        }
      };
      
      // Use much smaller chunks for more responsive real-time transcription
      mediaRecorder.start(250); // Reduced from 500ms to 250ms
      
      // Add some setup instructions to help users
      setIsListening(true);
      updateStatus('Listening... Speak clearly and I\'ll transcribe your words');
      
      // After 3 seconds, update the status to be less intrusive
      setTimeout(() => {
        if (isListening) {
          updateStatus('');
        }
      }, 3000);
      
    } catch (error: any) {
      console.error('Error starting continuous listening:', error);
      setIsListening(false);
      
      // Handle error cases
      if (error.name === 'NotAllowedError') {
        updateStatus('Microphone access denied. Please check your browser permissions.');
      } else if (error.name === 'NotFoundError') {
        updateStatus('No microphone found. Please connect a microphone and try again.');
      } else if (error.name === 'NotReadableError' || error.name === 'AbortError') {
        updateStatus('Cannot access microphone. It may be in use by another application.');
      } else if (error.message) {
        updateStatus(`Error: ${error.message}`);
      } else {
        updateStatus('Failed to access microphone');
      }
      
      setTimeout(() => {
        updateStatus('');
      }, 5000);
    }
  };

  // Stop continuous listening
  const stopListening = () => {
    if (silenceTimerRef.current) {
      clearTimeout(silenceTimerRef.current);
      silenceTimerRef.current = null;
    }
    
    if (audioProcessorIntervalRef.current) {
      clearInterval(audioProcessorIntervalRef.current);
      audioProcessorIntervalRef.current = null;
    }
    
    // Stop media recorder if active
    if (mediaRecorderRef.current && mediaRecorderRef.current.state === 'recording') {
      mediaRecorderRef.current.stop();
    }
    
    // Stop audio tracks
    if (mediaRecorderRef.current && mediaRecorderRef.current.stream) {
      mediaRecorderRef.current.stream.getTracks().forEach(track => track.stop());
    }
    
    // Process any remaining audio if it's substantial enough
    if (audioChunksRef.current.length > 3) {
      processContinuousAudio();
    } else if (audioChunksRef.current.length > 0) {
      console.log(`Not enough audio chunks (${audioChunksRef.current.length}), discarding`);
      audioChunksRef.current = [];
    }
    
    // Reset audio level
    updateAudioLevel(0);
    setIsListening(false);
    updateStatus('');
  };

  // Cleanup effect
  useEffect(() => {
    return () => {
      // Cleanup function
      if (silenceTimerRef.current) {
        clearTimeout(silenceTimerRef.current);
      }
      
      if (audioProcessorIntervalRef.current) {
        clearInterval(audioProcessorIntervalRef.current);
      }
      
      if (mediaRecorderRef.current && mediaRecorderRef.current.state === 'recording') {
        mediaRecorderRef.current.stop();
        if (mediaRecorderRef.current.stream) {
          mediaRecorderRef.current.stream.getTracks().forEach(track => track.stop());
        }
      }
    };
  }, []);

  return {
    isListening,
    audioLevel,
    recordingStatus,
    startListening,
    stopListening,
    toggleListening: () => {
      if (isListening) {
        stopListening();
      } else {
        startListening();
      }
    }
  };
};
