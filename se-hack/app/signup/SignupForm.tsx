"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { FormEvent, useState } from "react";

import { authErrorMessage } from "@/lib/auth-client";

export function SignupForm({ redirectPath }: { redirectPath: string }) {
  const router = useRouter();
  const [form, setForm] = useState({ name: "", email: "", password: "" });
  const [error, setError] = useState("");
  const [submitting, setSubmitting] = useState(false);

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setSubmitting(true);
    setError("");
    try {
      const response = await fetch("/api/auth/register", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(form),
      });
      const payload = await response.json();
      if (!response.ok) {
        setError(authErrorMessage(payload, "Unable to create your account"));
        return;
      }
      router.push(
        `/auth/check-email?email=${encodeURIComponent(form.email)}&redirect=${encodeURIComponent(redirectPath)}`,
      );
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
          Name
          <input
            type="text"
            autoComplete="name"
            value={form.name}
            onChange={(event) => setForm({ ...form, name: event.target.value })}
            className="mt-2 w-full border border-[var(--border-default)] bg-white px-4 py-3 text-sm outline-none focus:border-[var(--accent-primary)]"
          />
        </label>
        <label className="block text-sm font-medium text-[var(--text-primary)]">
          Email
          <input
            type="email"
            autoComplete="email"
            required
            value={form.email}
            onChange={(event) => setForm({ ...form, email: event.target.value })}
            className="mt-2 w-full border border-[var(--border-default)] bg-white px-4 py-3 text-sm outline-none focus:border-[var(--accent-primary)]"
          />
        </label>
        <label className="block text-sm font-medium text-[var(--text-primary)]">
          Password
          <input
            type="password"
            autoComplete="new-password"
            minLength={8}
            required
            value={form.password}
            onChange={(event) => setForm({ ...form, password: event.target.value })}
            className="mt-2 w-full border border-[var(--border-default)] bg-white px-4 py-3 text-sm outline-none focus:border-[var(--accent-primary)]"
          />
          <span className="mt-1 block text-xs font-normal text-[var(--text-tertiary)]">
            Use at least 8 characters.
          </span>
        </label>
        {error ? <p className="text-sm text-red-600">{error}</p> : null}
        <button
          type="submit"
          disabled={submitting}
          className="w-full bg-[var(--foreground)] px-4 py-3 text-sm font-semibold text-[var(--background)] transition hover:opacity-90 disabled:cursor-wait disabled:opacity-60"
        >
          {submitting ? "Creating account..." : "Create account"}
        </button>
      </form>
      <p className="mt-6 text-center text-sm text-[var(--text-secondary)]">
        Already have an account?{" "}
        <Link
          href={`/login?redirect=${encodeURIComponent(redirectPath)}`}
          className="font-semibold text-[var(--accent-primary)]"
        >
          Sign in
        </Link>
      </p>
    </>
  );
}
