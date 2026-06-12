import { NextRequest, NextResponse } from "next/server";

import { authBackendUrl, readBackendResponse } from "@/lib/auth-api";
import { clearSessionCookies, setAccessCookie } from "@/lib/session";

async function fetchUser(accessToken: string) {
  return fetch(`${authBackendUrl}/me`, {
    headers: { Cookie: `access_token=${accessToken}` },
    cache: "no-store",
  });
}

export async function GET(request: NextRequest) {
  const accessToken = request.cookies.get("access_token")?.value;
  const refreshToken = request.cookies.get("refresh_token")?.value;
  if (!accessToken && !refreshToken) {
    return NextResponse.json({ detail: "Not authenticated" }, { status: 401 });
  }

  let userResponse = accessToken ? await fetchUser(accessToken) : null;
  let refreshedAccessToken: string | null = null;

  if ((!userResponse || userResponse.status === 401) && refreshToken) {
    const refreshResponse = await fetch(`${authBackendUrl}/refresh`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ refresh_token: refreshToken }),
      cache: "no-store",
    });
    if (refreshResponse.ok) {
      const refreshPayload = (await refreshResponse.json()) as { access_token: string };
      refreshedAccessToken = refreshPayload.access_token;
      userResponse = await fetchUser(refreshedAccessToken);
    } else {
      userResponse = refreshResponse;
    }
  }

  if (!userResponse) {
    return NextResponse.json({ detail: "Not authenticated" }, { status: 401 });
  }

  const payload = await readBackendResponse(userResponse);
  const response = NextResponse.json(payload, { status: userResponse.status });
  if (refreshedAccessToken && userResponse.ok) {
    setAccessCookie(response, refreshedAccessToken);
  }
  if (userResponse.status === 401 || userResponse.status === 403) {
    clearSessionCookies(response);
  }
  return response;
}
