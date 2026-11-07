import React, { useState } from 'react';
import { User, Room, ThemeId, ThemeConfig, Playlist } from '../types';
import { THEMES } from '../theme';
import { 
  Star, 
  Copy, 
  Check, 
  Palette, 
  Crown, 
  Radio, 
  Sparkles, 
  ListMusic, 
  Sliders, 
  ShieldCheck, 
  Zap, 
  ExternalLink,
  Music,
  Headphones,
  Flame,
  Volume2
} from 'lucide-react';

interface ProfileViewProps {
  user?: User | null;
  room?: Room | null;
  queueCount: number;
  currentTheme: ThemeId;
  theme: ThemeConfig;
  onSelectTheme: (theme: ThemeId) => void;
  playlists: Playlist[];
  onOpenPlaylistModal: () => void;
}

export const ProfileView: React.FC<ProfileViewProps> = ({ 
  user, 
  room, 
  queueCount, 
  currentTheme,
  theme,
  onSelectTheme,
  playlists,
  onOpenPlaylistModal
}) => {
  const [copied, setCopied] = useState(false);
  const [streamQuality, setStreamQuality] = useState<'320k' | '192k' | '128k'>('320k');
  const [lowLatency, setLowLatency] = useState(true);

  const isDJ = room?.is_dj ?? false;
  const displayName = user?.display_name || user?.username || "Telegram User";
  const username = user?.username ? `@${user.username}` : "No username";
  const userId = user?.telegram_user_id || 999999999;
  const isPremium = user?.is_premium ?? true;

  const handleCopyId = () => {
    navigator.clipboard?.writeText(String(userId));
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  const themeList = Object.values(THEMES);

  return (
    <div className="w-full max-w-md mx-auto px-5 pt-3 pb-36 space-y-4 animate-fade-in">
      {/* Header */}
      <div className="px-1 flex items-center justify-between">
        <div>
          <h2 className="text-xl font-bold text-white tracking-tight">Hub & Settings</h2>
          <p className="text-xs text-gray-400">Profile, Themes, Playlists & Engine</p>
        </div>
        <div 
          className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-bold border"
          style={{ 
            backgroundColor: `${theme.primary}15`,
            color: theme.primary,
            borderColor: `${theme.primary}40`
          }}
        >
          <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-pulse" />
          <span>Live Sync</span>
        </div>
      </div>

      {/* Main Profile Card in Ultra Liquid Glass */}
      <div className="relative apple-glass-card p-5 rounded-[30px] flex items-center gap-4 overflow-hidden border border-white/10 shadow-2xl">
        {/* Ambient Halo */}
        <div 
          className="absolute -top-12 -right-12 w-36 h-36 rounded-full blur-3xl opacity-35 pointer-events-none"
          style={{ backgroundColor: theme.primary }}
        />

        {/* Profile Avatar with Glowing Rim */}
        <div 
          className="relative w-16 h-16 rounded-full p-0.5 shadow-xl flex-shrink-0"
          style={{ 
            background: `linear-gradient(135deg, ${theme.secondary}, ${theme.primary})`,
            boxShadow: `0 0 20px ${theme.glow}`
          }}
        >
          <div className="w-full h-full rounded-full overflow-hidden bg-black flex items-center justify-center">
            {user?.photo_url ? (
              <img src={user.photo_url} alt={displayName} className="w-full h-full object-cover" />
            ) : (
              <span className="text-xl font-black text-white tracking-wider">
                {displayName.slice(0, 2).toUpperCase()}
              </span>
            )}
          </div>
          {isDJ && (
            <div 
              className="absolute -bottom-1 -right-1 px-2 py-0.2 rounded-full text-black text-[9px] font-black uppercase shadow-lg border border-white/20"
              style={{ backgroundColor: theme.primary }}
            >
              DJ
            </div>
          )}
        </div>

        {/* User Details */}
        <div className="min-w-0 flex-1">
          <div className="flex items-center gap-1.5">
            <h3 className="text-base font-bold text-white tracking-tight truncate">{displayName}</h3>
            {isPremium && (
              <Star className="w-3.5 h-3.5 fill-amber-400 text-amber-400 flex-shrink-0" />
            )}
          </div>
          <p className="text-xs text-gray-400 font-medium truncate">{username}</p>

          <button
            onClick={handleCopyId}
            className="inline-flex items-center gap-1.5 mt-1.5 text-[11px] text-gray-400 hover:text-white"
          >
            <span className="font-mono">ID: {userId}</span>
            {copied ? <Check className="w-3 h-3 text-emerald-400" /> : <Copy className="w-3 h-3 text-gray-500" />}
          </button>
        </div>
      </div>

      {/* COMPACT THEME SELECTOR IN A SHORT PLACE */}
      <div className="p-4 rounded-2xl apple-glass-card space-y-2.5">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-1.5 text-xs font-bold text-white uppercase font-mono tracking-wider">
            <Palette className="w-3.5 h-3.5" style={{ color: theme.primary }} />
            <span>Theme Aesthetics</span>
          </div>
          <span className="text-xs font-semibold" style={{ color: theme.primary }}>
            {theme.name}
          </span>
        </div>

        {/* Horizontal Mini Swatch Grid */}
        <div className="grid grid-cols-5 gap-2 pt-1">
          {themeList.map((t) => {
            const isSelected = currentTheme === t.id;
            return (
              <button
                key={t.id}
                onClick={() => onSelectTheme(t.id)}
                className={`py-2 px-1 rounded-xl flex flex-col items-center gap-1.5 transition-all active:scale-95 ${
                  isSelected
                    ? 'bg-white/15 border border-white/40 shadow-lg'
                    : 'bg-white/[0.03] border border-white/5 hover:bg-white/[0.08]'
                }`}
                style={isSelected ? { boxShadow: `0 0 16px ${t.glow}` } : {}}
                title={t.name}
              >
                <div 
                  className="w-5 h-5 rounded-full border border-white/20 shadow-sm"
                  style={{ backgroundColor: t.primary }}
                />
                <span className="text-[10px] text-gray-300 font-medium truncate w-full text-center">
                  {t.name.split(' ')[0]}
                </span>
              </button>
            );
          })}
        </div>
      </div>

      {/* PLAYLISTS SHORTCUT CARD */}
      <div 
        onClick={onOpenPlaylistModal}
        className="p-4 rounded-2xl apple-glass-card flex items-center justify-between gap-3 cursor-pointer hover:border-cyan-400/40 transition-all group"
      >
        <div className="flex items-center gap-3">
          <div 
            className="w-10 h-10 rounded-xl flex items-center justify-center font-bold shadow-md"
            style={{ backgroundColor: `${theme.primary}25`, color: theme.primary }}
          >
            <ListMusic className="w-5 h-5" />
          </div>
          <div>
            <h4 className="text-xs font-bold text-white tracking-wide">My Custom Playlists</h4>
            <p className="text-[11px] text-gray-400">
              {playlists.length} created • Tap to view & make playlists
            </p>
          </div>
        </div>

        <span 
          className="text-xs px-3 py-1 rounded-full font-bold text-black flex items-center gap-1 group-hover:scale-105 transition-transform"
          style={{ backgroundColor: theme.primary }}
        >
          <span>Manage</span>
        </span>
      </div>

      {/* BOT OWNER & DEVELOPER ATTRIBUTION */}
      <div className="p-4 rounded-2xl apple-glass-card space-y-3 border border-amber-500/20 bg-gradient-to-br from-amber-500/5 to-transparent">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <Crown className="w-4 h-4 text-amber-400" />
            <span className="text-xs font-bold text-amber-300 uppercase tracking-wider font-mono">
              Bot Creator & Owner
            </span>
          </div>
          <span className="text-[10px] px-2 py-0.5 rounded-full bg-amber-400/20 text-amber-300 border border-amber-400/30 font-bold">
            Verified Dev
          </span>
        </div>

        <div className="flex items-center justify-between gap-3">
          <div className="flex items-center gap-2.5">
            <div className="w-9 h-9 rounded-full bg-gradient-to-tr from-amber-500 to-yellow-300 text-black flex items-center justify-center font-black text-sm shadow-md">
              R
            </div>
            <div>
              <p className="text-xs font-bold text-white">Rahul</p>
              <p className="text-[10px] text-gray-400">@royalrahul456 • Lead Developer</p>
            </div>
          </div>

          <a
            href="https://t.me/royalrahul456"
            target="_blank"
            rel="noopener noreferrer"
            className="px-3 py-1.5 rounded-full apple-glass-pill text-xs text-amber-300 hover:text-white flex items-center gap-1 font-semibold border-amber-400/30 transition-all active:scale-95"
          >
            <span>Message</span>
            <ExternalLink className="w-3 h-3" />
          </a>
        </div>
      </div>

      {/* AUDIO ENGINE & FIDELITY SETTINGS */}
      <div className="p-4 rounded-2xl apple-glass-card space-y-3">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-1.5 text-xs font-bold text-white uppercase font-mono">
            <Volume2 className="w-3.5 h-3.5 text-cyan-400" />
            <span>Streaming Engine</span>
          </div>
          <span className="text-[10px] font-mono text-cyan-300">v2.4 Active</span>
        </div>

        {/* Quality selector */}
        <div className="grid grid-cols-3 gap-2">
          {[
            { id: '320k', label: '320k Master', desc: 'Ultra HD' },
            { id: '192k', label: '192k High', desc: 'Balanced' },
            { id: '128k', label: '128k Eco', desc: 'Low Data' }
          ].map((q) => (
            <button
              key={q.id}
              onClick={() => setStreamQuality(q.id as any)}
              className={`p-2 rounded-xl text-center transition-all ${
                streamQuality === q.id
                  ? 'bg-cyan-500/20 border border-cyan-400 text-cyan-300 shadow-sm'
                  : 'bg-white/[0.02] border border-white/5 text-gray-400'
              }`}
            >
              <div className="text-xs font-bold">{q.label}</div>
              <div className="text-[9px] opacity-70">{q.desc}</div>
            </button>
          ))}
        </div>

        {/* Toggle */}
        <div className="flex items-center justify-between pt-1 text-xs">
          <span className="text-gray-300">Ultra-Low Latency Mode</span>
          <button
            onClick={() => setLowLatency(!lowLatency)}
            className={`w-9 h-5 rounded-full transition-colors relative ${
              lowLatency ? 'bg-cyan-500' : 'bg-gray-700'
            }`}
          >
            <div 
              className={`w-4 h-4 rounded-full bg-white absolute top-0.5 transition-transform ${
                lowLatency ? 'left-4' : 'left-0.5'
              }`}
            />
          </button>
        </div>
      </div>

      {/* LISTENER STATS */}
      <div className="grid grid-cols-3 gap-2">
        <div className="p-3 rounded-2xl apple-glass-card text-center">
          <Headphones className="w-4 h-4 mx-auto text-cyan-400 mb-1" />
          <p className="text-base font-bold text-white">{room?.members_count || 1}</p>
          <p className="text-[9px] text-gray-400 uppercase font-mono">In Room</p>
        </div>
        <div className="p-3 rounded-2xl apple-glass-card text-center">
          <Flame className="w-4 h-4 mx-auto text-amber-400 mb-1" />
          <p className="text-base font-bold text-white">{queueCount}</p>
          <p className="text-[9px] text-gray-400 uppercase font-mono">In Queue</p>
        </div>
        <div className="p-3 rounded-2xl apple-glass-card text-center">
          <Radio className="w-4 h-4 mx-auto text-emerald-400 mb-1" />
          <p className="text-base font-bold text-white">Lossless</p>
          <p className="text-[9px] text-gray-400 uppercase font-mono">Audio Sync</p>
        </div>
      </div>
    </div>
  );
};
