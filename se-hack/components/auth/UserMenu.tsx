"use client";

import { LogOut, UserRound } from "lucide-react";
import { useRouter } from "next/navigation";
import { useEffect, useState } from "react";

import type { AuthUser } from "@/lib/auth";

export function UserMenu() {
  const router = useRouter();
  const [user, setUser] = useState<AuthUser | null>(null);
  const [loggingOut, setLoggingOut] = useState(false);

  useEffect(() => {
    let active = true;
    void fetch("/api/auth/me", { cache: "no-store" })
      .then(async (response) => (response.ok ? ((await response.json()) as AuthUser) : null))
      .then((currentUser) => {
        if (active) setUser(currentUser);
      })
      .catch(() => null);
    return () => {
      active = false;
    };
  }, []);

  async function logout() {
    setLoggingOut(true);
    await fetch("/api/auth/logout", { method: "POST" }).catch(() => null);
    router.replace("/login");
    router.refresh();
  }

  return (
    <div className="mt-4 border-t border-[var(--border-subtle)] pt-4">
      <div className="flex items-center gap-3">
        <div className="flex h-9 w-9 shrink-0 items-center justify-center rounded-full bg-[var(--accent-primary)]/10 text-[var(--accent-primary)]">
          <UserRound className="h-4 w-4" />
        </div>
        <div className="min-w-0 flex-1">
          <p className="truncate text-xs font-semibold text-[var(--text-primary)]">
            {user?.name || "Your account"}
          </p>
          <p className="truncate text-[11px] text-[var(--text-tertiary)]">
            {user?.email || "Loading..."}
          </p>
        </div>
        <button
          type="button"
          onClick={logout}
          disabled={loggingOut}
          aria-label="Log out"
          title="Log out"
          className="rounded-lg p-2 text-[var(--text-tertiary)] transition hover:bg-[var(--surface-secondary)] hover:text-[var(--text-primary)] disabled:opacity-50"
        >
          <LogOut className="h-4 w-4" />
        </button>
      </div>
    </div>
  );
}
