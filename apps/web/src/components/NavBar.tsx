"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { Home, LayoutDashboard, Cat, Clock, Github } from "lucide-react";

const navItems = [
  { href: "/", label: "HOME", icon: Home },
  { href: "/dashboard", label: "DASHBOARD", icon: LayoutDashboard },
  { href: "/cats", label: "CATS", icon: Cat },
  { href: "/timeline", label: "TIMELINE", icon: Clock },
];

const GITHUB_URL = "https://github.com/6m1w/project_purrview";

export function NavBar() {
  const pathname = usePathname();

  return (
    <>
      {/* Desktop nav — horizontal buttons */}
      <nav className="hidden md:flex gap-4 items-center">
        {navItems.map((item) => (
          <Link
            key={item.href}
            href={item.href}
            className={`border-2 border-black px-5 py-2 flex items-center font-press-start text-sm font-bold uppercase transition-all hover:-translate-y-1 hover:shadow-[4px_4px_0_0_rgba(0,0,0,1)] ${
              pathname === item.href
                ? "bg-[#00FF66]"
                : "bg-white hover:bg-[#00FF66]"
            }`}
          >
            {item.label}
          </Link>
        ))}
        <a
          href={GITHUB_URL}
          target="_blank"
          rel="noopener noreferrer"
          className="border-2 border-black bg-white p-2 flex items-center transition-all hover:-translate-y-1 hover:shadow-[4px_4px_0_0_rgba(0,0,0,1)] hover:bg-[#00FF66]"
        >
          <Github className="h-5 w-5" />
        </a>
      </nav>

      {/* Mobile bottom tab bar */}
      <nav className="md:hidden fixed bottom-0 left-0 right-0 z-50 border-t-4 border-black bg-[#f4f4f0] shadow-[0_-4px_0_0_rgba(0,0,0,1)]">
        <div className="flex items-center justify-around h-16">
          {navItems.map((item) => {
            const Icon = item.icon;
            const isActive = pathname === item.href;
            return (
              <Link
                key={item.href}
                href={item.href}
                className={`flex flex-col items-center justify-center gap-1 flex-1 h-full transition-colors ${
                  isActive ? "bg-[#00FF66]" : "hover:bg-black/5"
                }`}
              >
                <Icon className="h-5 w-5" strokeWidth={isActive ? 2.5 : 2} />
                <span className="font-press-start text-[8px] font-bold uppercase">
                  {item.label}
                </span>
              </Link>
            );
          })}
        </div>
      </nav>
    </>
  );
}
