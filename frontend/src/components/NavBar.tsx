"use client";

import { useState } from "react";
import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import { useAuth } from "@/contexts/AuthContext";
import { Button } from "@/components/ui/button";
import { PhoneIcon, MenuIcon, XIcon, LogOutIcon, UserIcon, Loader2Icon } from "lucide-react";

export default function NavBar() {
  const { user, loading, logout } = useAuth();
  const pathname = usePathname();
  const router = useRouter();
  const [mobileOpen, setMobileOpen] = useState(false);

  const handleLogout = () => {
    logout();
    router.push("/");
  };

  const navLinks = [
    { href: "/", label: "Home" },
    { href: "/#how-it-works", label: "How It Works" },
    { href: "/blog", label: "Blog" },
    { href: "/portal", label: "Get Started" },
    { href: "/book", label: "Book a Demo" },
    { href: "/owner", label: "Partner Portal" },
  ];

  return (
    <header className="sticky top-0 z-50 w-full border-b border-white/10 bg-[#0a1628]/95 backdrop-blur supports-[backdrop-filter]:bg-[#0a1628]/80">
      <div className="mx-auto flex h-14 max-w-7xl items-center justify-between px-4 sm:px-6">
        <Link
          href="/"
          className="flex items-center gap-2 text-lg font-bold tracking-tight text-white"
        >
          <PhoneIcon className="h-5 w-5 text-[#2563eb]" />
          <span>1st <span className="text-[#2563eb]">4</span> Mobile</span>
        </Link>

        {/* Desktop nav */}
        <nav className="hidden items-center gap-6 sm:flex">
          {navLinks.map((link) => (
            <Link
              key={link.href}
              href={link.href}
              className={`text-sm font-medium transition-colors ${
                pathname === link.href
                  ? "text-white"
                  : "text-white/70 hover:text-white"
              }`}
            >
              {link.label}
            </Link>
          ))}

          {/* Auth section */}
          {loading ? (
            <Loader2Icon className="h-4 w-4 animate-spin text-white/50" />
          ) : user ? (
            <div className="flex items-center gap-3">
              <span className="flex items-center gap-1.5 text-xs text-white/50">
                <UserIcon className="h-3.5 w-3.5" />
                {user.email}
              </span>
              <Button
                variant="ghost"
                size="sm"
                onClick={handleLogout}
                className="h-7 text-xs text-white/50 hover:text-white"
              >
                <LogOutIcon className="mr-1 h-3 w-3" />
                Logout
              </Button>
            </div>
          ) : (
            <div className="flex items-center gap-2">
              <Link
                href="/login"
                className="text-sm font-medium text-white/70 transition-colors hover:text-white"
              >
                Sign In
              </Link>
              <Link
                href="/register"
                className="rounded-md bg-[#2563eb] px-3 py-1.5 text-xs font-medium text-white transition-colors hover:bg-[#2563eb]/90"
              >
                Sign Up
              </Link>
            </div>
          )}
        </nav>

        {/* Mobile menu button */}
        <button
          onClick={() => setMobileOpen(!mobileOpen)}
          aria-expanded={mobileOpen}
          className="flex items-center justify-center p-2 text-white/70 hover:text-white sm:hidden"
        >
          {mobileOpen ? <XIcon className="h-5 w-5" /> : <MenuIcon className="h-5 w-5" />}
        </button>
      </div>

      {/* Mobile nav */}
      {mobileOpen && (
        <div className="border-t border-white/10 bg-[#0a1628] px-4 pb-4 pt-2 sm:hidden">
          <nav className="flex flex-col gap-3">
            {navLinks.map((link) => (
              <Link
                key={link.href}
                href={link.href}
                onClick={() => setMobileOpen(false)}
                className={`text-sm font-medium ${
                  pathname === link.href
                    ? "text-white"
                    : "text-white/70 hover:text-white"
                }`}
              >
                {link.label}
              </Link>
            ))}

            {/* Mobile auth */}
            {loading ? (
              <div className="flex items-center gap-2 py-2">
                <Loader2Icon className="h-4 w-4 animate-spin text-white/50" />
                <span className="text-xs text-white/50">Loading...</span>
              </div>
            ) : user ? (
              <div className="border-t border-white/10 pt-3">
                <div className="flex items-center justify-between">
                  <span className="flex items-center gap-1.5 text-xs text-white/50">
                    <UserIcon className="h-3.5 w-3.5" />
                    {user.email}
                  </span>
                  <button
                    onClick={() => { handleLogout(); setMobileOpen(false); }}
                    className="flex items-center gap-1 text-xs text-white/50 hover:text-white"
                  >
                    <LogOutIcon className="h-3 w-3" />
                    Logout
                  </button>
                </div>
              </div>
            ) : (
              <div className="flex items-center gap-2 border-t border-white/10 pt-3">
                <Link
                  href="/login"
                  onClick={() => setMobileOpen(false)}
                  className="text-sm font-medium text-white/70 hover:text-white"
                >
                  Sign In
                </Link>
                <Link
                  href="/register"
                  onClick={() => setMobileOpen(false)}
                  className="rounded-md bg-[#2563eb] px-3 py-1.5 text-xs font-medium text-white"
                >
                  Sign Up
                </Link>
              </div>
            )}
          </nav>
        </div>
      )}
    </header>
  );
}
