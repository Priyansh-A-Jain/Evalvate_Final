"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useEffect, useRef, useState } from "react";

import { authErrorMessage } from "@/lib/auth-client";

export function VerifyClient({ token }: { token?: string }) {
  const router = useRouter();
  const started = useRef(false);
  const [error, setError] = useState(token ? "" : "Missing verification token");

  useEffect(() => {
    if (!token || started.current) return;
    started.current = true;
    void (async () => {
      try {
        const response = await fetch(`/api/auth/verify?token=${encodeURIComponent(token)}`);
        const payload = await response.json();
        if (!response.ok) {
          // The token may have already been consumed by an earlier request
          // (duplicate tab, double-click, a prior successful verification in
          // this session). Before showing an error, check if the user is
          // already authenticated — if so, this was just a stale duplicate.
          try {
            const meResponse = await fetch("/api/auth/me", { cache: "no-store" });
            if (meResponse.ok) {
              router.replace("/dashboard");
              router.refresh();
              return;
            }
          } catch {
            // Ignore — fall through to showing the original verification error.
          }
          setError(authErrorMessage(payload, "This verification link is invalid or expired"));
          return;
        }
        router.replace("/dashboard");
        router.refresh();
      } catch {
        setError("Unable to verify your email right now");
      }
    })();
  }, [router, token]);

  if (error) {
    return (
      <div>
        <p className="text-sm text-red-600">{error}</p>
        <Link
          href="/auth/check-email"
          className="mt-5 inline-block font-semibold text-[var(--accent-primary)]"
        >
          Request another email
        </Link>
      </div>
    );
  }
  return <p className="text-sm text-[var(--text-secondary)]">Verifying your email...</p>;
}
