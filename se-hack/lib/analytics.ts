import posthog from "posthog-js";

const POSTHOG_KEY = process.env.NEXT_PUBLIC_POSTHOG_KEY ?? "";
const POSTHOG_HOST = process.env.NEXT_PUBLIC_POSTHOG_HOST ?? "https://us.i.posthog.com";

let initialized = false;

export function initAnalytics(): void {
  if (!POSTHOG_KEY || typeof window === "undefined" || initialized) return;
  posthog.init(POSTHOG_KEY, {
    api_host: POSTHOG_HOST,
    capture_pageview: true,
    capture_pageleave: true,
  });
  initialized = true;
}

export function track(event: string, properties?: Record<string, unknown>): void {
  if (!POSTHOG_KEY || typeof window === "undefined") return;
  try {
    posthog.capture(event, properties);
  } catch {
    // Analytics must never break the product.
  }
}
