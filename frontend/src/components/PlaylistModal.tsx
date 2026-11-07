import React, { useState } from 'react';
import { Playlist, Track, ThemeConfig } from '../types';
import { 
  X, 
  Plus, 
  Music2, 
  Play, 
  Trash2, 
  Check, 
  ListPlus, 
  FolderPlus, 
  Sparkles,
  ChevronRight
} from 'lucide-react';

interface PlaylistModalProps {
  isOpen: boolean;
  onClose: () => void;
  playlists: Playlist[];
  onCreatePlaylist: (title: string, description?: string) => void;
  onDeletePlaylist: (playlistId: string) => void;
  onAddTrackToPlaylist: (playlistId: string, track: Track) => void;
  onRemoveTrackFromPlaylist: (playlistId: string, trackId: string) => void;
  onPlayPlaylist: (playlist: Playlist) => void;
  trackToAdd?: Track | null;
  theme: ThemeConfig;
}

export const PlaylistModal: React.FC<PlaylistModalProps> = ({
  isOpen,
  onClose,
  playlists,
  onCreatePlaylist,
  onDeletePlaylist,
  onAddTrackToPlaylist,
  onRemoveTrackFromPlaylist,
  onPlayPlaylist,
  trackToAdd,
  theme
}) => {
  const [selectedPlaylistId, setSelectedPlaylistId] = useState<string | null>(null);
  const [isCreating, setIsCreating] = useState(false);
  const [newTitle, setNewTitle] = useState('');
  const [newDesc, setNewDesc] = useState('');
  const [addedSuccessId, setAddedSuccessId] = useState<string | null>(null);

  if (!isOpen) return null;

  const selectedPlaylist = playlists.find(p => p.id === selectedPlaylistId);

  const handleCreate = (e: React.FormEvent) => {
    e.preventDefault();
    if (!newTitle.trim()) return;
    onCreatePlaylist(newTitle.trim(), newDesc.trim() || undefined);
    setNewTitle('');
    setNewDesc('');
    setIsCreating(false);
  };

  const handleAddTrack = (playlistId: string) => {
    if (!trackToAdd) return;
    onAddTrackToPlaylist(playlistId, trackToAdd);
    setAddedSuccessId(playlistId);
    setTimeout(() => {
      setAddedSuccessId(null);
      onClose();
    }, 1200);
  };

  return (
    <div className="fixed inset-0 z-50 flex items-end sm:items-center justify-center p-0 sm:p-4 bg-black/80 backdrop-blur-md animate-fade-in">
      <div 
        className="w-full max-w-md max-h-[85vh] apple-glass p-5 rounded-t-[36px] sm:rounded-[36px] flex flex-col border border-white/15 shadow-[0_30px_70px_rgba(0,0,0,0.95)] overflow-hidden"
      >
        {/* Header */}
        <div className="flex items-center justify-between pb-3 border-b border-white/10">
          <div className="flex items-center gap-2">
            <div 
              className="w-8 h-8 rounded-full flex items-center justify-center"
              style={{ backgroundColor: `${theme.primary}25`, color: theme.primary }}
            >
              <Music2 className="w-4 h-4" />
            </div>
            <div>
              <h3 className="text-base font-bold text-white tracking-tight">
                {selectedPlaylist ? selectedPlaylist.title : trackToAdd ? 'Add to Playlist' : 'My Playlists'}
              </h3>
              <p className="text-[11px] text-gray-400">
                {selectedPlaylist 
                  ? `${selectedPlaylist.tracks.length} tracks` 
                  : `${playlists.length} playlists available`}
              </p>
            </div>
          </div>

          <div className="flex items-center gap-2">
            {selectedPlaylist && (
              <button
                onClick={() => setSelectedPlaylistId(null)}
                className="text-xs px-2.5 py-1 rounded-full bg-white/10 hover:bg-white/20 text-gray-300 font-medium"
              >
                Back
              </button>
            )}
            <button
              onClick={onClose}
              className="w-8 h-8 rounded-full apple-glass-pill flex items-center justify-center text-gray-400 hover:text-white"
            >
              <X className="w-4 h-4" />
            </button>
          </div>
        </div>

        {/* Content Area */}
        <div className="flex-1 overflow-y-auto no-scrollbar py-3 space-y-3">
          {/* Create Playlist Form Drawer */}
          {isCreating ? (
            <form onSubmit={handleCreate} className="p-4 rounded-2xl apple-glass-card space-y-3 animate-fade-in">
              <div className="flex items-center justify-between">
                <span className="text-xs font-bold text-white uppercase font-mono">Create New Playlist</span>
                <button
                  type="button"
                  onClick={() => setIsCreating(false)}
                  className="text-xs text-gray-400 hover:text-white"
                >
                  Cancel
                </button>
              </div>

              <input
                type="text"
                placeholder="Playlist name (e.g. Midnight Beats)"
                value={newTitle}
                onChange={(e) => setNewTitle(e.target.value)}
                maxLength={40}
                required
                className="w-full px-3.5 py-2.5 rounded-xl bg-black/50 border border-white/15 text-white text-xs placeholder-gray-500 focus:outline-none focus:border-cyan-400"
              />

              <input
                type="text"
                placeholder="Optional description"
                value={newDesc}
                onChange={(e) => setNewDesc(e.target.value)}
                maxLength={60}
                className="w-full px-3.5 py-2.5 rounded-xl bg-black/50 border border-white/15 text-white text-xs placeholder-gray-500 focus:outline-none focus:border-cyan-400"
              />

              <button
                type="submit"
                className="w-full py-2.5 rounded-xl text-xs font-bold text-black flex items-center justify-center gap-1.5 shadow-lg active:scale-95 transition-all"
                style={{ backgroundColor: theme.primary }}
              >
                <FolderPlus className="w-3.5 h-3.5" />
                <span>Save Playlist</span>
              </button>
            </form>
          ) : (
            !selectedPlaylist && (
              <button
                onClick={() => setIsCreating(true)}
                className="w-full p-3 rounded-2xl border border-dashed border-white/20 hover:border-cyan-400/60 bg-white/[0.02] hover:bg-white/[0.05] flex items-center justify-center gap-2 text-xs font-semibold text-gray-300 hover:text-white transition-all group"
              >
                <Plus className="w-4 h-4 text-cyan-400 group-hover:scale-110 transition-transform" />
                <span>Create New Custom Playlist</span>
              </button>
            )
          )}

          {/* Active Playlist Detail View */}
          {selectedPlaylist ? (
            <div className="space-y-3">
              {/* Playlist Action Bar */}
              <div className="p-3.5 rounded-2xl apple-glass-card flex items-center justify-between gap-3">
                <div className="min-w-0">
                  <p className="text-xs text-gray-400 truncate">
                    {selectedPlaylist.description || 'Custom playlist crafted in BeatWave'}
                  </p>
                </div>

                <div className="flex items-center gap-2 flex-shrink-0">
                  <button
                    onClick={() => {
                      onPlayPlaylist(selectedPlaylist);
                      onClose();
                    }}
                    disabled={selectedPlaylist.tracks.length === 0}
                    className="px-3.5 py-1.5 rounded-full text-xs font-bold text-black flex items-center gap-1.5 shadow-md active:scale-95 transition-all disabled:opacity-40"
                    style={{ backgroundColor: theme.primary }}
                  >
                    <Play className="w-3 h-3 fill-current" />
                    <span>Play in Room</span>
                  </button>

                  <button
                    onClick={() => {
                      onDeletePlaylist(selectedPlaylist.id);
                      setSelectedPlaylistId(null);
                    }}
                    className="p-1.5 rounded-full text-gray-400 hover:text-rose-400 hover:bg-rose-500/10 transition-colors"
                    title="Delete Playlist"
                  >
                    <Trash2 className="w-3.5 h-3.5" />
                  </button>
                </div>
              </div>

              {/* Tracks List inside Playlist */}
              {selectedPlaylist.tracks.length === 0 ? (
                <div className="p-8 rounded-2xl bg-white/[0.02] border border-white/5 text-center space-y-2">
                  <Music2 className="w-8 h-8 mx-auto text-gray-600" />
                  <p className="text-xs text-gray-400">This playlist is empty.</p>
                  <p className="text-[11px] text-gray-500">
                    Use the Search tab or Now Playing screen to add songs here!
                  </p>
                </div>
              ) : (
                <div className="space-y-1.5">
                  {selectedPlaylist.tracks.map((t, idx) => (
                    <div
                      key={`${t.id}-${idx}`}
                      className="p-2.5 rounded-xl apple-glass-card flex items-center justify-between gap-3 group"
                    >
                      <div className="flex items-center gap-2.5 min-w-0 flex-1">
                        <span className="text-[10px] font-mono text-gray-500 w-4 text-center">
                          {idx + 1}
                        </span>
                        <img
                          src={t.artwork_url || 'https://images.unsplash.com/photo-1511671782779-c97d3d27a1d4?w=100'}
                          alt={t.title}
                          className="w-9 h-9 rounded-lg object-cover flex-shrink-0"
                        />
                        <div className="min-w-0 flex-1">
                          <p className="text-xs font-bold text-white truncate">{t.title}</p>
                          <p className="text-[10px] text-gray-400 truncate">{t.artist || 'Artist'}</p>
                        </div>
                      </div>

                      <button
                        onClick={() => onRemoveTrackFromPlaylist(selectedPlaylist.id, t.id)}
                        className="p-1 text-gray-500 hover:text-rose-400 opacity-60 group-hover:opacity-100 transition-opacity"
                        title="Remove track"
                      >
                        <Trash2 className="w-3.5 h-3.5" />
                      </button>
                    </div>
                  ))}
                </div>
              )}
            </div>
          ) : (
            /* Playlists Directory List */
            <div className="space-y-2">
              {playlists.map((pl) => {
                const isAdded = addedSuccessId === pl.id;
                return (
                  <div
                    key={pl.id}
                    className="p-3 rounded-2xl apple-glass-card flex items-center justify-between gap-3 group hover:border-white/20 transition-all cursor-pointer"
                    onClick={() => {
                      if (trackToAdd) {
                        handleAddTrack(pl.id);
                      } else {
                        setSelectedPlaylistId(pl.id);
                      }
                    }}
                  >
                    <div className="flex items-center gap-3 min-w-0 flex-1">
                      <div 
                        className="w-11 h-11 rounded-xl flex items-center justify-center font-bold text-white shadow-md flex-shrink-0"
                        style={{
                          background: pl.gradient || `linear-gradient(135deg, ${theme.secondary}, ${theme.primary})`
                        }}
                      >
                        <Music2 className="w-5 h-5 text-black" />
                      </div>

                      <div className="min-w-0 flex-1">
                        <h4 className="text-xs font-bold text-white truncate">{pl.title}</h4>
                        <p className="text-[10px] text-gray-400 truncate">
                          {pl.tracks.length} {pl.tracks.length === 1 ? 'track' : 'tracks'}
                          {pl.description ? ` • ${pl.description}` : ''}
                        </p>
                      </div>
                    </div>

                    <div className="flex items-center gap-1.5 flex-shrink-0">
                      {trackToAdd ? (
                        <button
                          onClick={(e) => {
                            e.stopPropagation();
                            handleAddTrack(pl.id);
                          }}
                          className={`px-3 py-1.5 rounded-full text-xs font-bold transition-all ${
                            isAdded
                              ? 'bg-emerald-500 text-black'
                              : 'apple-glass-pill text-white hover:border-cyan-400'
                          }`}
                        >
                          {isAdded ? (
                            <span className="flex items-center gap-1">
                              <Check className="w-3.5 h-3.5" /> Added
                            </span>
                          ) : (
                            <span className="flex items-center gap-1">
                              <Plus className="w-3.5 h-3.5" /> Add
                            </span>
                          )}
                        </button>
                      ) : (
                        <div className="flex items-center gap-1 text-gray-400 group-hover:text-white">
                          <ChevronRight className="w-4 h-4" />
                        </div>
                      )}
                    </div>
                  </div>
                );
              })}
            </div>
          )}
        </div>
      </div>
    </div>
  );
};
