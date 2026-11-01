export type ThemeId = 'purple' | 'cyan' | 'emerald' | 'amber' | 'silver';

export interface ThemeConfig {
  id: ThemeId;
  name: string;
  primary: string;        // Hex for main accent
  secondary: string;      // Hex for gradient end
  glow: string;           // CSS rgba for drop-shadow & glow
  bg: string;             // Deep background
  bgElevated: string;     // Card background
  accentRgb: string;      // "r, g, b"
  gradient: string;       // Tailwind gradient
}

export const THEMES: Record<ThemeId, ThemeConfig> = {
  purple: {
    id: 'purple',
    name: 'Midnight Purple',
    primary: '#a855f7',
    secondary: '#c084fc',
    glow: 'rgba(168, 85, 247, 0.45)',
    bg: '#0d091a',
    bgElevated: '#17102b',
    accentRgb: '168, 85, 247',
    gradient: 'from-purple-500 to-indigo-500'
  },
  cyan: {
    id: 'cyan',
    name: 'Cyber Cyan',
    primary: '#00f2fe',
    secondary: '#38bdf8',
    glow: 'rgba(0, 242, 254, 0.45)',
    bg: '#050a14',
    bgElevated: '#0b1626',
    accentRgb: '0, 242, 254',
    gradient: 'from-cyan-400 to-blue-500'
  },
  emerald: {
    id: 'emerald',
    name: 'Matrix Emerald',
    primary: '#10b981',
    secondary: '#34d399',
    glow: 'rgba(16, 185, 129, 0.45)',
    bg: '#05120d',
    bgElevated: '#0c2219',
    accentRgb: '16, 185, 129',
    gradient: 'from-emerald-400 to-teal-500'
  },
  amber: {
    id: 'amber',
    name: 'Sunset Amber',
    primary: '#f59e0b',
    secondary: '#fbbf24',
    glow: 'rgba(245, 158, 11, 0.45)',
    bg: '#140c04',
    bgElevated: '#241508',
    accentRgb: '245, 158, 11',
    gradient: 'from-amber-400 to-orange-500'
  },
  silver: {
    id: 'silver',
    name: 'Vision Silver',
    primary: '#e2e8f0',
    secondary: '#94a3b8',
    glow: 'rgba(226, 232, 240, 0.35)',
    bg: '#0d1017',
    bgElevated: '#181d28',
    accentRgb: '226, 232, 240',
    gradient: 'from-slate-200 to-slate-400'
  }
};
