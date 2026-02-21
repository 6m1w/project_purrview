import Link from "next/link";
import { ArrowRight } from "lucide-react";
import { ScanlineCanvas } from "@/components/ScanlineCanvas";

export default function Home() {
  return (
    <section className="relative flex min-h-[calc(100vh-4rem)] items-center overflow-hidden">
      {/* Left side — title, subtitle, CTA */}
      <div className="relative z-10 flex w-full flex-col gap-8 px-8 md:w-[45%] md:px-12 lg:px-16">
        <h1 className="font-press-start text-5xl md:text-6xl lg:text-7xl font-bold leading-[1.4] tracking-tight uppercase">
          PurrView
        </h1>

        <p className="font-space-mono text-sm md:text-base leading-relaxed max-w-md">
          Lin&apos;s AI cat monitor for 5 happy house cats, tracking meals and
          making smarter decisions for your feline family.
        </p>

        <div className="flex flex-col gap-4 sm:flex-row sm:items-center">
          <Link
            href="/dashboard"
            className="inline-flex items-center gap-2 border-2 border-black bg-black px-6 py-3 font-space-mono text-sm font-bold text-[#f4f4f0] transition-all hover:-translate-y-1 hover:shadow-[6px_6px_0_0_rgba(0,0,0,1)]"
          >
            Get Started
            <ArrowRight className="h-4 w-4" />
          </Link>

          <Link
            href="#how-it-works"
            className="font-space-mono text-sm font-bold transition-colors hover:text-neutral-500"
          >
            See How It Works &gt;
          </Link>
        </div>
      </div>

      {/* Right side — scanline canvas, full viewport, cover mode fills it */}
      <div className="absolute inset-0 hidden md:block">
        <ScanlineCanvas
          videoSrc="/majiang_nobg.webm"
          className="w-full h-full"
        />
      </div>
    </section>
  );
}
