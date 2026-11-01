# BeatWave — Liquid Glass Skill Reference

## Selected reference repository
- Repository: https://github.com/RmaNMetaverse/Apple-LiquidGlass-Skill
- Skill name: `liquidglass`
- Package documented by the skill: `@ybouane/liquidglass`
- Live demo/playground listed by the repository: https://liquid-glass.ybouane.com/

Use this repository as the implementation reference for BeatWave's glassmorphism / liquid-glass visual layer. Do not merely imitate the GitHub screenshot. Read the repository's current `SKILL.md`, README, examples, and relevant references before implementing the UI.

## Antigravity project-level skill setup
The repository README lists this project-level Antigravity/Gemini skill location:

`.agents/skills/liquidglass/`

Recommended workflow:
1. In the BeatWave project root, install or clone the skill using the repository's documented method.
2. Ensure the actual skill instructions are available at `.agents/skills/liquidglass/SKILL.md`.
3. Verify Antigravity recognizes the skill before UI implementation.
4. If automatic installation is unavailable, manually copy the repository's skill files into that project-level directory.
5. Do not blindly execute remote install scripts without reviewing them first.

Repository install instructions shown in its README:
- Windows PowerShell: `irm https://raw.githubusercontent.com/RmaNMetaverse/Apple-LiquidGlass-Skill/main/install.ps1 | iex`
- macOS/Linux: `curl -fsSL https://raw.githubusercontent.com/RmaNMetaverse/Apple-LiquidGlass-Skill/main/install.sh | bash`

Prefer project-level installation for this project so the skill is scoped to BeatWave and can be committed/reproduced with the repository. Review the installer and repository license before running or vendoring files.

## Library integration
The skill documents:
- NPM package: `@ybouane/liquidglass`
- Install: `npm install @ybouane/liquidglass`
- React/Vite integration through `LiquidGlass.init(...)`.
- Glass elements are configured through `data-config` JSON or initialization defaults.
- The `LiquidGlass.init` root and its background/glass layers have direct-child structural requirements.
- Animated content behind glass may require `data-dynamic`.
- Keep the instance and call `instance.destroy()` on component unmount to avoid animation-frame, event-listener, and WebGL-context leaks.

Antigravity must verify the current package API and compatibility from the installed package's own types/docs before writing integration code. Do not assume this reference's examples are guaranteed to match future package versions.

## BeatWave visual application
Use liquid glass selectively:
- Now Playing hero / artwork surround.
- Floating mini-player or compact playback dock.
- Search/filter overlays and modal sheets.
- Queue/member panels where glass improves hierarchy.
- Primary playback controls and selected-state surfaces.

Keep the main background near-black and use cyan as the accent/reflection tint. Glass should read as translucent optical material, not as a flat semi-transparent rectangle. Use subtle blur, refraction, rim highlights, specular response, and controlled cyan tint. Maintain legible text and sufficient contrast.

Suggested starting values from the reference skill's frosted-card preset (tune after testing):
```json
{
  "blurAmount": 0.35,
  "refraction": 0.45,
  "chromAberration": 0.04,
  "edgeHighlight": 0.12,
  "specular": 0.08,
  "fresnel": 0.9,
  "cornerRadius": 28,
  "zRadius": 20,
  "shadowOpacity": 0.25,
  "shadowSpread": 16,
  "shadowOffsetY": 4
}
```

These are starting values, not mandatory constants. Avoid excessive chromatic aberration, glow, blur, or nested glass-on-glass surfaces.

## Telegram Mini App constraints and fallback
- Test the effect inside Telegram Android/iOS WebViews, not only desktop Chrome.
- Detect WebGL availability and handle initialization failures gracefully.
- Provide a CSS fallback using translucent dark surfaces, `backdrop-filter` where supported, subtle borders, and shadows.
- Respect reduced-motion preferences and avoid unnecessary per-frame recapture.
- Keep animated backgrounds behind glass minimal; mark only genuinely changing background elements as dynamic.
- Ensure audio controls remain responsive and never let the glass canvas intercept taps or keyboard focus.
- Keep interactive DOM controls accessible above/alongside the visual glass layer.
- Do not make the entire app depend on WebGL; core playback, search, queue, and permissions must work if the effect is disabled.
- Profile memory, GPU use, scrolling, and battery on lower-end phones.
- Clean up LiquidGlass instances when routes/components unmount.

## Acceptance checklist
- [ ] Antigravity skill installed and recognized at project level.
- [ ] `@ybouane/liquidglass` API verified against installed version.
- [ ] Glass surfaces implemented in selected UI areas only.
- [ ] CSS fallback works when WebGL is unavailable.
- [ ] Telegram WebView touch interaction remains reliable.
- [ ] Reduced-motion and accessibility behavior verified.
- [ ] No WebGL/resource leaks during navigation.
- [ ] UI remains readable over album art and changing backgrounds.
