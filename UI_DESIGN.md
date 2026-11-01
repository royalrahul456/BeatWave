# BeatWave — UI / UX Design Specification

## 1. Brand
- Name: BeatWave
- Theme: Black + Cyan
- Mood: premium, energetic, clean, modern, music-first.
- Do not copy the exact design or assets of Spotify, Apple Music, YouTube Music, or other brands.

## 2. Glassmorphism / Liquid Glass
Use the selected reference skill: https://github.com/RmaNMetaverse/Apple-LiquidGlass-Skill and its `@ybouane/liquidglass` integration guidance. Read `LIQUID_GLASS_REFERENCE.md` and the actual skill before implementation.

Apply refractive glass selectively to the Now Playing hero, mini-player, overlays, queue panels, and selected controls. The visual should feel like translucent optical glass with subtle refraction, blur, cyan-tinted edge highlights, and controlled specular reflections. Keep typography and controls crisp.

Respect the library's root/direct-child structure, dynamic-layer rules, and teardown requirements. Provide a CSS fallback for unsupported WebGL and test in Telegram mobile WebViews. Avoid excessive nested glass, GPU-heavy animation, and any glass canvas that blocks taps or accessibility.

## 2. Color tokens
Suggested starting tokens (adjust after contrast testing):
- `bg-primary`: `#070B0F`
- `bg-secondary`: `#0D141B`
- `surface`: `#111C24`
- `surface-elevated`: `#172630`
- `accent-cyan`: `#00D9F5`
- `accent-cyan-soft`: `#65EAFB`
- `text-primary`: `#F4FAFC`
- `text-secondary`: `#9BB0BA`
- `border-subtle`: `#20323C`
- `danger`: accessible red token
- `success`: accessible green token

Use cyan for primary actions, active playback, focus, and selected states. Do not apply neon glow to every component.

## 3. Typography and shape
- Use a highly readable modern sans-serif.
- Strong hierarchy: track title, artist, section heading, metadata.
- Rounded cards and controls, but avoid excessive pill shapes.
- Touch targets should be comfortably large (aim for 44px minimum).
- Keep important playback controls reachable on small screens.

## 4. Main screen: Room / Now Playing
Include:
- BeatWave wordmark
- Room/group title
- Connection state indicator
- Album artwork
- Track title and artist
- Progress slider with elapsed and remaining/total time
- Play/pause control (disabled/read-only for non-DJ members)
- Previous/next only if supported by room policy; skip is DJ-only
- Queue preview
- Listener count
- Current DJ
- Add song button
- Navigation to queue and search

## 5. Search screen
- Search input with debounce.
- Search results list with artwork, title, artist, duration, source label.
- Add-to-queue action available to all members.
- Loading, no-results, provider-unavailable, and error states.
- Avoid displaying tracks unavailable for the user's territory or playback context.

## 6. Queue screen
- Current track pinned at top.
- Upcoming tracks with requester attribution.
- Drag reorder only for DJ if implemented.
- Remove action only for DJ/moderator.
- Members can add tracks.
- Empty queue illustration/message and search CTA.

## 7. Members / DJ panel
- Listener count.
- Current DJ clearly identified.
- Compact member avatars/initials.
- Group admin controls only when server confirms authority.
- Do not expose unnecessary Telegram profile information.

## 8. Interaction and motion
- Smooth but restrained transitions.
- Reduced-motion preference respected.
- Progress updates should not cause layout shifts.
- Use skeletons for loading.
- Use toast/snackbar messages for queue request success/failure.
- Confirm destructive actions such as clear queue or close room.
- Show an explicit tap-to-start state if autoplay is blocked.

## 9. Telegram Mini App integration
- Use Telegram Web App SDK.
- Respect Telegram viewport and safe-area insets.
- Configure theme/header/background colors where supported.
- Handle back button and close confirmation where appropriate.
- Authenticate using raw initData sent to backend for validation.
- Do not assume every Telegram client supports identical WebView features.

## 10. Required states
- Initial loading
- Room not found
- Room ended
- Room access denied
- No current track
- Queue empty
- Searching
- No search results
- Provider unavailable
- Audio loading
- Autoplay blocked
- Audio playback error
- Offline
- WebSocket reconnecting
- Permission denied
- Track unavailable
