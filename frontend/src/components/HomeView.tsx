import React, { useState } from 'react';
import { Search, Bell, Play, Plus, Check, Palette, Sparkles, MoreVertical } from 'lucide-react';
import { User, Room, Track, ThemeConfig } from '../types';

interface HomeViewProps {
  user?: User | null;
  room?: Room | null;
  theme: ThemeConfig;
  onOpenSearch: () => void;
  onOpenThemeModal: () => void;
  onRequestTrack: (provider: string, trackId: string) => Promise<{ success: boolean; message: string }>;
  onSelectTrackDirect: (track: Track) => void;
}

export const HomeView: React.FC<HomeViewProps> = ({
  user,
  room,
  theme,
  onOpenSearch,
  onOpenThemeModal,
  onRequestTrack,
  onSelectTrackDirect,
}) => {
  const [selectedCategory, setSelectedCategory] = useState('All');
  const [addedIds, setAddedIds] = useState<Set<string>>(new Set());

  const displayName = user?.display_name || user?.username || "James Wilson";
  const userPhoto = user?.photo_url || "https://images.unsplash.com/photo-1534528741775-53994a69daeb?w=200&q=80";

  const categories = ['All', 'Party', 'New Artists', 'Sad', 'Pop', 'Rock', 'Electronic'];

  const popularSongs: Track[] = [
    {
      id: "p1",
      provider: "youtube",
      provider_track_id: "viimfQi_pUw",
      title: "Ocean Eyes",
      artist: "Billie Eilish • Soft rock",
      duration_ms: 200000,
      artwork_url: "https://images.unsplash.com/photo-1514525253161-7a46d19cd819?w=400&q=80",
      availability_status: "available"
    },
    {
      id: "p2",
      provider: "youtube",
      provider_track_id: "kJQP7kiw5Fk",
      title: "Circles Run",
      artist: "Post Malone • Fan fav",
      duration_ms: 215000,
      artwork_url: "https://images.unsplash.com/photo-1501386761578-eac5c94b800a?w=400&q=80",
      availability_status: "available"
    },
    {
      id: "p3",
      provider: "youtube",
      provider_track_id: "4NRXx6U8ABQ",
      title: "Blinding Light",
      artist: "The Weeknd • Top hit",
      duration_ms: 200000,
      artwork_url: "https://images.unsplash.com/photo-1470225620780-dba8ba36b745?w=400&q=80",
      availability_status: "available"
    },
    {
      id: "p4",
      provider: "youtube",
      provider_track_id: "60ItHLz5WEA",
      title: "Faded",
      artist: "Alan Walker • Electro",
      duration_ms: 212000,
      artwork_url: "https://images.unsplash.com/photo-1511671782779-c97d3d27a1d4?w=400&q=80",
      availability_status: "available"
    },
    {
      id: "p5",
      provider: "youtube",
      provider_track_id: "34Na4j8AVgA",
      title: "Starboy",
      artist: "The Weeknd • Synthpop",
      duration_ms: 230000,
      artwork_url: "https://images.unsplash.com/photo-1518770660439-4636190af475?w=400&q=80",
      availability_status: "available"
    }
  ];

  const favoritePlaylists = [
    {
      id: "f1",
      title: "Rok Anthems",
      subtitle: "Rock • Classic • Hits • 22k Likes",
      artwork: "https://images.unsplash.com/photo-1465847899084-d164df4dedc6?w=300&q=80",
      track: popularSongs[0]
    },
    {
      id: "f2",
      title: "Night Drive Vibes",
      subtitle: "Synthwave • Chill • 18k Likes",
      artwork: "https://images.unsplash.com/photo-1508739773434-c26b3d09e071?w=300&q=80",
      track: popularSongs[2]
    },
    {
      id: "f3",
      title: "Midnight Tokyo FM",
      subtitle: "Lo-Fi • Future Funk • 35k Likes",
      artwork: "https://images.unsplash.com/photo-1518770660439-4636190af475?w=300&q=80",
      track: popularSongs[3]
    }
  ];

  const handleQueueTrack = async (e: React.MouseEvent, track: Track) => {
    e.stopPropagation();
    const res = await onRequestTrack(track.provider, track.provider_track_id);
    if (res.success) {
      setAddedIds((prev) => new Set(prev).add(track.provider_track_id));
    }
  };

  return (
    <div className="w-full max-w-md mx-auto px-5 pt-3 pb-28 space-y-5 animate-fade-in">
      {/* Top Header matching Middle Screen: Avatar + Greeting + Search & Notification/Theme Icons */}
      <div className="flex items-center justify-between pt-1">
        <div className="flex items-center gap-3">
          {/* Avatar with Halo Ring */}
          <div 
            className="w-12 h-12 rounded-full p-0.5 shadow-lg transition-transform active:scale-95"
            style={{ 
              background: `linear-gradient(135deg, ${theme.secondary}, ${theme.primary})`,
              boxShadow: `0 0 15px ${theme.glow}`
            }}
          >
            <div className="w-full h-full rounded-full overflow-hidden bg-black flex items-center justify-center">
              {user?.photo_url ? (
                <img src={userPhoto} alt={displayName} className="w-full h-full object-cover" />
              ) : (
                <span className="text-xs font-black text-white">
                  {displayName.slice(0, 2).toUpperCase()}
                </span>
              )}
            </div>
          </div>

          <div>
            <span className="text-[11px] text-gray-400 block font-medium tracking-wide">
              Good Morning!
            </span>
            <h2 className="text-base font-bold text-white tracking-tight leading-tight line-clamp-1">
              {displayName}
            </h2>
          </div>
        </div>

        <div className="flex items-center gap-2">
          {/* Search Button */}
          <button
            onClick={onOpenSearch}
            className="w-10 h-10 rounded-full apple-glass-pill flex items-center justify-center text-gray-300 hover:text-white transition-all active:scale-95"
            title="Search Music"
          >
            <Search className="w-4 h-4" />
          </button>

          {/* Theme / Palette Button with theme color dot */}
          <button
            onClick={onOpenThemeModal}
            className="w-10 h-10 rounded-full apple-glass-pill flex items-center justify-center text-gray-300 hover:text-white transition-all active:scale-95 relative"
            title="Themes & Profile"
          >
            <Palette className="w-4 h-4" style={{ color: theme.primary }} />
            <span 
              className="absolute top-2 right-2 w-2 h-2 rounded-full animate-pulse"
              style={{ backgroundColor: theme.primary }}
            />
          </button>
        </div>
      </div>

      {/* New Collections Hero Carousel Banner (Exact match from middle screen) */}
      <div className="space-y-2.5">
        <div className="flex items-center justify-between px-0.5">
          <h3 className="text-base font-bold text-white tracking-tight">New Collections</h3>
        </div>

        {/* Carousel Container */}
        <div className="relative w-full flex gap-3 overflow-x-auto no-scrollbar pb-1">
          {/* Main Hero Card */}
          <div 
            onClick={() => onSelectTrackDirect(popularSongs[2])}
            className="relative min-w-[88%] sm:min-w-[90%] h-44 rounded-[28px] overflow-hidden apple-glass-card border border-white/15 p-5 shadow-2xl flex flex-col justify-center cursor-pointer group flex-shrink-0"
          >
            {/* Background concert/singer photo & gradient overlay */}
            <img
              src="https://images.unsplash.com/photo-1501386761578-eac5c94b800a?w=800&q=80"
              alt="Performer on stage"
              className="absolute inset-0 w-full h-full object-cover object-right opacity-45 group-hover:scale-105 transition-transform duration-700 pointer-events-none"
            />
            <div className="absolute inset-0 bg-gradient-to-r from-black/95 via-black/70 to-transparent pointer-events-none" />

            {/* Banner text & Play Button */}
            <div className="relative z-10 max-w-[200px] space-y-3">
              <span 
                className="text-[10px] font-bold uppercase tracking-wider block"
                style={{ color: theme.primary }}
              >
                Featured Room Stream
              </span>
              <h4 className="text-lg font-extrabold text-white leading-snug tracking-tight">
                30 Day Free Trial Only For You
              </h4>
              <button
                onClick={(e) => {
                  e.stopPropagation();
                  onSelectTrackDirect(popularSongs[2]);
                }}
                className="inline-flex items-center gap-2 px-4 py-2 rounded-full apple-play-button text-white text-xs font-bold transition-all active:scale-95"
              >
                <Play className="w-3.5 h-3.5 fill-white translate-x-0.5" />
                <span>Start Listening</span>
              </button>
            </div>
          </div>

          {/* Peeking Next Card in Carousel */}
          <div 
            onClick={() => onSelectTrackDirect(popularSongs[1])}
            className="relative min-w-[70%] h-44 rounded-[28px] overflow-hidden apple-glass-card border border-white/10 p-5 shadow-xl flex flex-col justify-center cursor-pointer group flex-shrink-0 opacity-80"
          >
            <img
              src="https://images.unsplash.com/photo-1470225620780-dba8ba36b745?w=600&q=80"
              alt="Next Collection"
              className="absolute inset-0 w-full h-full object-cover opacity-35 group-hover:scale-105 transition-transform duration-700 pointer-events-none"
            />
            <div className="absolute inset-0 bg-gradient-to-r from-black/95 to-transparent pointer-events-none" />
            <div className="relative z-10 space-y-2">
              <span className="text-[10px] font-bold uppercase tracking-wider text-gray-400">
                Top Trending
              </span>
              <h4 className="text-base font-extrabold text-white leading-tight">
                Festival Live Hits
              </h4>
            </div>
          </div>
        </div>
      </div>

      {/* Categories Horizontal Pills (Exact match from middle screen) */}
      <div className="space-y-3">
        <div className="flex items-center justify-between px-0.5">
          <h3 className="text-base font-bold text-white tracking-tight">Categories</h3>
          <span className="text-xs text-gray-400 hover:text-white cursor-pointer font-medium">See all</span>
        </div>

        <div className="flex gap-2 overflow-x-auto no-scrollbar pb-1">
          {categories.map((cat) => {
            const isActive = selectedCategory === cat;
            return (
              <button
                key={cat}
                onClick={() => setSelectedCategory(cat)}
                className={`px-5 py-2 rounded-full text-xs font-semibold whitespace-nowrap transition-all active:scale-95 ${
                  isActive ? 'text-white font-bold' : 'text-gray-400 hover:text-white'
                }`}
                style={
                  isActive
                    ? {
                        backgroundColor: theme.primary,
                        boxShadow: `0 0 18px ${theme.glow}`,
                        borderColor: 'rgba(255, 255, 255, 0.3)'
                      }
                    : {
                        backgroundColor: 'rgba(255, 255, 255, 0.06)',
                        border: '1px solid rgba(255, 255, 255, 0.1)'
                      }
                }
              >
                {cat}
              </button>
            );
          })}
        </div>
      </div>

      {/* Popular Songs Horizontal Scroll (Exact match from middle screen) */}
      <div className="space-y-3">
        <div className="flex items-center justify-between px-0.5">
          <h3 className="text-base font-bold text-white tracking-tight">Popular Songs</h3>
          <span className="text-xs text-gray-400 hover:text-white cursor-pointer font-medium">See all</span>
        </div>

        <div className="flex gap-3.5 overflow-x-auto no-scrollbar pb-1">
          {popularSongs.map((track) => {
            const isAdded = addedIds.has(track.provider_track_id);
            return (
              <div
                key={track.provider_track_id}
                onClick={() => onSelectTrackDirect(track)}
                className="w-32 flex-shrink-0 space-y-2 cursor-pointer group"
              >
                {/* Artwork Card */}
                <div className="relative w-32 h-32 rounded-2xl overflow-hidden border border-white/10 shadow-lg apple-glass-card">
                  <img
                    src={track.artwork_url}
                    alt={track.title}
                    className="w-full h-full object-cover transition-transform duration-500 group-hover:scale-110"
                  />
                  {/* Subtle Dark Gradient Overlay */}
                  <div className="absolute inset-0 bg-gradient-to-t from-black/60 via-transparent to-transparent pointer-events-none" />

                  {/* Quick add button (+) */}
                  <button
                    onClick={(e) => handleQueueTrack(e, track)}
                    className="absolute bottom-2 right-2 w-7 h-7 rounded-full bg-black/70 backdrop-blur-md border border-white/20 flex items-center justify-center text-white hover:scale-110 transition-transform shadow-md"
                    title="Add to Up Next Queue"
                  >
                    {isAdded ? (
                      <Check className="w-3.5 h-3.5 text-emerald-400" />
                    ) : (
                      <Plus className="w-4 h-4" />
                    )}
                  </button>
                </div>

                {/* Title & Artist */}
                <div>
                  <h4 
                    className="text-xs font-bold text-white truncate transition-colors"
                    style={{ color: undefined }}
                  >
                    {track.title}
                  </h4>
                  <p className="text-[11px] text-gray-400 truncate mt-0.5">
                    {track.artist}
                  </p>
                </div>
              </div>
            );
          })}
        </div>
      </div>

      {/* Favorite Playlist Vertical List (Exact match from middle screen) */}
      <div className="space-y-3 pb-3">
        <div className="flex items-center justify-between px-0.5">
          <h3 className="text-base font-bold text-white tracking-tight">Favorite Playlist</h3>
          <span className="text-xs text-gray-400 hover:text-white cursor-pointer font-medium">See all</span>
        </div>

        <div className="space-y-2.5">
          {favoritePlaylists.map((pl) => (
            <div
              key={pl.id}
              onClick={() => onSelectTrackDirect(pl.track)}
              className="p-3 rounded-2xl apple-glass-card flex items-center justify-between gap-3 cursor-pointer group hover:border-white/20"
            >
              <div className="flex items-center gap-3 min-w-0">
                <img
                  src={pl.artwork}
                  alt={pl.title}
                  className="w-13 h-13 rounded-xl object-cover border border-white/10 flex-shrink-0 shadow-md"
                />
                <div className="min-w-0">
                  <h4 className="text-sm font-bold text-white truncate group-hover:text-gray-100 transition-colors">
                    {pl.title}
                  </h4>
                  <p className="text-xs text-gray-400 truncate mt-0.5">
                    {pl.subtitle}
                  </p>
                </div>
              </div>

              {/* Play Button & More Options */}
              <div className="flex items-center gap-2 flex-shrink-0">
                <button
                  className="w-9 h-9 rounded-full apple-glass-pill flex items-center justify-center text-white hover:scale-105 transition-all shadow-md"
                  style={{ color: theme.primary }}
                  title="Play Playlist"
                >
                  <Play className="w-4 h-4 fill-current translate-x-0.5" />
                </button>
                <button 
                  className="p-1.5 text-gray-400 hover:text-white"
                  onClick={(e) => e.stopPropagation()}
                >
                  <MoreVertical className="w-4 h-4" />
                </button>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
};
