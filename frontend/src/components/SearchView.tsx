import React, { useState, useEffect, useRef } from 'react';
import { Search as SearchIcon, Plus, Check, Loader2, Flame, X, Sparkles } from 'lucide-react';
import { Track } from '../types';

interface SearchViewProps {
  onSearch: (query: string) => Promise<Track[]>;
  onRequestTrack: (provider: string, trackId: string) => Promise<{ success: boolean; message: string }>;
}

export const SearchView: React.FC<SearchViewProps> = ({ onSearch, onRequestTrack }) => {
  const [query, setQuery] = useState('');
  const [results, setResults] = useState<Track[]>([]);
  const [loading, setLoading] = useState(false);
  const [addedIds, setAddedIds] = useState<Set<string>>(new Set());
  const [addingId, setAddingId] = useState<string | null>(null);
  const [feedback, setFeedback] = useState<string | null>(null);
  const searchTimeoutRef = useRef<any>(null);

  // Load trending default tracks initially
  useEffect(() => {
    onSearch('').then(setResults);
  }, [onSearch]);

  // Instant Debounced Auto-Search as user types
  useEffect(() => {
    if (searchTimeoutRef.current) {
      clearTimeout(searchTimeoutRef.current);
    }

    const trimmed = query.trim();
    if (!trimmed) {
      // Empty query: show trending
      onSearch('').then(setResults);
      setLoading(false);
      return;
    }

    if (trimmed.length >= 2) {
      setLoading(true);
      searchTimeoutRef.current = setTimeout(async () => {
        try {
          const res = await onSearch(trimmed);
          setResults(res);
        } finally {
          setLoading(false);
        }
      }, 350); // 350ms debounce
    }

    return () => {
      if (searchTimeoutRef.current) {
        clearTimeout(searchTimeoutRef.current);
      }
    };
  }, [query, onSearch]);

  const handleClear = () => {
    setQuery('');
    setLoading(false);
    onSearch('').then(setResults);
  };

  const handleAdd = async (track: Track) => {
    setAddingId(track.provider_track_id);
    const res = await onRequestTrack(track.provider, track.provider_track_id);
    setAddingId(null);
    if (res.success) {
      setAddedIds((prev) => new Set(prev).add(track.provider_track_id));
    }
    setFeedback(res.message);
    setTimeout(() => setFeedback(null), 3000);
  };

  const popularHits = [
    'Starboy', 'Faded Alan Walker', 'Blinding Lights', 'Shape of You',
    'Stay Justin Bieber', 'As It Was', 'Levitating Dua Lipa'
  ];

  return (
    <div className="w-full max-w-md mx-auto px-4 pt-2 pb-28 space-y-4">
      {/* Search Bar Header */}
      <div className="space-y-1">
        <h2 className="text-xl font-bold text-white tracking-tight flex items-center gap-2">
          <span>Search Any Song</span>
          <span className="text-[10px] px-2.5 py-0.5 rounded-full bg-cyan-500/20 text-cyan-300 font-semibold border border-cyan-400/30">
            Instant Search
          </span>
        </h2>
        <p className="text-xs text-gray-400">Type any track name or artist — results load automatically</p>
      </div>

      {/* Instant Glass Search Input */}
      <div className="relative flex items-center">
        <input
          type="text"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          placeholder="Start typing song name or artist..."
          className="w-full py-4 pl-12 pr-12 rounded-[24px] vision-glass text-white placeholder-gray-500 text-sm focus:outline-none focus:border-cyan-400 focus:shadow-[0_0_25px_rgba(0,242,254,0.35)] transition-all"
        />
        <SearchIcon className="w-5 h-5 text-cyan-400 absolute left-4" />
        
        {/* Right side: Loading spinner or Clear button */}
        <div className="absolute right-4 flex items-center">
          {loading ? (
            <Loader2 className="w-5 h-5 text-cyan-400 animate-spin" />
          ) : query ? (
            <button
              onClick={handleClear}
              className="p-1 rounded-full text-gray-400 hover:text-white bg-white/10 transition-colors"
            >
              <X className="w-4 h-4" />
            </button>
          ) : null}
        </div>
      </div>

      {/* Floating Notification Feedback */}
      {feedback && (
        <div className="py-2.5 px-4 rounded-2xl bg-cyan-500/20 border border-cyan-400/40 text-cyan-200 text-xs text-center font-medium shadow-[0_0_20px_rgba(0,242,254,0.25)] animate-fade-in">
          {feedback}
        </div>
      )}

      {/* Quick Suggestion Pills */}
      <div className="space-y-2">
        <div className="flex items-center gap-1.5 text-xs text-gray-400 px-1">
          <Flame className="w-3.5 h-3.5 text-cyan-400" />
          <span>Trending Quick Suggestions</span>
        </div>
        <div className="flex gap-2 overflow-x-auto pb-1 no-scrollbar">
          {popularHits.map((term) => (
            <button
              key={term}
              onClick={() => setQuery(term)}
              className="py-1.5 px-3.5 rounded-full vision-card text-xs text-gray-300 hover:text-cyan-300 hover:border-cyan-400/40 whitespace-nowrap transition-all flex-shrink-0"
            >
              {term}
            </button>
          ))}
        </div>
      </div>

      {/* Results Header */}
      <div className="flex items-center justify-between text-xs text-gray-400 px-1 pt-1">
        <span>{query ? `Searching for "${query}"` : 'Popular Releases'}</span>
        <span>{results.length} songs available</span>
      </div>

      {/* Real Track Cards */}
      <div className="space-y-2.5">
        {results.map((track) => {
          const isAdded = addedIds.has(track.provider_track_id);
          const isCurrentlyAdding = addingId === track.provider_track_id;

          const durationSec = Math.floor(track.duration_ms / 1000);
          const mins = Math.floor(durationSec / 60);
          const secs = durationSec % 60;
          const durationStr = `${mins}:${secs < 10 ? '0' : ''}${secs}`;

          return (
            <div
              key={`${track.provider}-${track.provider_track_id}`}
              className="p-3 rounded-[24px] vision-card flex items-center justify-between gap-3 group"
            >
              {/* Thumbnail */}
              <div className="relative w-14 h-14 rounded-2xl overflow-hidden flex-shrink-0 border border-white/10 shadow-md">
                <img
                  src={track.artwork_url || "https://images.unsplash.com/photo-1618005182384-a83a8bd57fbe?w=200&q=80"}
                  alt={track.title}
                  className="w-full h-full object-cover transition-transform duration-500 group-hover:scale-110"
                />
              </div>

              {/* Info */}
              <div className="min-w-0 flex-1">
                <h4 className="text-sm font-bold text-white truncate group-hover:text-cyan-300 transition-colors">
                  {track.title}
                </h4>
                <p className="text-xs text-gray-400 truncate">
                  {track.artist || 'Unknown Artist'}
                </p>
                <div className="flex items-center gap-2 mt-1 text-[10px] text-gray-500 font-mono">
                  <span>{durationStr}</span>
                  <span>•</span>
                  <span className="text-cyan-400/70">{track.source_attribution || 'Direct Stream'}</span>
                </div>
              </div>

              {/* Action Button */}
              <button
                onClick={() => handleAdd(track)}
                disabled={isCurrentlyAdding || isAdded}
                className={`p-3 rounded-2xl transition-all active:scale-90 flex-shrink-0 ${
                  isAdded
                    ? 'bg-emerald-500/20 text-emerald-400 border border-emerald-400/40'
                    : 'vision-button-play text-black hover:opacity-95'
                }`}
                title="Add to queue"
              >
                {isCurrentlyAdding ? (
                  <Loader2 className="w-5 h-5 animate-spin" />
                ) : isAdded ? (
                  <Check className="w-5 h-5" />
                ) : (
                  <Plus className="w-5 h-5 stroke-[2.5]" />
                )}
              </button>
            </div>
          );
        })}
      </div>
    </div>
  );
};
