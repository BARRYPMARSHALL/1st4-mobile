import type { Metadata } from "next";
import { Geist, Geist_Mono } from "next/font/google";
import "./globals.css";
import Link from "next/link";
import { PhoneIcon } from "lucide-react";

const geistSans = Geist({
  variable: "--font-geist-sans",
  subsets: ["latin"],
});

const geistMono = Geist_Mono({
  variable: "--font-geist-mono",
  subsets: ["latin"],
});

export const metadata: Metadata = {
  title: "1st 4 Mobile — Uncover Systemic Overcharges in Corporate Mobile & Fleet Data Invoices",
  description:
    "AI-powered audit platform that detects hidden overcharges in your corporate mobile and fleet data invoices. Save up to 35% on annual telecom costs.",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html
      lang="en"
      className={`${geistSans.variable} ${geistMono.variable} h-full antialiased`}
    >
      <body className="min-h-full flex flex-col">
        <header className="sticky top-0 z-50 w-full border-b border-white/10 bg-[#0a1628]/95 backdrop-blur supports-[backdrop-filter]:bg-[#0a1628]/80">
          <div className="mx-auto flex h-14 max-w-7xl items-center justify-between px-4 sm:px-6">
            <Link
              href="/"
              className="flex items-center gap-2 text-lg font-bold tracking-tight text-white"
            >
              <PhoneIcon className="h-5 w-5 text-[#2563eb]" />
              <span>1st <span className="text-[#2563eb]">4</span> Mobile</span>
            </Link>
            <nav className="hidden items-center gap-6 sm:flex">
              <Link
                href="/"
                className="text-sm font-medium text-white/70 transition-colors hover:text-white"
              >
                Home
              </Link>
              <Link
                href="/portal"
                className="text-sm font-medium text-white/70 transition-colors hover:text-white"
              >
                Get Started
              </Link>
              <Link
                href="/owner"
                className="text-sm font-medium text-white/70 transition-colors hover:text-white"
              >
                Partner Portal
              </Link>
            </nav>
          </div>
        </header>
        <main className="flex-1">{children}</main>
        <footer className="border-t border-white/10 bg-[#0a1628] py-8">
          <div className="mx-auto max-w-7xl px-4 sm:px-6">
            <div className="flex flex-col items-center justify-between gap-4 sm:flex-row">
              <Link
                href="/"
                className="flex items-center gap-2 text-sm font-bold text-white"
              >
                <PhoneIcon className="h-4 w-4 text-[#2563eb]" />
                <span>1st <span className="text-[#2563eb]">4</span> Mobile</span>
              </Link>
              <p className="text-xs text-white/50">
                &copy; {new Date().getFullYear()} 1st 4 Mobile. All rights reserved.
              </p>
            </div>
          </div>
        </footer>
      </body>
    </html>
  );
}
