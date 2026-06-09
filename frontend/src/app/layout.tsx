import type { Metadata } from "next";
import { Geist, Geist_Mono } from "next/font/google";
import "./globals.css";
import Link from "next/link";
import AuthWrapper from "@/components/AuthWrapper";
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
      <head>
        <script
          dangerouslySetInnerHTML={{
            __html: `
document.addEventListener('click', function(e) {
  var btn = e.target.closest('[data-mobile-menu-btn]');
  if (btn) {
    e.preventDefault();
    var menu = document.getElementById('mobile-menu');
    if (menu) {
      var open = menu.classList.toggle('hidden');
      btn.setAttribute('aria-expanded', !open);
    }
  }
});
            `,
          }}
        />
      </head>
      <body className="min-h-full flex flex-col">
        <AuthWrapper>
          {children}
        </AuthWrapper>

        {/* ─── FOOTER ─── */}
        <footer className="border-t border-white/10 bg-[#0a1628] py-12">
          <div className="mx-auto max-w-7xl px-4 sm:px-6">
            <div className="grid gap-8 sm:grid-cols-2 lg:grid-cols-4">
              {/* Brand */}
              <div>
                <Link
                  href="/"
                  className="flex items-center gap-2 text-sm font-bold text-white"
                >
                  <PhoneIcon className="h-4 w-4 text-[#2563eb]" />
                  <span>1st <span className="text-[#2563eb]">4</span> Mobile</span>
                </Link>
                <p className="mt-3 text-xs leading-relaxed text-white/50 max-w-xs">
                  AI-powered telecom audit platform uncovering hidden overcharges
                  in corporate mobile and fleet data invoices.
                </p>
              </div>

              {/* Platform */}
              <div>
                <h4 className="text-xs font-semibold uppercase tracking-wider text-white/40">
                  Platform
                </h4>
                <ul className="mt-4 space-y-3">
                  <li>
                    <Link href="/" className="text-sm text-white/70 transition-colors hover:text-white">
                      Home
                    </Link>
                  </li>
                  <li>
                    <Link href="/#how-it-works" className="text-sm text-white/70 transition-colors hover:text-white">
                      How It Works
                    </Link>
                  </li>
                  <li>
                    <Link href="/portal" className="text-sm text-white/70 transition-colors hover:text-white">
                      Get Started
                    </Link>
                  </li>
                  <li>
                    <Link href="/blog" className="text-sm text-white/70 transition-colors hover:text-white">
                      Blog
                    </Link>
                  </li>
                  <li>
                    <Link href="/owner" className="text-sm text-white/70 transition-colors hover:text-white">
                      Partner Portal
                    </Link>
                  </li>
                </ul>
              </div>

              {/* Company */}
              <div>
                <h4 className="text-xs font-semibold uppercase tracking-wider text-white/40">
                  Company
                </h4>
                <ul className="mt-4 space-y-3">
                  <li>
                    <Link href="/book" className="text-sm text-white/70 transition-colors hover:text-white">
                      Book a Demo
                    </Link>
                  </li>
                  <li>
                    <Link href="/privacy" className="text-sm text-white/70 transition-colors hover:text-white">
                      Privacy Policy
                    </Link>
                  </li>
                  <li>
                    <Link href="/terms" className="text-sm text-white/70 transition-colors hover:text-white">
                      Terms of Service
                    </Link>
                  </li>
                </ul>
              </div>

              {/* Contact */}
              <div>
                <h4 className="text-xs font-semibold uppercase tracking-wider text-white/40">
                  Contact
                </h4>
                <ul className="mt-4 space-y-3">
                  <li className="text-sm text-white/70">
                    <a href="mailto:hello@1st4.mobi" className="transition-colors hover:text-white">
                      hello@1st4.mobi
                    </a>
                  </li>
                  <li className="text-sm text-white/70">
                    <a href="mailto:privacy@1st4.mobi" className="transition-colors hover:text-white">
                      privacy@1st4.mobi
                    </a>
                  </li>
                  <li className="text-sm text-white/70">
                    <a href="mailto:legal@1st4.mobi" className="transition-colors hover:text-white">
                      legal@1st4.mobi
                    </a>
                  </li>
                  <li className="text-xs text-white/40">
                    Sydney, Australia
                  </li>
                </ul>
              </div>
            </div>

            <div className="mt-10 border-t border-white/10 pt-6 text-center">
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
