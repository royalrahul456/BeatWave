import React, { useState, useEffect } from 'react';
import { 
  ChevronLeft, Heart, Play, Pause, SkipForward, SkipBack, 
  Shuffle, Repeat, RotateCcw, RotateCw, Volume2, VolumeX, ShieldCheck,
  ListMusic, Trash2, Plus, Disc3
} from 'lucide-react';
import { Room, QueueItem, ThemeConfig } from '../types';

interface NowPlayingProps {
  room?: Room;
  queue: QueueItem[];
  theme: ThemeConfig;
  onControlAction: (action: string, payload?: any) => Promise<void>;
  onRemoveQueueItem: (itemId: string) => Promise<void>;
  onOpenSearch: () => void;
  onBack: () => void;
}

export const NowPlaying: React.FC<NowPlayingProps> = ({ 
  room, 
  queue,
  theme,
  onControlAction,
  onRemoveQueueItem,
  onOpenSearch,
  onBack 
}) => {
  const playback = room?.playback_state;
  const currentItem = playback?.current_queue_item;
  const track = currentItem?.track;
  const isPlaying = playback?.status === 'playing';
  const isDJ = room?.is_dj ?? false;

  const [isLiked, setIsLiked] = useState(false);
  const [isShuffle, setIsShuffle] = useState(false);
  const [volume, setVolume] = useState(85);
  const [showVolume, setShowVolume] = useState(false);

  // Smooth local scrubber ticker with safe UTC parsing
  const [displayPositionMs, setDisplayPositionMs] = useState(0);

  const parseUtcDate = (dateStr?: string | null): number => {
    if (!dateStr) return 0;
    const isoStr = dateStr.includes('Z') || dateStr.includes('+') ? dateStr : dateStr + 'Z';
    const parsed = new Date(isoStr).getTime();
    return isNaN(parsed) ? 0 : parsed;
  };

  useEffect(() => {
    if (!playback) return;

    const basePositionMs = playback.position_ms || 0;
    const startedAt = parseUtcDate(playback.started_at);
    const rate = playback.playback_rate || 1.0;
    const duration = track?.duration_ms || 240000;

    if (playback.status === 'playing' && startedAt > 0) {
      const updatePosition = () => {
        const now = Date.now();
        const rawElapsed = (now - startedAt) * rate;
        // Guard against timezone clock skew jumps (> 1 hour or negative)
        const elapsed = (rawElapsed > 0 && rawElapsed < duration + 10000) ? rawElapsed : 0;
        const current = basePositionMs + elapsed;
        setDisplayPositionMs(Math.max(0, Math.min(current, duration)));
      };

      updatePosition();
      const interval = setInterval(updatePosition, 200);
      return () => clearInterval(interval);
    } else {
      setDisplayPositionMs(basePositionMs);
    }
  }, [playback?.status, playback?.position_ms, playback?.started_at, track?.duration_ms]);

  const durationMs = track?.duration_ms || 222000;
  const progressRatio = Math.max(0, Math.min(1, displayPositionMs / durationMs));
  const progressPercent = progressRatio * 100;

  const formatTime = (ms: number) => {
    const totalSeconds = Math.floor(ms / 1000);
    const mins = Math.floor(totalSeconds / 60);
    const secs = totalSeconds % 60;
    return `${mins}:${secs < 10 ? '0' : ''}${secs}`;
  };

  const handleSeek = (e: React.MouseEvent<HTMLDivElement>) => {
    if (!isDJ) return;
    const rect = e.currentTarget.getBoundingClientRect();
    const clickX = e.clientX - rect.left;
    const ratio = Math.max(0, Math.min(1, clickX / rect.width));
    const targetMs = Math.floor(ratio * durationMs);
    setDisplayPositionMs(targetMs);
    onControlAction('seek', { position_ms: targetMs });
  };

  const handleJump = (deltaMs: number) => {
    if (!isDJ) return;
    const newPos = Math.max(0, Math.min(durationMs, displayPositionMs + deltaMs));
    setDisplayPositionMs(newPos);
    onControlAction('seek', { position_ms: newPos });
  };

  // Filter out currently playing item to show upcoming in queue
  const upcomingQueue = queue.filter(item => item.status === 'queued');

  if (!track) {
    return (
      <div className="flex flex-col items-center justify-center min-h-[78vh] px-4 text-center">
        <div className="relative w-full max-w-sm apple-glass p-8 rounded-[36px] flex flex-col items-center">
          <div 
            className="w-24 h-24 rounded-full bg-white/5 border border-white/10 flex items-center justify-center mb-5 shadow-2xl"
            style={{ color: theme.primary }}
          >
            <Play className="w-10 h-10 translate-x-0.5 fill-current" />
          </div>
          <h2 className="text-2xl font-bold text-white mb-2 tracking-tight">No Track Playing</h2>
          <p className="text-sm text-gray-400 mb-6 max-w-xs leading-relaxed">
            Select a song from the Home tab or Search any track to start listening in sync!
          </p>
          <button
            onClick={onOpenSearch}
            className="px-6 py-3 rounded-full apple-play-button text-white text-xs font-bold"
          >
            Search Songs
          </button>
        </div>
      </div>
    );
  }

  // Wavy SVG path
  const waveSvgPath = "M 0,20 C 30,10 50,30 80,20 C 110,10 130,30 160,20 C 190,10 210,30 240,20 C 270,10 290,25 300,20";

  return (
    <div className="flex flex-col items-center w-full max-w-md mx-auto px-5 pt-1 pb-32">
      {/* Top Header Bar matching picture: Left Arrow, "Now Playing", Volume/Mute Icon */}
      <div className="w-full flex items-center justify-between py-3 mb-2">
        <button
          onClick={onBack}
          className="w-10 h-10 rounded-full apple-glass-pill flex items-center justify-center text-gray-300 hover:text-white transition-all active:scale-95"
          title="Back to Home"
        >
          <ChevronLeft className="w-5 h-5 -translate-x-0.5" />
        </button>

        <h3 className="text-base font-semibold text-white tracking-wide">
          Now Playing
        </h3>

        <button
          onClick={() => setShowVolume(!showVolume)}
          className="w-10 h-10 rounded-full apple-glass-pill flex items-center justify-center text-gray-300 hover:text-white transition-all active:scale-95"
          title="Adjust Volume"
        >
          <Volume2 className="w-5 h-5" />
        </button>
      </div>

      {/* Volume Bar if toggled */}
      {showVolume && (
        <div className="w-full px-4 py-2.5 mb-3 rounded-2xl apple-glass flex items-center gap-3 animate-fade-in">
          <VolumeX className="w-4 h-4 text-gray-400" />
          <input
            type="range"
            min="0"
            max="100"
            value={volume}
            onChange={(e) => setVolume(Number(e.target.value))}
            style={{ accentColor: theme.primary }}
            className="w-full h-1.5 bg-gray-800 rounded-lg cursor-pointer"
          />
          <Volume2 className="w-4 h-4 text-gray-400" />
        </div>
      )}

      {/* Giant Circular Artwork with Double Glass Ring Halo (Matches uploaded picture) */}
      <div className="relative my-3 flex items-center justify-center">
        {/* Soft Radial Ambient Glow */}
        <div 
          className="absolute w-72 h-72 rounded-full blur-3xl opacity-40 pointer-events-none transition-all duration-700"
          style={{ backgroundColor: theme.primary }}
        />

        {/* Outer Frosted Glass Ring */}
        <div className="w-64 h-64 sm:w-72 sm:h-72 rounded-full p-3 apple-glass circular-halo-ring flex items-center justify-center relative">
          {/* Inner Circular Artwork */}
          <div className="w-full h-full rounded-full overflow-hidden border-2 border-white/20 shadow-2xl relative">
            <img
              src={track.artwork_url || "https://images.unsplash.com/photo-1518770660439-4636190af475?w=600&q=85"}
              alt={track.title}
              className={`w-full h-full object-cover transition-transform duration-700 ${
                isPlaying ? 'scale-105' : 'scale-100'
              }`}
            />
            {/* Glass reflection overlay */}
            <div className="absolute inset-0 bg-gradient-to-tr from-black/40 via-transparent to-white/20 pointer-events-none" />
          </div>
        </div>
      </div>

      {/* Track Title, Artist & Glass Heart Button (Exact layout from uploaded picture) */}
      <div className="w-full flex items-center justify-between px-2 mt-4 mb-2">
        <div className="min-w-0 pr-4">
          <h1 className="text-2xl font-bold text-white tracking-tight line-clamp-1">
            {track.title}
          </h1>
          <p className="text-sm text-gray-400 font-medium line-clamp-1 mt-0.5">
            {track.artist || 'Unknown Artist'}
          </p>
        </div>

        {/* Heart Like in Frosted Circle Button */}
        <button
          onClick={() => setIsLiked(!isLiked)}
          className="w-11 h-11 rounded-full apple-glass-card flex items-center justify-center transition-all active:scale-125 flex-shrink-0"
        >
          <Heart className={`w-5 h-5 ${isLiked ? 'fill-rose-500 text-rose-500' : 'text-gray-300'}`} />
        </button>
      </div>

      {/* Wavy Fluid Audio Scrubber & Controls (Exact layout from uploaded picture) */}
      <div className="w-full px-2 mt-2 mb-3">
        {/* Rewind 10 & Forward 10 overlaying wavy line */}
        <div className="flex items-center justify-between text-xs text-gray-400 px-1 mb-1">
          <button 
            onClick={() => handleJump(-10000)}
            disabled={!isDJ}
            className="flex items-center gap-0.5 text-gray-400 hover:text-white transition-colors disabled:opacity-40"
          >
            <RotateCcw className="w-3.5 h-3.5" />
            <span className="text-[10px] font-mono">10</span>
          </button>

          <button 
            onClick={() => handleJump(10000)}
            disabled={!isDJ}
            className="flex items-center gap-0.5 text-gray-400 hover:text-white transition-colors disabled:opacity-40"
          >
            <span className="text-[10px] font-mono">10</span>
            <RotateCw className="w-3.5 h-3.5" />
          </button>
        </div>

        {/* Wavy SVG Soundwave Line Scrubber */}
        <div 
          onClick={handleSeek}
          className={`relative w-full h-10 flex items-center ${isDJ ? 'cursor-pointer' : ''}`}
        >
          <svg className="w-full h-8 overflow-visible" viewBox="0 0 300 40" preserveAspectRatio="none">
            {/* Background inactive wave */}
            <path
              d={waveSvgPath}
              fill="none"
              stroke="rgba(255, 255, 255, 0.15)"
              strokeWidth="2.5"
              strokeLinecap="round"
            />
            {/* Active glowing theme wave */}
            <path
              d={waveSvgPath}
              fill="none"
              stroke={theme.primary}
              strokeWidth="3.2"
              strokeLinecap="round"
              strokeDasharray="300"
              strokeDashoffset={300 - (300 * progressRatio)}
              style={{ filter: `drop-shadow(0 0 8px ${theme.primary})` }}
            />
          </svg>

          {/* Progress bead on wave */}
          <div 
            className="absolute top-1/2 -translate-y-1/2 w-4 h-4 rounded-full bg-white shadow-[0_0_12px_var(--theme-primary)] pointer-events-none transition-all duration-100"
            style={{ 
              left: `calc(${progressPercent}% - 8px)`,
              boxShadow: `0 0 12px ${theme.primary}`
            }}
          />
        </div>

        {/* Timestamps */}
        <div className="flex justify-between items-center text-xs font-mono text-gray-400 px-1 mt-0.5">
          <span>{formatTime(displayPositionMs)}</span>
          <span>{formatTime(durationMs)}</span>
        </div>
      </div>

      {/* Bottom Playback Controls Bar (Exact layout from uploaded picture) */}
      <div className="w-full flex items-center justify-around px-2 py-3 mb-5">
        {/* Shuffle Button */}
        <button
          onClick={() => isDJ && setIsShuffle(!isShuffle)}
          disabled={!isDJ}
          className={`p-2.5 rounded-full transition-all active:scale-95 ${
            isShuffle ? 'text-white' : 'text-gray-400 hover:text-white disabled:opacity-40'
          }`}
          style={{ color: isShuffle ? theme.primary : undefined }}
          title="Shuffle Queue"
        >
          <Shuffle className="w-5 h-5" />
        </button>

        {/* Previous Track */}
        <button
          onClick={() => handleJump(-15000)}
          disabled={!isDJ}
          className="p-2.5 rounded-full text-gray-300 hover:text-white transition-all active:scale-95 disabled:opacity-40"
          title="Previous Track"
        >
          <SkipBack className="w-6 h-6 fill-current" />
        </button>

        {/* Large Glowing Circular Glass Play/Pause Button */}
        <button
          onClick={() => isDJ && onControlAction(isPlaying ? 'pause' : 'resume')}
          disabled={!isDJ}
          className="w-16 h-16 rounded-full apple-play-button flex items-center justify-center text-white font-bold transition-all active:scale-95 disabled:opacity-50"
          title={isDJ ? (isPlaying ? 'Pause' : 'Play') : 'DJ Controls Playback'}
        >
          {isPlaying ? (
            <Pause className="w-7 h-7 fill-white" />
          ) : (
            <Play className="w-7 h-7 fill-white translate-x-0.5" />
          )}
        </button>

        {/* Next Track */}
        <button
          onClick={() => isDJ && onControlAction('skip')}
          disabled={!isDJ}
          className="p-2.5 rounded-full text-gray-300 hover:text-white transition-all active:scale-95 disabled:opacity-40"
          title="Skip to Next"
        >
          <SkipForward className="w-6 h-6 fill-current" />
        </button>

        {/* Loop / Repeat Mode */}
        <button
          onClick={() => isDJ && onControlAction('loop', { mode: playback?.loop_mode === 'track' ? 'off' : 'track' })}
          disabled={!isDJ}
          className={`p-2.5 rounded-full transition-all active:scale-95 ${
            playback?.loop_mode === 'track'
              ? 'text-white'
              : 'text-gray-400 hover:text-white disabled:opacity-40'
          }`}
          style={{ color: playback?.loop_mode === 'track' ? theme.primary : undefined }}
          title="Repeat Track"
        >
          <Repeat className="w-5 h-5" />
        </button>
      </div>

      {/* --- INTEGRATED QUEUE SECTION SHIFTED BELOW SONG CARD & CONTROLS --- */}
      <div className="w-full mt-2 pt-5 border-t border-white/10 space-y-3">
        <div className="flex items-center justify-between px-1">
          <div className="flex items-center gap-2">
            <ListMusic className="w-4 h-4" style={{ color: theme.primary }} />
            <h3 className="text-base font-bold text-white tracking-tight">Up Next in Room</h3>
            <span 
              className="text-xs px-2 py-0.5 rounded-full font-bold"
              style={{ backgroundColor: `${theme.primary}25`, color: theme.primary }}
            >
              {upcomingQueue.length}
            </span>
          </div>

          <button
            onClick={onOpenSearch}
            className="inline-flex items-center gap-1 text-xs font-semibold hover:underline"
            style={{ color: theme.primary }}
          >
            <Plus className="w-3.5 h-3.5" />
            <span>Add Songs</span>
          </button>
        </div>

        {/* Upcoming Queue List */}
        {upcomingQueue.length === 0 ? (
          <div className="p-5 rounded-2xl apple-glass-card text-center space-y-2">
            <p className="text-xs text-gray-400">No tracks queued up next</p>
            <button
              onClick={onOpenSearch}
              className="px-4 py-1.5 rounded-full text-xs font-bold apple-glass-pill hover:text-white transition-all"
              style={{ color: theme.primary }}
            >
              + Search & Queue Songs
            </button>
          </div>
        ) : (
          <div className="space-y-2">
            {upcomingQueue.map((item, idx) => (
              <div
                key={item.id}
                className="p-3 rounded-2xl apple-glass-card flex items-center justify-between gap-3"
              >
                {/* Number badge */}
                <div className="w-6 text-center font-mono text-xs font-bold text-gray-400">
                  #{idx + 1}
                </div>

                {/* Thumbnail */}
                <img
                  src={item.track.artwork_url || "https://images.unsplash.com/photo-1618005182384-a83a8bd57fbe?w=120&q=80"}
                  alt={item.track.title}
                  className="w-11 h-11 rounded-xl object-cover border border-white/10 flex-shrink-0"
                />

                {/* Info */}
                <div className="min-w-0 flex-1">
                  <h4 className="text-sm font-semibold text-white truncate">
                    {item.track.title}
                  </h4>
                  <p className="text-xs text-gray-400 truncate">
                    {item.track.artist || 'Artist'} • By {item.requested_by.display_name || 'Member'}
                  </p>
                </div>

                {/* DJ delete button */}
                {isDJ && (
                  <button
                    onClick={() => onRemoveQueueItem(item.id)}
                    className="p-2 rounded-lg text-gray-500 hover:text-red-400 hover:bg-red-500/10 transition-colors flex-shrink-0"
                    title="Remove from queue"
                  >
                    <Trash2 className="w-4 h-4" />
                  </button>
                )}
              </div>
            ))}
          </div>
        )}
      </div>

      {/* DJ Authority Pill */}
      <div className="w-full mt-4 pt-3 border-t border-white/10 flex items-center justify-between text-xs text-gray-400 px-1">
        <div className="flex items-center gap-1.5">
          <ShieldCheck className="w-4 h-4" style={{ color: theme.primary }} />
          <span>
            {isDJ ? (
              <b style={{ color: theme.primary }}>You are the DJ (Full Control)</b>
            ) : (
              <span>DJ: <b className="text-gray-200">{room?.current_dj?.display_name || 'Group Admin'}</b></span>
            )}
          </span>
        </div>

        <span className="font-mono text-[11px] text-gray-500">v{playback?.version || 1}</span>
      </div>
    </div>
  );
};
