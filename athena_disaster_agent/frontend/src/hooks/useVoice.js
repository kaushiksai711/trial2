import { useState, useRef, useCallback } from 'react';

export const useVoice = () => {
  const [voiceConfig, setVoiceConfig] = useState({
    isSupported: 'webkitSpeechRecognition' in window || 'SpeechRecognition' in window,
    isRecording: false,
    isPlaying: false,
  });

  const recognitionRef = useRef(null);
  const synthRef = useRef(window.speechSynthesis);

  const startListening = useCallback((onResult, onError) => {
    if (!voiceConfig.isSupported) {
      onError?.('Speech recognition not supported in this browser');
      return;
    }

    try {
      const SpeechRecognition = window.webkitSpeechRecognition || window.SpeechRecognition;
      recognitionRef.current = new SpeechRecognition();
      
      recognitionRef.current.continuous = false;
      recognitionRef.current.interimResults = false;
      recognitionRef.current.lang = 'en-US';

      recognitionRef.current.onstart = () => {
        setVoiceConfig(prev => ({ ...prev, isRecording: true }));
      };

      recognitionRef.current.onresult = (event) => {
        const transcript = event.results[0][0].transcript;
        onResult(transcript);
        setVoiceConfig(prev => ({ ...prev, isRecording: false }));
      };

      recognitionRef.current.onerror = (event) => {
        console.error('Speech recognition error:', event.error);
        onError?.(event.error);
        setVoiceConfig(prev => ({ ...prev, isRecording: false }));
      };

      recognitionRef.current.onend = () => {
        setVoiceConfig(prev => ({ ...prev, isRecording: false }));
      };

      recognitionRef.current.start();
    } catch (error) {
      console.error('Voice recognition error:', error);
      onError?.('Failed to start voice recognition');
    }
  }, [voiceConfig.isSupported]);

  const stopListening = useCallback(() => {
    if (recognitionRef.current) {
      recognitionRef.current.stop();
    }
  }, []);

  const speak = useCallback((text) => {
    if (!synthRef.current) return;

    // Stop any current speech
    synthRef.current.cancel();

    const utterance = new SpeechSynthesisUtterance(text);
    utterance.rate = 0.9;
    utterance.pitch = 1.0;
    utterance.volume = 0.8;

    utterance.onstart = () => {
      setVoiceConfig(prev => ({ ...prev, isPlaying: true }));
    };

    utterance.onend = () => {
      setVoiceConfig(prev => ({ ...prev, isPlaying: false }));
    };

    utterance.onerror = () => {
      setVoiceConfig(prev => ({ ...prev, isPlaying: false }));
    };

    synthRef.current.speak(utterance);
  }, []);

  const stopSpeaking = useCallback(() => {
    if (synthRef.current) {
      synthRef.current.cancel();
      setVoiceConfig(prev => ({ ...prev, isPlaying: false }));
    }
  }, []);

  return {
    voiceConfig,
    startListening,
    stopListening,
    speak,
    stopSpeaking,
  };
};
