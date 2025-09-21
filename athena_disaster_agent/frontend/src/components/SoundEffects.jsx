import React, { useState, useEffect } from 'react';

const SoundEffects = ({ enabled = true }) => {
  const [audioContext, setAudioContext] = useState(null);
  const [sounds, setSounds] = useState({});

  useEffect(() => {
    if (enabled && !audioContext) {
      const ctx = new (window.AudioContext || window.webkitAudioContext)();
      setAudioContext(ctx);
      
      // Create professional sound effects
      const createTone = (frequency, duration, type = 'sine', volume = 0.1) => {
        return () => {
          if (ctx.state === 'suspended') {
            ctx.resume();
          }
          
          const oscillator = ctx.createOscillator();
          const gainNode = ctx.createGain();
          
          oscillator.connect(gainNode);
          gainNode.connect(ctx.destination);
          
          oscillator.frequency.setValueAtTime(frequency, ctx.currentTime);
          oscillator.type = type;
          
          gainNode.gain.setValueAtTime(0, ctx.currentTime);
          gainNode.gain.linearRampToValueAtTime(volume, ctx.currentTime + 0.01);
          gainNode.gain.exponentialRampToValueAtTime(0.001, ctx.currentTime + duration);
          
          oscillator.start(ctx.currentTime);
          oscillator.stop(ctx.currentTime + duration);
        };
      };

      const createChord = (frequencies, duration, volume = 0.05) => {
        return () => {
          if (ctx.state === 'suspended') {
            ctx.resume();
          }
          
          frequencies.forEach((freq, index) => {
            setTimeout(() => {
              const oscillator = ctx.createOscillator();
              const gainNode = ctx.createGain();
              
              oscillator.connect(gainNode);
              gainNode.connect(ctx.destination);
              
              oscillator.frequency.setValueAtTime(freq, ctx.currentTime);
              oscillator.type = 'sine';
              
              gainNode.gain.setValueAtTime(0, ctx.currentTime);
              gainNode.gain.linearRampToValueAtTime(volume, ctx.currentTime + 0.01);
              gainNode.gain.exponentialRampToValueAtTime(0.001, ctx.currentTime + duration);
              
              oscillator.start(ctx.currentTime);
              oscillator.stop(ctx.currentTime + duration);
            }, index * 50);
          });
        };
      };

      // Professional sound palette
      const newSounds = {
        // Message sounds
        messageSent: createTone(600, 0.15, 'triangle', 0.08),
        messageReceived: createChord([400, 500], 0.3),
        
        // Voice interaction
        voiceStart: createTone(800, 0.2, 'sine', 0.06),
        voiceStop: createTone(600, 0.2, 'sine', 0.06),
        voiceError: createTone(300, 0.4, 'sawtooth', 0.05),
        
        // System feedback
        success: createChord([523, 659, 784], 0.4), // C-E-G major chord
        error: createTone(200, 0.6, 'triangle', 0.08),
        warning: createTone(440, 0.3, 'square', 0.05),
        
        // Emergency sounds
        emergency: () => {
          // Emergency alert pattern
          for (let i = 0; i < 3; i++) {
            setTimeout(() => {
              createTone(880, 0.2, 'square', 0.1)();
              setTimeout(() => createTone(660, 0.2, 'square', 0.1)(), 200);
            }, i * 600);
          }
        },
        
        // Typing feedback
        typing: createTone(400, 0.05, 'sine', 0.03),
        
        // Connection status
        connected: createChord([523, 659], 0.3),
        disconnected: createTone(220, 0.5, 'triangle', 0.06)
      };

      setSounds(newSounds);
    }
  }, [enabled, audioContext]);

  // Expose sounds globally
  useEffect(() => {
    if (Object.keys(sounds).length > 0) {
      window.athenaSounds = sounds;
      
      // Auto-play connection sound when sounds are ready
      setTimeout(() => {
        if (sounds.connected) sounds.connected();
      }, 500);
    }
  }, [sounds]);

  return null;
};

export default SoundEffects;
