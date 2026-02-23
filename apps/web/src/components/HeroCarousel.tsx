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
    config: { cropLeft: 0.23, darknessGamma: 0.75 },
  },
  {
    name: "daji",
    videoSrc: "/daji_nobg.webm",
    config: { cropLeft: 0.23, darknessGamma: 0.75 },
  },
  {
    name: "xiaohei",
    videoSrc: "/xiaohei_nobg.webm",
    config: { cropLeft: 0.23, darknessGamma: 0.7 },
  },
];

export function HeroCarousel() {
  const [active, setActive] = useState(0);
  const [isMobile, setIsMobile] = useState(false);

  useEffect(() => {
    const mq = window.matchMedia("(max-width: 767px)");
    setIsMobile(mq.matches);
    const handler = (e: MediaQueryListEvent) => setIsMobile(e.matches);
    mq.addEventListener("change", handler);
    return () => mq.removeEventListener("change", handler);
  }, []);

  // Preload all videos via hidden video elements (more reliable than <link rel="preload">)
  useEffect(() => {
    const vids = SLIDES.map((s) => {
      const v = document.createElement("video");
      v.preload = "auto";
      v.muted = true;
      v.src = s.videoSrc;
      v.load();
      return v;
    });
    return () => vids.forEach((v) => { v.src = ""; });
  }, []);

  const goTo = useCallback((idx: number) => {
    setActive(idx);
  }, []);

  // Advance to next slide when current video ends
  const handleVideoEnd = useCallback(() => {
    setActive((prev) => (prev + 1) % SLIDES.length);
  }, []);

  const slide = SLIDES[active];
  // On mobile, shift cat left (positive offsetX = content moves left in UV space)
  const mergedConfig = isMobile
    ? { offsetX: 0.0, ...slide.config }
    : slide.config;

  return (
    <>
      {/* Canvas — single instance, hot-swaps video source */}
      <div className="absolute inset-0">
        <ScanlineCanvas
          videoSrc={slide.videoSrc}
          config={mergedConfig}
          onVideoEnd={handleVideoEnd}
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
