import React, { useEffect, useRef } from 'react';

interface LiquidGlassCardProps {
  children: React.ReactNode;
  className?: string;
  variant?: 'cyan' | 'default';
  onClick?: () => void;
}

export const LiquidGlassCard: React.FC<LiquidGlassCardProps> = ({
  children,
  className = '',
  variant = 'cyan',
  onClick
}) => {
  const cardRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    let instance: any = null;
    let isCancelled = false;

    // Dynamically attempt to initialize LiquidGlass if available in the browser environment
    async function initGlass() {
      try {
        const mod = await import('@ybouane/liquidglass');
        const LiquidGlass = mod.LiquidGlass || (mod as any).default;

        if (LiquidGlass && cardRef.current && !isCancelled) {
          // Initialize WebGL effect on element with selective Black + Cyan preset
          instance = LiquidGlass.init(cardRef.current, {
            blurAmount: 0.35,
            refraction: 0.40,
            chromAberration: 0.03,
            edgeHighlight: 0.15,
            specular: 0.10,
            fresnel: 0.85,
            cornerRadius: 24,
            tint: [0.0, 0.95, 1.0, 0.08] // Subtle cyan tint
          });
        }
      } catch (err) {
        // Fallback transparently active via CSS
      }
    }

    initGlass();

    return () => {
      isCancelled = true;
      if (instance && typeof instance.destroy === 'function') {
        try {
          instance.destroy();
        } catch (e) {
          // Ignore teardown errors
        }
      }
    };
  }, []);

  const baseStyle = variant === 'cyan' ? 'glass-panel-cyan' : 'glass-panel';

  return (
    <div
      ref={cardRef}
      onClick={onClick}
      className={`relative rounded-3xl p-5 overflow-hidden transition-all duration-300 ${baseStyle} ${className}`}
    >
      {/* Specular glare simulation layer */}
      <div className="absolute inset-0 bg-gradient-to-tr from-cyan-500/10 via-transparent to-white/5 pointer-events-none rounded-3xl" />
      <div className="relative z-10">
        {children}
      </div>
    </div>
  );
};
