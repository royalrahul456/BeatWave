import React, { useState } from 'react';
import { User, Room, ThemeId, ThemeConfig } from '../types';
import { THEMES } from '../theme';
import { Star, Copy, Check, Palette, Sparkles, CheckCircle2 } from 'lucide-react';

interface ProfileViewProps {
  user?: User | null;
  room?: Room | null;
  queueCount: number;
  currentTheme: ThemeId;
  theme: ThemeConfig;
  onSelectTheme: (theme: ThemeId) => void;
}

export const ProfileView: React.FC<ProfileViewProps> = ({ 
  user, 
  room, 
  queueCount, 
  currentTheme,
  theme,
  onSelectTheme 
}) => {
  const [copied, setCopied] = useState(false);

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
    <div className="w-full max-w-md mx-auto px-5 pt-3 pb-32 space-y-5 animate-fade-in">
      {/* Header */}
      <div className="px-1 flex items-center justify-between">
        <div>
          <h2 className="text-xl font-bold text-white tracking-tight">Account & Themes</h2>
          <p className="text-xs text-gray-400">Telegram Profile & Visual Customization</p>
        </div>
        <span 
          className="text-[10px] px-2.5 py-1 rounded-full font-bold border"
          style={{ 
            backgroundColor: `${theme.primary}20`,
            color: theme.primary,
            borderColor: `${theme.primary}40`
          }}
        >
          Synced
        </span>
      </div>

      {/* Main Profile Card in Ultra Liquid Glass */}
      <div className="relative apple-glass-card p-6 rounded-[34px] flex flex-col items-center text-center overflow-hidden border border-white/10 shadow-2xl">
        {/* Subtle background glow */}
        <div 
          className="absolute -top-10 w-48 h-48 rounded-full blur-3xl opacity-30 pointer-events-none"
          style={{ backgroundColor: theme.primary }}
        />

        {/* Profile Avatar with Glowing Rim */}
        <div 
          className="relative w-24 h-24 rounded-full p-1 shadow-2xl mb-4 transition-transform active:scale-95"
          style={{ 
            background: `linear-gradient(135deg, ${theme.secondary}, ${theme.primary})`,
            boxShadow: `0 0 25px ${theme.glow}`
          }}
        >
          <div className="w-full h-full rounded-full overflow-hidden bg-black flex items-center justify-center">
            {user?.photo_url ? (
              <img src={user.photo_url} alt={displayName} className="w-full h-full object-cover" />
            ) : (
              <span className="text-2xl font-black text-white tracking-wider">
                {displayName.slice(0, 2).toUpperCase()}
              </span>
            )}
          </div>
          {isDJ && (
            <div 
              className="absolute -bottom-1 -right-1 px-2.5 py-0.5 rounded-full text-black text-[9px] font-black uppercase shadow-lg"
              style={{ backgroundColor: theme.primary }}
            >
              DJ
            </div>
          )}
        </div>

        {/* Name & Badges */}
        <div className="flex items-center gap-1.5 justify-center mb-1">
          <h3 className="text-xl font-bold text-white tracking-tight">{displayName}</h3>
          {isPremium && (
            <span title="Telegram Premium">
              <Star className="w-4 h-4 fill-amber-400 text-amber-400 animate-pulse" />
            </span>
          )}
        </div>
        <p className="text-xs text-gray-400 font-medium mb-3">{username}</p>

        {/* User ID copy pill */}
        <button
          onClick={handleCopyId}
          className="inline-flex items-center gap-2 px-3.5 py-1.5 rounded-full apple-glass-pill text-xs text-gray-300 hover:text-white transition-all active:scale-95"
        >
          <span className="font-mono text-[11px] text-gray-400">ID: {userId}</span>
          {copied ? <Check className="w-3.5 h-3.5 text-emerald-400" /> : <Copy className="w-3.5 h-3.5 text-gray-400" />}
        </button>
      </div>

      {/* Visual Liquid Glass Themes Section */}
      <div className="apple-glass p-5 rounded-[30px] space-y-4">
        <div className="flex items-center justify-between">
          <span className="text-xs text-white uppercase font-mono tracking-wider flex items-center gap-1.5 font-bold">
            <Palette className="w-4 h-4" style={{ color: theme.primary }} />
            <span>Theme Palettes</span>
          </span>
          <span className="text-[11px] font-medium" style={{ color: theme.primary }}>
            {theme.name}
          </span>
        </div>

        <p className="text-xs text-gray-400 leading-relaxed">
          Select your color aesthetic. Updates dynamic glass refraction, ambient halos, glowing scrubbers, and Telegram header instantly.
        </p>

        {/* Theme Grid */}
        <div className="grid grid-cols-1 gap-2.5 pt-1">
          {themeList.map((t) => {
            const isSelected = currentTheme === t.id;
            return (
              <button
                key={t.id}
                onClick={() => onSelectTheme(t.id)}
                className={`w-full p-3.5 rounded-2xl flex items-center justify-between transition-all active:scale-[0.98] ${
                  isSelected 
                    ? 'apple-glass-card shadow-lg' 
                    : 'bg-white/[0.03] hover:bg-white/[0.06] border border-white/5'
                }`}
                style={
                  isSelected
                    ? {
                        borderColor: t.primary,
                        boxShadow: `0 0 20px ${t.glow}`,
                        backgroundColor: `${t.bgElevated}cc`
                      }
                    : {}
                }
              >
                <div className="flex items-center gap-3">
                  {/* Color Swatch Circle */}
                  <div 
                    className="w-8 h-8 rounded-full shadow-md flex items-center justify-center flex-shrink-0"
                    style={{ 
                      background: `linear-gradient(135deg, ${t.secondary}, ${t.primary})`,
                      boxShadow: `0 0 10px ${t.glow}`
                    }}
                  >
                    {isSelected && <Check className="w-4 h-4 text-white drop-shadow" />}
                  </div>

                  <div className="text-left">
                    <h4 className="text-sm font-bold text-white leading-tight">
                      {t.name}
                    </h4>
                    <p className="text-[11px] text-gray-400 font-mono mt-0.5">
                      {t.primary}
                    </p>
                  </div>
                </div>

                {isSelected ? (
                  <span 
                    className="text-[11px] font-extrabold px-3 py-1 rounded-full uppercase tracking-wider"
                    style={{ 
                      backgroundColor: `${t.primary}25`,
                      color: t.primary,
                      border: `1px solid ${t.primary}50`
                    }}
                  >
                    Active
                  </span>
                ) : (
                  <span className="text-xs text-gray-500 font-medium hover:text-gray-300">
                    Apply
                  </span>
                )}
              </button>
            );
          })}
        </div>
      </div>
    </div>
  );
};
