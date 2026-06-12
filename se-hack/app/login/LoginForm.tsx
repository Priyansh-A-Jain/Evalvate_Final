"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { FormEvent, useState } from "react";

import { authErrorMessage } from "@/lib/auth-client";

export function LoginForm({ redirectPath }: { redirectPath: string }) {
  const router = useRouter();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [submitting, setSubmitting] = useState(false);

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setSubmitting(true);
    setError("");
    try {
      const response = await fetch("/api/auth/login", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ email, password }),
      });
      const payload = await response.json();
      if (!response.ok) {
        if (response.status === 403) {
          router.push(`/auth/check-email?email=${encodeURIComponent(email)}`);
          return;
        }
        setError(authErrorMessage(payload, "Unable to sign in"));
        return;
      }
      router.replace(redirectPath);
      router.refresh();
    } catch {
      setError("Unable to reach the authentication service");
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <>
      <form onSubmit={handleSubmit} className="space-y-4">
        <label className="block text-sm font-medium text-[var(--text-primary)]">
          Email
          <input
            type="email"
            autoComplete="email"
            required
            value={email}
            onChange={(event) => setEmail(event.target.value)}
            className="mt-2 w-full border border-[var(--border-default)] bg-white px-4 py-3 text-sm outline-none transition focus:border-[var(--accent-primary)]"
          />
        </label>
        <label className="block text-sm font-medium text-[var(--text-primary)]">
          Password
          <input
            type="password"
            autoComplete="current-password"
            minLength={8}
            required
            value={password}
            onChange={(event) => setPassword(event.target.value)}
            className="mt-2 w-full border border-[var(--border-default)] bg-white px-4 py-3 text-sm outline-none transition focus:border-[var(--accent-primary)]"
          />
        </label>
        {error ? <p className="text-sm text-red-600">{error}</p> : null}
        <button
          type="submit"
          disabled={submitting}
          className="w-full bg-[var(--foreground)] px-4 py-3 text-sm font-semibold text-[var(--background)] transition hover:opacity-90 disabled:cursor-wait disabled:opacity-60"
        >
          {submitting ? "Signing in..." : "Sign in"}
        </button>
      </form>
      <div className="my-5 flex items-center gap-3 text-xs uppercase tracking-widest text-[var(--text-tertiary)]">
        <span className="h-px flex-1 bg-[var(--border-subtle)]" />
        or
        <span className="h-px flex-1 bg-[var(--border-subtle)]" />
      </div>
      <a
        href={`/api/auth/google?redirect=${encodeURIComponent(redirectPath)}`}
        className="flex w-full items-center justify-center border border-[var(--border-default)] px-4 py-3 text-sm font-semibold text-[var(--text-primary)] transition hover:bg-[var(--surface-secondary)]"
      >
        Continue with Google
      </a>
      <p className="mt-6 text-center text-sm text-[var(--text-secondary)]">
        New to Evalvate?{" "}
        <Link
          href={`/signup?redirect=${encodeURIComponent(redirectPath)}`}
          className="font-semibold text-[var(--accent-primary)]"
        >
          Create an account
        </Link>
      </p>
    </>
  );
}
