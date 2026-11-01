import React, { useEffect, useRef, useState } from 'react';
import { Volume2, VolumeX, Radio } from 'lucide-react';
import { PlaybackState } from '../types';

interface AudioPlayerProps {
  playbackState?: PlaybackState;
  onTrackEnded?: () => void;
}

export const AudioPlayer: React.FC<AudioPlayerProps> = ({ playbackState, onTrackEnded }) => {
  const audioRef = useRef<HTMLAudioElement | null>(null);
  const [isAutoplayBlocked, setIsAutoplayBlocked] = useState(false);
  const [isMuted, setIsMuted] = useState(false);
  const [isPlayingLocally, setIsPlayingLocally] = useState(false);

  const currentTrack = playbackState?.current_queue_item?.track;
  const currentTrackId = currentTrack?.id;
  const audioSrc = currentTrack?.audio_url;

  const lastSyncRef = useRef<{ baseMs: number; receivedAt: number }>({
    baseMs: 0,
    receivedAt: performance.now()
  });

  useEffect(() => {
    if (!playbackState) return;
    lastSyncRef.current = {
      baseMs: playbackState.position_ms || 0,
      receivedAt: performance.now()
    };
  }, [playbackState?.position_ms, playbackState?.version]);

  const getExpectedPositionSeconds = (): number => {
    if (!playbackState) return 0;
    if (playbackState.status !== 'playing') {
      return (playbackState.position_ms || 0) / 1000;
    }
    const { baseMs, receivedAt } = lastSyncRef.current;
    const elapsedSec = ((performance.now() - receivedAt) / 1000) * (playbackState.playback_rate || 1.0);
    const durationSec = (currentTrack?.duration_ms || 0) / 1000;
    const currentSec = (baseMs / 1000) + elapsedSec;
    return durationSec > 0 ? Math.min(currentSec, durationSec) : Math.max(0, currentSec);
  };

  useEffect(() => {
    const audio = audioRef.current;
    if (!audio || !audioSrc) return;

    // Detect track change and load new audio file immediately
    if (audio.src !== audioSrc) {
      audio.src = audioSrc;
      audio.load();
      audio.currentTime = 0;
    }

    if (playbackState?.status === 'playing') {
      const expectedSec = getExpectedPositionSeconds();
      // Seek only when drift exceeds 3 seconds to avoid micro-stutters or jumps
      if (Math.abs(audio.currentTime - expectedSec) > 3.0) {
        audio.currentTime = expectedSec;
      }

      const playPromise = audio.play();
      if (playPromise !== undefined) {
        playPromise
          .then(() => {
            setIsAutoplayBlocked(false);
            setIsPlayingLocally(true);
          })
          .catch((err) => {
            // Autoplay policy prevented playback until user interaction
            if (err.name === 'NotAllowedError') {
              setIsAutoplayBlocked(true);
              setIsPlayingLocally(false);
            }
          });
      }
    } else {
      audio.pause();
      setIsPlayingLocally(false);
      const posSec = (playbackState?.position_ms || 0) / 1000;
      if (Math.abs(audio.currentTime - posSec) > 1.0) {
        audio.currentTime = posSec;
      }
    }
  }, [playbackState?.status, playbackState?.version, currentTrackId, audioSrc]);

  const handleUserUnblock = () => {
    const audio = audioRef.current;
    if (audio) {
      const expectedSec = getExpectedPositionSeconds();
      audio.currentTime = expectedSec;
      audio.play().then(() => {
        setIsAutoplayBlocked(false);
        setIsPlayingLocally(true);
      });
    }
  };

  const toggleMute = () => {
    if (audioRef.current) {
      audioRef.current.muted = !isMuted;
      setIsMuted(!isMuted);
    }
  };

  return (
    <div>
      <audio
        ref={audioRef}
        src={audioSrc}
        preload="auto"
        onEnded={() => {
          setIsPlayingLocally(false);
          if (onTrackEnded) {
            onTrackEnded();
          }
        }}
      />

      {isAutoplayBlocked && (
        <div className="fixed top-4 left-4 right-4 z-50 animate-bounce">
          <button
            onClick={handleUserUnblock}
            className="w-full py-3.5 px-6 rounded-2xl bg-gradient-to-r from-cyan-500 to-blue-600 text-black font-semibold text-sm flex items-center justify-center gap-2 shadow-cyan-glow"
          >
            <Radio className="w-5 h-5 animate-pulse" />
            <span>Tap to Join Live Synchronized Audio</span>
          </button>
        </div>
      )}

      {/* Synchronized status badge in bottom dock */}
      <div className="flex items-center justify-between text-xs text-gray-400 px-3 py-1.5">
        <div className="flex items-center gap-2">
          <span className={`w-2 h-2 rounded-full ${isPlayingLocally ? 'bg-cyan-400 animate-ping' : 'bg-gray-600'}`} />
          <span className="font-mono uppercase text-[10px] tracking-wider text-cyan-300">
            {isPlayingLocally ? 'Synced Stream' : 'Ready'}
          </span>
        </div>
        <button
          onClick={toggleMute}
          className="p-1 rounded-full hover:bg-white/10 text-gray-400 hover:text-cyan-400 transition-colors"
        >
          {isMuted ? <VolumeX className="w-4 h-4" /> : <Volume2 className="w-4 h-4" />}
        </button>
      </div>
    </div>
  );
};
