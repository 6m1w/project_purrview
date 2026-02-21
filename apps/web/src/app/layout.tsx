import type { Metadata } from "next";
import { VT323, Space_Mono, Press_Start_2P } from "next/font/google";
import Link from "next/link";
import "./globals.css";

const vt323 = VT323({
  weight: "400",
  variable: "--font-vt323",
  subsets: ["latin"],
});

const spaceMono = Space_Mono({
  weight: ["400", "700"],
  variable: "--font-space-mono",
  subsets: ["latin"],
});

const pressStart2P = Press_Start_2P({
  weight: "400",
  variable: "--font-press-start",
  subsets: ["latin"],
});

export const metadata: Metadata = {
  title: "PurrView - Cat Feeding Monitor",
  description: "Monitor your cats' feeding habits with AI-powered analysis",
};

const navItems = [
  { href: "/", label: "HOME" },
  { href: "/dashboard", label: "DASHBOARD" },
  { href: "/cats", label: "CATS" },
  { href: "/timeline", label: "TIMELINE" },
];

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en">
      <body
        className={`${vt323.variable} ${spaceMono.variable} ${pressStart2P.variable} font-mono antialiased bg-[#f4f4f0] text-black w-full min-h-screen overflow-x-hidden m-0 p-0`}
      >
        <header className="sticky top-0 z-50 border-b-4 border-black bg-[#f4f4f0] shadow-[0_4px_0_0_rgba(0,0,0,1)]">
          <div className="mx-auto flex h-16 w-full max-w-[1600px] items-center justify-between px-6">
            <Link href="/" className="text-4xl font-vt323 tracking-widest uppercase hover:text-[#FF5722] transition-colors">
              PurrView
            </Link>
            <nav className="flex gap-4">
              {navItems.map((item) => (
                <Link
                  key={item.href}
                  href={item.href}
                  className="border-2 border-black bg-white px-4 py-1 flex items-center text-sm font-bold uppercase transition-all hover:-translate-y-1 hover:shadow-[4px_4px_0_0_rgba(0,0,0,1)] hover:bg-[#00FF66]"
                >
                  {item.label}
                </Link>
              ))}
            </nav>
          </div>
        </header>
        <main className="w-full flex-grow">{children}</main>
      </body>
    </html>
  );
}
