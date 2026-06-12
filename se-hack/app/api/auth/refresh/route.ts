import { NextRequest, NextResponse } from "next/server";

import { authBackendUrl, readBackendResponse } from "@/lib/auth-api";
import { setAccessCookie } from "@/lib/session";

export async function POST(request: NextRequest) {
  const refreshToken = request.cookies.get("refresh_token")?.value;
  if (!refreshToken) {
    return NextResponse.json({ detail: "Missing refresh token" }, { status: 401 });
  }

  const response = await fetch(`${authBackendUrl}/refresh`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ refresh_token: refreshToken }),
    cache: "no-store",
  });
  const payload = (await readBackendResponse(response)) as { access_token?: string };
  const nextResponse = NextResponse.json(
    response.ok ? { message: "Access token refreshed" } : payload,
    { status: response.status },
  );
  if (response.ok && payload.access_token) {
    setAccessCookie(nextResponse, payload.access_token);
  }
  return nextResponse;
}
