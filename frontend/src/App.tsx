import React, { useState, useEffect, useCallback } from 'react';
import { Home, Disc3, Search, User as UserIcon, AlertCircle, ListPlus } from 'lucide-react';
import { Room, QueueItem, Track, User, ThemeId, Playlist } from './types';
import { THEMES } from './theme';
import { HomeView } from './components/HomeView';
import { NowPlaying } from './components/NowPlaying';
import { SearchView } from './components/SearchView';
import { ProfileView } from './components/ProfileView';
import { AudioPlayer } from './components/AudioPlayer';
import { PlaylistModal } from './components/PlaylistModal';

export const App: React.FC = () => {
  const [activeTab, setActiveTab] = useState<'home' | 'now_playing' | 'search' | 'profile'>('home');
  const [currentTheme, setCurrentTheme] = useState<ThemeId>(() => {
    return (localStorage.getItem('beatwave_theme') as ThemeId) || 'purple';
  });
  const [room, setRoom] = useState<Room | null>(null);
  const [queue, setQueue] = useState<QueueItem[]>([]);
  const [currentUser, setCurrentUser] = useState<User | null>(null);
  const [token, setToken] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  // Custom User Playlists
  const [playlists, setPlaylists] = useState<Playlist[]>(() => {
    const saved = localStorage.getItem('beatwave_user_playlists');
    if (saved) {
      try { return JSON.parse(saved); } catch (e) {}
    }
    return [
      {
        id: 'pl-party',
        title: '🔥 Group Party Hits',
        description: 'High-energy tracks for group listening',
        tracks: [],
        gradient: 'linear-gradient(135deg, #f59e0b, #ef4444)',
        created_at: new Date().toISOString()
      },
      {
        id: 'pl-chill',
        title: '🌙 Midnight Glass Chill',
        description: 'Lo-fi & smooth synths',
        tracks: [],
        gradient: 'linear-gradient(135deg, #06b6d4, #3b82f6)',
        created_at: new Date().toISOString()
      }
    ];
  });
  const [isPlaylistModalOpen, setIsPlaylistModalOpen] = useState(false);
  const [trackToAddToPlaylist, setTrackToAddToPlaylist] = useState<Track | null>(null);

  useEffect(() => {
    localStorage.setItem('beatwave_user_playlists', JSON.stringify(playlists));
  }, [playlists]);

  const activeThemeConfig = THEMES[currentTheme] || THEMES.purple;

  // Extract query params (supports ?room_id=..., Telegram ?tgWebAppStartParam=..., and tg.initDataUnsafe.start_param)
  const getInitialRoomId = (): string | null => {
    const params = new URLSearchParams(window.location.search);
    const qParam = params.get('room_id') || params.get('tgWebAppStartParam');
    if (qParam) {
      localStorage.setItem('beatwave_active_room_id', qParam);
      return qParam;
    }

    const tg = (window as any).Telegram?.WebApp;
    const tgParam = tg?.initDataUnsafe?.start_param;
    if (tgParam) {
      localStorage.setItem('beatwave_active_room_id', tgParam);
      return tgParam;
    }

    const saved = localStorage.getItem('beatwave_active_room_id');
    if (saved) return saved;

    return null;
  };

  const roomIdFromUrl = getInitialRoomId();

  // Apply theme to document, root CSS variables, & Telegram WebApp
  useEffect(() => {
    const theme = THEMES[currentTheme] || THEMES.purple;
    document.body.className = `theme-${currentTheme}`;
    localStorage.setItem('beatwave_theme', currentTheme);

    const root = document.documentElement;
    root.style.setProperty('--theme-primary', theme.primary);
    root.style.setProperty('--theme-secondary', theme.secondary);
    root.style.setProperty('--theme-glow', theme.glow);
    root.style.setProperty('--theme-bg', theme.bg);
    root.style.setProperty('--theme-bg-elevated', theme.bgElevated);
    root.style.setProperty('--theme-accent-rgb', theme.accentRgb);
    root.style.setProperty('--theme-card-bg', `${theme.bgElevated}cc`);
    root.style.setProperty('--theme-border', `${theme.primary}40`);

    const tg = (window as any).Telegram?.WebApp;
    if (tg) {
      try {
        tg.setHeaderColor(theme.bg);
        tg.setBackgroundColor(theme.bg);
      } catch (e) {
        // Fallback
      }
    }
  }, [currentTheme]);

  // Initialize Telegram WebApp SDK
  useEffect(() => {
    const tg = (window as any).Telegram?.WebApp;
    if (tg) {
      tg.ready();
      tg.expand();

      const tgUser = tg.initDataUnsafe?.user;
      if (tgUser) {
        setCurrentUser({
          id: String(tgUser.id),
          telegram_user_id: tgUser.id,
          username: tgUser.username,
          display_name: `${tgUser.first_name || ''} ${tgUser.last_name || ''}`.trim() || tgUser.username,
          photo_url: tgUser.photo_url,
          is_premium: Boolean(tgUser.is_premium)
        });
      }
    }
  }, []);

  // Authenticate session & load room
  useEffect(() => {
    async function initSession() {
      try {
        const tg = (window as any).Telegram?.WebApp;
        const initData = tg?.initData || "demo_init_data";

        // Exchange initData for session token
        const authRes = await fetch('/api/v1/telegram/session', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ init_data: initData })
        });

        if (!authRes.ok) {
          throw new Error('Authentication failed');
        }

        const authData = await authRes.json();
        setToken(authData.token);
        if (authData.user) {
          setCurrentUser((prev) => prev ? { ...prev, ...authData.user } : authData.user);
        }

        // Fetch or create room
        let targetRoomId = roomIdFromUrl || getInitialRoomId();
        if (!targetRoomId) {
          const tgParam = (window as any).Telegram?.WebApp?.initDataUnsafe?.start_param;
          if (tgParam) {
            targetRoomId = tgParam;
            localStorage.setItem('beatwave_active_room_id', tgParam);
          }
        }

        let rData = null;
        if (targetRoomId) {
          const roomRes = await fetch(`/api/v1/rooms/${targetRoomId}`, {
            headers: { 'Authorization': `Bearer ${authData.token}` }
          });
          if (roomRes.ok) {
            rData = await roomRes.json();
          } else {
            // Stale or invalid room ID in localStorage/param - clear it so we create/fetch a valid room
            localStorage.removeItem('beatwave_active_room_id');
            targetRoomId = null;
          }
        }

        // If targetRoomId was invalid, missing, or returned 404, get or create the default room
        if (!rData) {
          const groupRes = await fetch('/api/v1/rooms/group/1001234567890?title=BeatWave+Music+Room', {
            method: 'POST',
            headers: {
              'Content-Type': 'application/json',
              'Authorization': `Bearer ${authData.token}`
            }
          });
          if (groupRes.ok) {
            rData = await groupRes.json();
            targetRoomId = rData.id;
            localStorage.setItem('beatwave_active_room_id', rData.id);
          }
        }

        if (rData) {
          setRoom(rData);
          const qRes = await fetch(`/api/v1/rooms/${rData.id}/queue`, {
            headers: { 'Authorization': `Bearer ${authData.token}` }
          });
          if (qRes.ok) {
            const qData = await qRes.json();
            setQueue(qData);
          }
        }
      } catch (err: any) {
        setErrorMessage(err.message || 'Error connecting to room');
      } finally {
        setLoading(false);
      }
    }

    initSession();
  }, [roomIdFromUrl]);

  // Connect WebSocket for real-time room sync
  useEffect(() => {
    if (!room?.id) return;

    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    const wsUrl = `${protocol}//${window.location.host}/api/v1/rooms/${room.id}/ws`;
    const socket = new WebSocket(wsUrl);

    socket.onmessage = (event) => {
      try {
        const payload = JSON.parse(event.data);
        if (payload.type === 'playback.snapshot') {
          setRoom((prev) => prev ? { ...prev, playback_state: payload.data } : null);
        }
      } catch (e) {
        // Ping
      }
    };

    return () => {
      socket.close();
    };
  }, [room?.id]);

  // Periodic poll to keep room state, queue, and participants continuously updated
  useEffect(() => {
    if (!room?.id || !token) return;
    const interval = setInterval(async () => {
      try {
        const [roomRes, qRes] = await Promise.all([
          fetch(`/api/v1/rooms/${room.id}`, { headers: { 'Authorization': `Bearer ${token}` } }),
          fetch(`/api/v1/rooms/${room.id}/queue`, { headers: { 'Authorization': `Bearer ${token}` } })
        ]);
        if (roomRes.ok) {
          const rData = await roomRes.json();
          setRoom(rData);
        }
        if (qRes.ok) {
          const qData = await qRes.json();
          setQueue(qData);
        }
      } catch (e) {
        // Silently ignore background poll errors
      }
    }, 3000);
    return () => clearInterval(interval);
  }, [room?.id, token]);

  // Playback Control Handlers
  const handleControlAction = useCallback(async (action: string, payload?: any) => {
    if (!room?.id || !token) return;

    try {
      const res = await fetch(`/api/v1/rooms/${room.id}/controls/${action}`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: payload ? JSON.stringify(payload) : undefined
      });

      if (res.ok) {
        const updatedState = await res.json();
        setRoom((prev) => prev ? { ...prev, playback_state: updatedState } : null);
      }
    } catch (err) {
      console.error(`Error performing ${action}:`, err);
    }
  }, [room?.id, token]);

  // Search API
  const handleSearch = useCallback(async (query: string): Promise<Track[]> => {
    if (!room?.id || !token) return [];
    try {
      const res = await fetch(`/api/v1/rooms/${room.id}/search`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify({ query })
      });
      if (res.ok) {
        const data = await res.json();
        return data.results || [];
      }
    } catch (e) {
      console.error('Search error:', e);
    }
    return [];
  }, [room?.id, token]);

  // Add Track Request API
  const handleRequestTrack = useCallback(async (provider: string, trackId: string, playNow: boolean = false) => {
    if (!room?.id || !token) return { success: false, message: 'Room not connected' };
    try {
      const res = await fetch(`/api/v1/rooms/${room.id}/requests`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify({ provider, provider_track_id: trackId, play_now: playNow })
      });
      const data = await res.json();
      if (res.ok) {
        // Refresh queue
        const qRes = await fetch(`/api/v1/rooms/${room.id}/queue`, {
          headers: { 'Authorization': `Bearer ${token}` }
        });
        if (qRes.ok) setQueue(await qRes.json());

        // Refresh room state
        const roomRes = await fetch(`/api/v1/rooms/${room.id}`, {
          headers: { 'Authorization': `Bearer ${token}` }
        });
        if (roomRes.ok) setRoom(await roomRes.json());

        return { success: true, message: playNow ? 'Playing now!' : 'Added to upcoming queue!' };
      }
      return { success: false, message: data.detail || 'Failed to add track' };
    } catch (e: any) {
      return { success: false, message: e.message || 'Network error' };
    }
  }, [room?.id, token]);

  // Direct select track and switch immediately to Now Playing
  const handleSelectTrackDirect = async (track: Track) => {
    await handleRequestTrack(track.provider, track.provider_track_id, true);
    setActiveTab('now_playing');
  };

  // Remove Queue Item
  const handleRemoveQueueItem = useCallback(async (itemId: string) => {
    if (!room?.id || !token) return;
    try {
      const res = await fetch(`/api/v1/rooms/${room.id}/queue/${itemId}`, {
        method: 'DELETE',
        headers: { 'Authorization': `Bearer ${token}` }
      });
      if (res.ok) {
        setQueue((prev) => prev.filter((item) => item.id !== itemId));
      }
    } catch (e) {
      console.error('Error removing item:', e);
    }
  }, [room?.id, token]);

  // Playlist Handlers
  const handleCreatePlaylist = useCallback((title: string, description?: string) => {
    const newPl: Playlist = {
      id: `pl-${Date.now()}`,
      title,
      description,
      tracks: [],
      gradient: `linear-gradient(135deg, ${activeThemeConfig.secondary}, ${activeThemeConfig.primary})`,
      created_at: new Date().toISOString()
    };
    setPlaylists(prev => [newPl, ...prev]);
  }, [activeThemeConfig]);

  const handleDeletePlaylist = useCallback((playlistId: string) => {
    setPlaylists(prev => prev.filter(p => p.id !== playlistId));
  }, []);

  const handleAddTrackToPlaylist = useCallback((playlistId: string, track: Track) => {
    setPlaylists(prev => prev.map(p => {
      if (p.id === playlistId) {
        if (p.tracks.some(t => t.id === track.id)) return p;
        return { ...p, tracks: [...p.tracks, track] };
      }
      return p;
    }));
  }, []);

  const handleRemoveTrackFromPlaylist = useCallback((playlistId: string, trackId: string) => {
    setPlaylists(prev => prev.map(p => {
      if (p.id === playlistId) {
        return { ...p, tracks: p.tracks.filter(t => t.id !== trackId) };
      }
      return p;
    }));
  }, []);

  const handlePlayPlaylist = useCallback(async (playlist: Playlist) => {
    if (playlist.tracks.length === 0) return;
    const first = playlist.tracks[0];
    await handleRequestTrack(first.provider, first.provider_track_id, true);
    for (let i = 1; i < playlist.tracks.length; i++) {
      const tr = playlist.tracks[i];
      await handleRequestTrack(tr.provider, tr.provider_track_id, false);
    }
    setActiveTab('now_playing');
  }, [handleRequestTrack]);

  const tabIndex = activeTab === 'home' ? 0 : activeTab === 'now_playing' ? 1 : activeTab === 'search' ? 2 : 3;

  const handleTabClick = (tab: 'home' | 'now_playing' | 'search' | 'profile') => {
    if (tab !== activeTab) {
      try {
        (window as any).Telegram?.WebApp?.HapticFeedback?.selectionChanged?.();
      } catch (_) {}
      setActiveTab(tab);
    }
  };

  if (loading) {
    return (
      <div 
        className="min-h-screen flex flex-col items-center justify-center p-4 text-center"
        style={{ backgroundColor: activeThemeConfig.bg }}
      >
        <div 
          className="w-16 h-16 rounded-3xl apple-glass flex items-center justify-center mb-4"
          style={{ color: activeThemeConfig.primary }}
        >
          <Disc3 className="w-8 h-8 animate-spin" />
        </div>
        <h1 className="text-xl font-extrabold text-white tracking-widest">BEATWAVE</h1>
        <p className="text-xs text-gray-400 mt-1.5 font-medium">Connecting to synchronized room...</p>
      </div>
    );
  }

  if (errorMessage && !room) {
    return (
      <div 
        className="min-h-screen flex flex-col items-center justify-center p-6 text-center"
        style={{ backgroundColor: activeThemeConfig.bg }}
      >
        <div className="apple-glass p-8 rounded-[36px] max-w-xs flex flex-col items-center">
          <AlertCircle className="w-12 h-12 text-red-400 mb-3" />
          <h2 className="text-lg font-bold text-white mb-2">Connection Error</h2>
          <p className="text-xs text-gray-400 mb-6">{errorMessage}</p>
          <button
            onClick={() => window.location.reload()}
            className="px-6 py-3 rounded-full apple-play-button text-white text-xs font-bold"
          >
            Try Again
          </button>
        </div>
      </div>
    );
  }

  return (
    <div 
      className="min-h-screen flex flex-col text-white relative overflow-x-hidden selection:text-white"
      style={{ backgroundColor: activeThemeConfig.bg }}
    >
      {/* Dynamic Ambient Glow Orbs matching active theme */}
      <div 
        className="fixed top-[-80px] left-[-80px] w-96 h-96 rounded-full blur-[120px] pointer-events-none opacity-40 transition-all duration-700"
        style={{ backgroundColor: activeThemeConfig.primary }}
      />
      <div 
        className="fixed top-1/2 right-[-80px] w-96 h-96 rounded-full blur-[130px] pointer-events-none opacity-30 transition-all duration-700"
        style={{ backgroundColor: activeThemeConfig.secondary }}
      />

      {/* Main Tab Content */}
      <main className="flex-1 overflow-y-auto relative z-10">
        {activeTab === 'home' && (
          <HomeView
            user={currentUser}
            room={room}
            theme={activeThemeConfig}
            onOpenSearch={() => setActiveTab('search')}
            onOpenThemeModal={() => setActiveTab('profile')}
            onRequestTrack={handleRequestTrack}
            onSelectTrackDirect={handleSelectTrackDirect}
          />
        )}
        {activeTab === 'now_playing' && (
          <NowPlaying 
            room={room || undefined}
            queue={queue}
            theme={activeThemeConfig}
            onControlAction={handleControlAction}
            onRemoveQueueItem={handleRemoveQueueItem}
            onOpenSearch={() => setActiveTab('search')}
            onBack={() => setActiveTab('home')}
            onOpenPlaylist={(track) => {
              setTrackToAddToPlaylist(track);
              setIsPlaylistModalOpen(true);
            }}
          />
        )}
        {activeTab === 'search' && (
          <SearchView onSearch={handleSearch} onRequestTrack={handleRequestTrack} />
        )}
        {activeTab === 'profile' && (
          <ProfileView 
            user={currentUser} 
            room={room} 
            queueCount={queue.length}
            currentTheme={currentTheme}
            theme={activeThemeConfig}
            onSelectTheme={setCurrentTheme}
            playlists={playlists}
            onOpenPlaylistModal={() => {
              setTrackToAddToPlaylist(null);
              setIsPlaylistModalOpen(true);
            }}
          />
        )}
      </main>

      {/* Bottom Synchronized Audio Streaming Engine */}
      <div className="fixed bottom-24 left-0 right-0 z-30 px-4 pointer-events-auto">
        <AudioPlayer 
          playbackState={room?.playback_state} 
          onTrackEnded={() => handleControlAction('skip')}
        />
      </div>

      {/* Floating Liquid Glass Navigation Bar (Matching exact uploaded reference picture) */}
      <div className="fixed bottom-4 left-4 right-4 z-40 flex items-center gap-2.5 max-w-md mx-auto pointer-events-auto">
        {/* Main Frosted Glass Pill Dock */}
        <nav className="relative flex-1 h-[68px] rounded-[34px] apple-glass-dock flex items-center p-1 shadow-[0_24px_50px_-8px_rgba(0,0,0,0.85)]">
          {/* Fluid Sliding Glass Lens Container */}
          <div 
            className="absolute inset-y-[-6px] left-1 pointer-events-none transition-transform will-change-transform z-0"
            style={{
              width: 'calc((100% - 8px) / 4)',
              transform: `translateX(calc(${tabIndex} * 100%))`,
              transitionDuration: '440ms',
              transitionTimingFunction: 'cubic-bezier(0.16, 1, 0.3, 1)',
            }}
          >
            <div className="w-full h-full px-0.5">
              <div className="w-full h-full rounded-[30px] apple-glass-lens relative flex flex-col items-center justify-between py-1 overflow-hidden">
                {/* Top specular refraction notch / meniscus (from reference image) */}
                <div className="w-8 h-[3.5px] rounded-full bg-black/85 shadow-[0_1px_1px_rgba(255,255,255,0.25)] border-b border-white/20 z-10" />
                
                {/* Dynamic radial theme aura */}
                <div 
                  className="absolute inset-0 rounded-[30px] opacity-40 blur-sm pointer-events-none"
                  style={{ background: `radial-gradient(circle at 50% 50%, ${activeThemeConfig.primary} 0%, transparent 70%)` }}
                />

                {/* Bottom specular refraction notch / meniscus (from reference image) */}
                <div className="w-8 h-[3.5px] rounded-full bg-black/85 shadow-[0_1px_1px_rgba(255,255,255,0.25)] border-t border-white/20 z-10" />
              </div>
            </div>
          </div>

          {/* 1. Home Tab */}
          <button
            onClick={() => handleTabClick('home')}
            className="flex-1 h-full relative z-10 flex flex-col items-center justify-center transition-all duration-300 select-none active:scale-95 group"
          >
            <div className={`transition-transform duration-300 ${activeTab === 'home' ? 'scale-110' : 'scale-100 opacity-60 group-hover:opacity-90'}`}>
              <Home 
                className={`w-5 h-5 transition-colors duration-300 ${activeTab === 'home' ? 'fill-current' : ''}`}
                style={{ color: activeTab === 'home' ? activeThemeConfig.primary : '#9ca3af' }}
              />
            </div>
            <span 
              className="text-[10px] mt-0.5 transition-all duration-300 tracking-tight"
              style={{ 
                color: activeTab === 'home' ? activeThemeConfig.primary : '#9ca3af',
                fontWeight: activeTab === 'home' ? 700 : 500
              }}
            >
              Home
            </span>
          </button>

          {/* 2. Play / Music Tab */}
          <button
            onClick={() => handleTabClick('now_playing')}
            className="flex-1 h-full relative z-10 flex flex-col items-center justify-center transition-all duration-300 select-none active:scale-95 group"
          >
            <div className={`transition-transform duration-300 ${activeTab === 'now_playing' ? 'scale-110' : 'scale-100 opacity-60 group-hover:opacity-90'}`}>
              <Disc3 
                className={`w-5 h-5 transition-colors duration-300 ${activeTab === 'now_playing' ? 'animate-spin' : ''}`}
                style={{ 
                  animationDuration: '4s',
                  color: activeTab === 'now_playing' ? activeThemeConfig.primary : '#9ca3af' 
                }}
              />
            </div>
            <span 
              className="text-[10px] mt-0.5 transition-all duration-300 tracking-tight"
              style={{ 
                color: activeTab === 'now_playing' ? activeThemeConfig.primary : '#9ca3af',
                fontWeight: activeTab === 'now_playing' ? 700 : 500
              }}
            >
              Music
            </span>
          </button>

          {/* 3. Search Tab */}
          <button
            onClick={() => handleTabClick('search')}
            className="flex-1 h-full relative z-10 flex flex-col items-center justify-center transition-all duration-300 select-none active:scale-95 group"
          >
            <div className={`transition-transform duration-300 ${activeTab === 'search' ? 'scale-110' : 'scale-100 opacity-60 group-hover:opacity-90'}`}>
              <Search 
                className="w-5 h-5 transition-colors duration-300"
                style={{ color: activeTab === 'search' ? activeThemeConfig.primary : '#9ca3af' }}
              />
            </div>
            <span 
              className="text-[10px] mt-0.5 transition-all duration-300 tracking-tight"
              style={{ 
                color: activeTab === 'search' ? activeThemeConfig.primary : '#9ca3af',
                fontWeight: activeTab === 'search' ? 700 : 500
              }}
            >
              Search
            </span>
          </button>

          {/* 4. Profile Tab */}
          <button
            onClick={() => handleTabClick('profile')}
            className="flex-1 h-full relative z-10 flex flex-col items-center justify-center transition-all duration-300 select-none active:scale-95 group"
          >
            <div className={`transition-transform duration-300 ${activeTab === 'profile' ? 'scale-110' : 'scale-100 opacity-60 group-hover:opacity-90'}`}>
              <UserIcon 
                className={`w-5 h-5 transition-colors duration-300 ${activeTab === 'profile' ? 'fill-current' : ''}`}
                style={{ color: activeTab === 'profile' ? activeThemeConfig.primary : '#9ca3af' }}
              />
            </div>
            <span 
              className="text-[10px] mt-0.5 transition-all duration-300 tracking-tight"
              style={{ 
                color: activeTab === 'profile' ? activeThemeConfig.primary : '#9ca3af',
                fontWeight: activeTab === 'profile' ? 700 : 500
              }}
            >
              Profile
            </span>
          </button>
        </nav>

        {/* Detached Circular Glass Action Button (matches reference picture) */}
        <button
          onClick={() => {
            try {
              (window as any).Telegram?.WebApp?.HapticFeedback?.impactOccurred?.('light');
            } catch (_) {}
            setTrackToAddToPlaylist(room?.playback_state?.current_queue_item?.track || null);
            setIsPlaylistModalOpen(true);
          }}
          className="w-[64px] h-[64px] rounded-[26px] apple-glass-circle-btn flex items-center justify-center transition-all duration-200 shadow-2xl active:scale-92 group relative flex-shrink-0"
          title="Playlists & Quick Add"
          style={{ borderColor: `${activeThemeConfig.primary}45` }}
        >
          <div className="relative">
            <ListPlus 
              className="w-6 h-6 transition-transform duration-200 group-hover:scale-110 group-active:scale-90" 
              style={{ color: activeThemeConfig.primary }}
            />
            {/* Subtle glow underneath icon */}
            <div 
              className="absolute inset-0 blur-sm opacity-50 pointer-events-none"
              style={{ backgroundColor: activeThemeConfig.primary }}
            />
          </div>
        </button>
      </div>

      {/* Playlist Management Modal */}
      <PlaylistModal
        isOpen={isPlaylistModalOpen}
        onClose={() => {
          setIsPlaylistModalOpen(false);
          setTrackToAddToPlaylist(null);
        }}
        playlists={playlists}
        onCreatePlaylist={handleCreatePlaylist}
        onDeletePlaylist={handleDeletePlaylist}
        onAddTrackToPlaylist={handleAddTrackToPlaylist}
        onRemoveTrackFromPlaylist={handleRemoveTrackFromPlaylist}
        onPlayPlaylist={handlePlayPlaylist}
        trackToAdd={trackToAddToPlaylist}
        theme={activeThemeConfig}
      />
    </div>
  );
};

export default App;
