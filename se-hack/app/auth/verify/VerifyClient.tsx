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
