import { NextRequest, NextResponse } from "next/server";

import { authBackendUrl } from "@/lib/auth-api";

export function GET(request: NextRequest) {
  const requested = request.nextUrl.searchParams.get("redirect");
  const redirect = requested?.startsWith("/") && !requested.startsWith("//")
    ? requested
    : "/dashboard";
  return NextResponse.redirect(
    `${authBackendUrl}/demo/login?redirect=${encodeURIComponent(redirect)}`,
  );
}
