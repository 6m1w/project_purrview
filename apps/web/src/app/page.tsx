import Link from "next/link";
import { ArrowRight } from "lucide-react";
import { HeroCarousel } from "@/components/HeroCarousel";

export default function Home() {
  return (
    <section className="flex flex-col h-[calc(100dvh-8rem)] md:relative md:flex-row md:h-auto md:min-h-[calc(100vh-4rem)] md:items-center overflow-hidden">
      {/* Canvas: flex-grows to fill remaining space on mobile, absolute on desktop */}
      <div className="relative flex-1 min-h-0 md:absolute md:inset-0 md:flex-none">
        <HeroCarousel />
      </div>

      {/* Text content: keeps natural height on mobile, left-aligned on desktop */}
      <div className="relative z-10 shrink-0 flex w-full flex-col gap-4 px-10 pt-4 pb-2 md:shrink md:gap-8 md:py-0 md:w-[45%] md:px-12 lg:px-16">
        {/* Scanline overlay — mobile only, matches canvas aesthetic */}
        <div
          className="absolute inset-0 pointer-events-none md:hidden"
          style={{
            backgroundImage:
              "repeating-linear-gradient(to bottom, transparent, transparent 5px, rgba(0,0,0,0.04) 5px, rgba(0,0,0,0.04) 6px)",
          }}
        />

        <h1 className="font-press-start text-5xl md:text-6xl lg:text-7xl font-bold leading-[1.4] tracking-tight uppercase">
          PurrView
        </h1>

        <p className="font-space-mono text-sm md:text-base font-bold leading-relaxed max-w-md">
          5 cats. Every meal tracked. Zero guesswork.
        </p>

        <div className="flex flex-row items-center gap-4">
          <Link
            href="/dashboard"
            className="inline-flex items-center gap-2 border-2 border-black bg-black text-[#f4f4f0] px-6 py-3 font-space-mono text-sm font-bold transition-all hover:-translate-y-1 hover:shadow-[6px_6px_0_0_rgba(0,0,0,1)]"
          >
            Dashboard
            <ArrowRight className="h-4 w-4" />
          </Link>

          <a
            href="https://github.com/6m1w/project_purrview"
            target="_blank"
            rel="noopener noreferrer"
            className="font-space-mono text-sm font-bold transition-colors hover:text-neutral-500"
          >
            See How It Works &gt;
          </a>
        </div>
      </div>
    </section>
  );
}
