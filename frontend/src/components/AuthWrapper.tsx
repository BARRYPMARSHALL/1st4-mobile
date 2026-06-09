"use client";

import { type ReactNode } from "react";
import { AuthProvider } from "@/contexts/AuthContext";
import NavBar from "@/components/NavBar";

export default function AuthWrapper({ children }: { children: ReactNode }) {
  return (
    <AuthProvider>
      <NavBar />
      <main className="flex-1">{children}</main>
    </AuthProvider>
  );
}
