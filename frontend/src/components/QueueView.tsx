import React from 'react';
import { Trash2, Disc3, ListMusic, User as UserIcon, Sparkles } from 'lucide-react';
import { QueueItem, Room } from '../types';

interface QueueViewProps {
  queue: QueueItem[];
  room?: Room;
  onRemoveItem: (itemId: string) => Promise<void>;
}

export const QueueView: React.FC<QueueViewProps> = ({ queue, room, onRemoveItem }) => {
  const isDJ = room?.is_dj ?? false;

  const formatDuration = (ms: number) => {
    const totalSecs = Math.floor(ms / 1000);
    const mins = Math.floor(totalSecs / 60);
    const secs = totalSecs % 60;
    return `${mins}:${secs < 10 ? '0' : ''}${secs}`;
  };

  if (queue.length === 0) {
    return (
      <div className="flex flex-col items-center justify-center min-h-[70vh] px-4 text-center">
        <div className="w-full max-w-sm vision-glass p-8 rounded-[36px] flex flex-col items-center">
          <div className="w-20 h-20 rounded-3xl bg-white/5 border border-white/10 flex items-center justify-center mb-4 text-gray-400">
            <ListMusic className="w-10 h-10" />
          </div>
          <h3 className="text-xl font-bold text-white mb-2">No Tracks Queued</h3>
          <p className="text-xs text-gray-400 max-w-xs leading-relaxed mb-4">
            Search for your favorite tracks and queue them up for the whole room!
          </p>
        </div>
      </div>
    );
  }

  return (
    <div className="w-full max-w-md mx-auto px-4 pt-2 pb-28 space-y-3.5">
      {/* Queue Header */}
      <div className="flex items-center justify-between px-1">
        <div>
          <h2 className="text-xl font-bold text-white tracking-tight flex items-center gap-2">
            <span>Live Room Queue</span>
            <span className="text-xs py-0.5 px-2.5 rounded-full bg-cyan-500/20 text-cyan-300 font-semibold border border-cyan-400/30">
              {queue.length}
            </span>
          </h2>
          <p className="text-xs text-gray-400">Upcoming tracks will play in order</p>
        </div>

        {isDJ && (
          <span className="text-[10px] uppercase font-mono px-2.5 py-1 rounded-full bg-cyan-950/60 border border-cyan-400/40 text-cyan-300">
            DJ Moderation
          </span>
        )}
      </div>

      {/* Queue List */}
      <div className="space-y-2.5">
        {queue.map((item, index) => {
          const isCurrent = item.status === 'current';
          return (
            <div
              key={item.id}
              className={`p-3.5 rounded-[26px] flex items-center gap-3 transition-all ${
                isCurrent
                  ? 'vision-glass-glow border-cyan-400/40'
                  : 'vision-card'
              }`}
            >
              {/* Position badge or Live Disc */}
              <div className="w-8 flex items-center justify-center">
                {isCurrent ? (
                  <Disc3 className="w-6 h-6 text-cyan-400 animate-spin" style={{ animationDuration: '3s' }} />
                ) : (
                  <span className="font-mono text-sm font-bold text-gray-400">#{index}</span>
                )}
              </div>

              {/* Artwork */}
              <div className="relative w-14 h-14 rounded-2xl overflow-hidden flex-shrink-0 border border-white/10 shadow-md">
                <img
                  src={item.track.artwork_url || "https://images.unsplash.com/photo-1618005182384-a83a8bd57fbe?w=200&q=80"}
                  alt={item.track.title}
                  className="w-full h-full object-cover"
                />
              </div>

              {/* Metadata */}
              <div className="min-w-0 flex-1">
                <div className="flex items-center gap-1.5">
                  <h4 className="text-sm font-bold text-white truncate">
                    {item.track.title}
                  </h4>
                  {isCurrent && (
                    <span className="text-[9px] px-1.5 py-0.5 rounded-md bg-cyan-400 text-black font-extrabold uppercase">
                      NOW
                    </span>
                  )}
                </div>
                <p className="text-xs text-cyan-300/80 truncate">
                  {item.track.artist || 'Artist'}
                </p>
                <div className="flex items-center gap-2 mt-1 text-[10px] text-gray-400">
                  <span className="flex items-center gap-1">
                    <UserIcon className="w-3 h-3 text-gray-500" />
                    <span>{item.requested_by.display_name || item.requested_by.username || 'Member'}</span>
                  </span>
                  <span>•</span>
                  <span>{formatDuration(item.track.duration_ms)}</span>
                </div>
              </div>

              {/* DJ Action to remove */}
              {isDJ && !isCurrent && (
                <button
                  onClick={() => onRemoveItem(item.id)}
                  className="p-2.5 rounded-xl text-gray-500 hover:text-red-400 hover:bg-red-500/10 transition-colors"
                  title="Remove track"
                >
                  <Trash2 className="w-4 h-4" />
                </button>
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
};
