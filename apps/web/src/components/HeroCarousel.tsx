"use client";

import { useState, useCallback, useEffect } from "react";
import { ScanlineCanvas, type ScanlineConfig } from "./ScanlineCanvas";

interface CatSlide {
  name: string;
  videoSrc: string;
  config?: Partial<ScanlineConfig>;
}

// Per-cat video configs (tune each via /shader-debug.html then paste here)
const SLIDES: CatSlide[] = [
  {
    name: "majiang",
    videoSrc: "/majiang_nobg.webm",
    // Default config works for majiang
  },
  {
    name: "songhua",
    videoSrc: "/songhua_nobg.webm",
    // TODO: tune via shader-debug.html
  },
  {
    name: "xiaoman",
    videoSrc: "/xiaoman_nobg.webm",
    // TODO: tune via shader-debug.html
  },
  // TODO: add daji, xiaohei
];

export function HeroCarousel() {
  const [active, setActive] = useState(0);

  const goTo = useCallback((idx: number) => {
    setActive(idx);
  }, []);

  // Auto-advance every 8 seconds
  useEffect(() => {
    const timer = setInterval(() => {
      setActive((prev) => (prev + 1) % SLIDES.length);
    }, 8000);
    return () => clearInterval(timer);
  }, []);

  const slide = SLIDES[active];

  return (
    <>
      {/* Canvas — key forces remount on slide change to swap video */}
      <div className="absolute inset-0 hidden md:block">
        <ScanlineCanvas
          key={slide.name}
          videoSrc={slide.videoSrc}
          config={slide.config}
          className="w-full h-full"
        />
      </div>

      {/* Dot indicators */}
      <div className="absolute bottom-8 left-1/2 z-20 flex -translate-x-1/2 gap-3">
        {SLIDES.map((s, i) => (
          <button
            key={s.name}
            onClick={() => goTo(i)}
            className={`h-3 w-3 border-2 border-black transition-all ${
              i === active
                ? "bg-black scale-125"
                : "bg-white hover:bg-black/30"
            }`}
            aria-label={`Show ${s.name}`}
          />
        ))}
      </div>
    </>
  );
}
