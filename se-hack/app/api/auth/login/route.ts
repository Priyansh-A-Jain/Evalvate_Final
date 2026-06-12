import { NextResponse } from "next/server";

import { authBackendUrl, publicAuthPayload, readBackendResponse } from "@/lib/auth-api";
import { setSessionCookies } from "@/lib/session";

export async function POST(request: Request) {
  const response = await fetch(`${authBackendUrl}/auth/login`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(await request.json()),
    cache: "no-store",
  });
  const payload = (await readBackendResponse(response)) as Record<string, unknown>;
  const nextResponse = NextResponse.json(
    response.ok ? publicAuthPayload(payload) : payload,
    { status: response.status },
  );
  if (response.ok) {
    setSessionCookies(nextResponse, payload as { access_token: string; refresh_token: string });
  }
  return nextResponse;
}
