"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useEffect, useRef, useState } from "react";

import { authErrorMessage } from "@/lib/auth-client";

export function CallbackClient({ code }: { code?: string }) {
  const router = useRouter();
  const exchanged = useRef(false);
  const [error, setError] = useState(code ? "" : "Missing authorization code");

  useEffect(() => {
    if (!code || exchanged.current) return;
    exchanged.current = true;
    void (async () => {
      try {
        const response = await fetch("/api/auth/exchange", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ code }),
        });
        const payload = await response.json();
        if (!response.ok) {
          setError(authErrorMessage(payload, "Unable to complete Google sign-in"));
          return;
        }
        const redirect =
          typeof payload.redirect === "string" &&
          payload.redirect.startsWith("/") &&
          !payload.redirect.startsWith("//")
            ? payload.redirect
            : "/dashboard";
        router.replace(redirect);
        router.refresh();
      } catch {
        setError("Unable to complete Google sign-in");
      }
    })();
  }, [code, router]);

  if (error) {
    return (
      <div>
        <p className="text-sm text-red-600">{error}</p>
        <Link href="/login" className="mt-5 inline-block font-semibold text-[var(--accent-primary)]">
          Return to sign in
        </Link>
      </div>
    );
  }
  return <p className="text-sm text-[var(--text-secondary)]">Securing your session...</p>;
}
