import type { Metadata } from "next";
import { VT323, Space_Mono, Pixelify_Sans, Noto_Sans_SC } from "next/font/google";
import Link from "next/link";
import { NavBar } from "@/components/NavBar";
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

const pixelifySans = Pixelify_Sans({
  weight: ["400", "500", "600", "700"],
  variable: "--font-press-start",
  subsets: ["latin"],
});

const notoSansSC = Noto_Sans_SC({
  weight: ["400", "500", "700"],
  variable: "--font-noto-sc",
  subsets: ["latin"],
});

const SITE_URL = "https://purrview.vercel.app";
const TITLE = "PurrView — AI-Powered Care for 5 Beloved Cats";
const DESCRIPTION =
  "An open-source AI dashboard that watches over 5 rescue cats — tracking every meal, sip, and visit with computer vision and Gemini, so they never miss a beat.";

export const metadata: Metadata = {
  title: {
    default: TITLE,
    template: "%s | PurrView",
  },
  description: DESCRIPTION,
  metadataBase: new URL(SITE_URL),
  openGraph: {
    title: TITLE,
    description: DESCRIPTION,
    url: SITE_URL,
    siteName: "PurrView",
    locale: "en_US",
    type: "website",
    images: [
      {
        url: "/og-image.png",
        width: 1200,
        height: 630,
        alt: "PurrView — AI care for 5 beloved cats",
      },
    ],
  },
  twitter: {
    card: "summary_large_image",
    title: TITLE,
    description: DESCRIPTION,
    images: ["/og-image.png"],
  },
  keywords: [
    "cat monitor",
    "AI pet care",
    "feeding tracker",
    "computer vision",
    "rescue cats",
    "Gemini AI",
    "open source",
    "pet dashboard",
  ],
  robots: {
    index: true,
    follow: true,
  },
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en">
      <body
        className={`${vt323.variable} ${spaceMono.variable} ${pixelifySans.variable} ${notoSansSC.variable} font-mono antialiased bg-[#f4f4f0] text-black w-full min-h-screen overflow-x-hidden m-0 p-0`}
      >
        <header className="sticky top-0 z-50 border-b-4 border-black bg-[#f4f4f0] shadow-[0_4px_0_0_rgba(0,0,0,1)] relative">
          <div className="mx-auto flex h-16 w-full max-w-[1600px] items-center justify-between px-6">
            <Link href="/" className="font-press-start text-2xl font-bold uppercase hover:text-[#FF5722] transition-colors">
              PurrView
            </Link>
            <NavBar />
          </div>
        </header>
        <main className="w-full flex-grow pb-20 md:pb-0">{children}</main>
      </body>
    </html>
  );
}
