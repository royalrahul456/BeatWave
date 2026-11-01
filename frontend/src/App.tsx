import React, { useState, useEffect, useCallback } from 'react';
import { Home, Disc3, Search, User as UserIcon, AlertCircle } from 'lucide-react';
import { Room, QueueItem, Track, User, ThemeId } from './types';
import { THEMES } from './theme';
import { HomeView } from './components/HomeView';
import { NowPlaying } from './components/NowPlaying';
import { SearchView } from './components/SearchView';
import { ProfileView } from './components/ProfileView';
import { AudioPlayer } from './components/AudioPlayer';

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

  const activeThemeConfig = THEMES[currentTheme] || THEMES.purple;

  // Extract query params (e.g. ?room_id=...)
  const params = new URLSearchParams(window.location.search);
  const roomIdFromUrl = params.get('room_id');

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
        let targetRoomId = roomIdFromUrl;
        if (!targetRoomId) {
          const groupRes = await fetch('/api/v1/rooms/group/1001234567890?title=BeatWave+Music+Room', {
            method: 'POST',
            headers: {
              'Content-Type': 'application/json',
              'Authorization': `Bearer ${authData.token}`
            }
          });
          if (groupRes.ok) {
            const groupData = await groupRes.json();
            targetRoomId = groupData.id;
          }
        }

        if (targetRoomId) {
          const roomRes = await fetch(`/api/v1/rooms/${targetRoomId}`, {
            headers: { 'Authorization': `Bearer ${authData.token}` }
          });
          if (roomRes.ok) {
            const rData = await roomRes.json();
            setRoom(rData);
          }

          const qRes = await fetch(`/api/v1/rooms/${targetRoomId}/queue`, {
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
          />
        )}
      </main>

      {/* Bottom Synchronized Audio Streaming Engine */}
      <div className="fixed bottom-24 left-0 right-0 z-30 px-4 pointer-events-auto">
        <AudioPlayer playbackState={room?.playback_state} />
      </div>

      {/* Floating 4-Button Glass Pill Navigation Bar (Queue removed & shifted to Play tab) */}
      <nav className="fixed bottom-4 left-6 right-6 z-40 h-16 rounded-full apple-glass flex items-center justify-around px-4 shadow-[0_20px_45px_rgba(0,0,0,0.85)]">
        {/* 1. Home Tab */}
        <button
          onClick={() => setActiveTab('home')}
          className={`w-11 h-11 rounded-full flex items-center justify-center transition-all ${
            activeTab === 'home'
              ? 'apple-play-button text-white shadow-lg'
              : 'text-gray-400 hover:text-white'
          }`}
          style={activeTab === 'home' ? { boxShadow: `0 0 20px ${activeThemeConfig.glow}` } : {}}
          title="Home"
        >
          <Home className="w-5 h-5" />
        </button>

        {/* 2. Play / Now Playing Tab */}
        <button
          onClick={() => setActiveTab('now_playing')}
          className={`w-11 h-11 rounded-full flex items-center justify-center transition-all ${
            activeTab === 'now_playing'
              ? 'apple-play-button text-white shadow-lg'
              : 'text-gray-400 hover:text-white'
          }`}
          style={activeTab === 'now_playing' ? { boxShadow: `0 0 20px ${activeThemeConfig.glow}` } : {}}
          title="Play & Queue"
        >
          <Disc3 className={`w-5 h-5 ${activeTab === 'now_playing' ? 'animate-spin' : ''}`} style={{ animationDuration: '4s' }} />
        </button>

        {/* 3. Search Tab */}
        <button
          onClick={() => setActiveTab('search')}
          className={`w-11 h-11 rounded-full flex items-center justify-center transition-all ${
            activeTab === 'search'
              ? 'apple-play-button text-white shadow-lg'
              : 'text-gray-400 hover:text-white'
          }`}
          style={activeTab === 'search' ? { boxShadow: `0 0 20px ${activeThemeConfig.glow}` } : {}}
          title="Search"
        >
          <Search className="w-5 h-5" />
        </button>

        {/* 4. Profile & Themes Tab */}
        <button
          onClick={() => setActiveTab('profile')}
          className={`w-11 h-11 rounded-full flex items-center justify-center transition-all ${
            activeTab === 'profile'
              ? 'apple-play-button text-white shadow-lg'
              : 'text-gray-400 hover:text-white'
          }`}
          style={activeTab === 'profile' ? { boxShadow: `0 0 20px ${activeThemeConfig.glow}` } : {}}
          title="Profile & Themes"
        >
          <UserIcon className="w-5 h-5" />
        </button>
      </nav>
    </div>
  );
};

export default App;
