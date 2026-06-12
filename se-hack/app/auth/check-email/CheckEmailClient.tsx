"use client";

import Link from "next/link";
import { FormEvent, useState } from "react";

import { authErrorMessage } from "@/lib/auth-client";

export function CheckEmailClient({ initialEmail }: { initialEmail?: string }) {
  const [email, setEmail] = useState(initialEmail ?? "");
  const [message, setMessage] = useState("");
  const [error, setError] = useState("");
  const [submitting, setSubmitting] = useState(false);

  async function resend(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setSubmitting(true);
    setMessage("");
    setError("");
    try {
      const response = await fetch("/api/auth/resend", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ email }),
      });
      const payload = await response.json();
      if (!response.ok) {
        setError(authErrorMessage(payload, "Unable to resend the email"));
        return;
      }
      setMessage("A new verification email is on its way.");
    } catch {
      setError("Unable to reach the authentication service");
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <>
      <form onSubmit={resend} className="space-y-4">
        <label className="block text-sm font-medium text-[var(--text-primary)]">
          Email
          <input
            type="email"
            required
            value={email}
            onChange={(event) => setEmail(event.target.value)}
            className="mt-2 w-full border border-[var(--border-default)] bg-white px-4 py-3 text-sm outline-none focus:border-[var(--accent-primary)]"
          />
        </label>
        {message ? <p className="text-sm text-emerald-700">{message}</p> : null}
        {error ? <p className="text-sm text-red-600">{error}</p> : null}
        <button
          type="submit"
          disabled={submitting}
          className="w-full border border-[var(--border-default)] px-4 py-3 text-sm font-semibold text-[var(--text-primary)] transition hover:bg-[var(--surface-secondary)] disabled:opacity-60"
        >
          {submitting ? "Sending..." : "Resend verification email"}
        </button>
      </form>
      <Link href="/login" className="mt-6 block text-center font-semibold text-[var(--accent-primary)]">
        Back to sign in
      </Link>
    </>
  );
}
