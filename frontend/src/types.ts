export type { ThemeId, ThemeConfig } from './theme';

export interface User {
  id: string;
  telegram_user_id: number;
  username?: string;
  display_name?: string;
  photo_url?: string;
  is_premium?: boolean;
}

export interface Track {
  id: string;
  provider: string;
  provider_track_id: string;
  title: string;
  artist?: string;
  album?: string;
  duration_ms: number;
  artwork_url?: string;
  audio_url?: string;
  source_attribution?: string;
  availability_status: string;
}

export interface QueueItem {
  id: string;
  room_id: string;
  track: Track;
  requested_by: User;
  position: number;
  status: 'queued' | 'current' | 'played' | 'skipped' | 'removed';
  created_at: string;
}

export interface PlaybackState {
  room_id: string;
  status: 'playing' | 'paused' | 'idle' | 'stopped';
  current_queue_item?: QueueItem;
  position_ms: number;
  started_at?: string;
  paused_at?: string;
  playback_rate: number;
  loop_mode: 'off' | 'track' | 'queue';
  version: number;
  server_time: string;
}

export interface Room {
  id: string;
  group_id: string;
  group_title?: string;
  status: string;
  is_dj: boolean;
  is_admin: boolean;
  current_dj?: User;
  members_count: number;
  members?: User[];
  playback_state?: PlaybackState;
}

export interface LyricLine {
  time_ms: number;
  text: string;
}

export interface LyricsData {
  found: boolean;
  synced: boolean;
  lines: LyricLine[];
  plain: string;
  track_name?: string;
  artist_name?: string;
}

export interface Playlist {
  id: string;
  title: string;
  description?: string;
  tracks: Track[];
  cover_url?: string;
  gradient?: string;
  created_at: string;
}
