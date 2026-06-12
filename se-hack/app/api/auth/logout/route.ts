import { NextResponse } from "next/server";

import { authBackendUrl } from "@/lib/auth-api";
import { clearSessionCookies } from "@/lib/session";

export async function POST() {
  await fetch(`${authBackendUrl}/logout`, { method: "POST", cache: "no-store" }).catch(() => null);
  const response = NextResponse.json({ message: "Logged out" });
  clearSessionCookies(response);
  return response;
}
