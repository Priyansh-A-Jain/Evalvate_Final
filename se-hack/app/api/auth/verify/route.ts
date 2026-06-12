import { NextRequest, NextResponse } from "next/server";

import { authBackendUrl, publicAuthPayload, readBackendResponse } from "@/lib/auth-api";
import { setSessionCookies } from "@/lib/session";

export async function GET(request: NextRequest) {
  const token = request.nextUrl.searchParams.get("token");
  if (!token) {
    return NextResponse.json({ detail: "Missing verification token" }, { status: 400 });
  }

  const response = await fetch(
    `${authBackendUrl}/auth/verify-email?token=${encodeURIComponent(token)}`,
    { cache: "no-store" },
  );
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
