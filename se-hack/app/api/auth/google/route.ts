import { NextRequest, NextResponse } from "next/server";

import { authBackendUrl } from "@/lib/auth-api";

function safeRedirect(value: string | null) {
  return value?.startsWith("/") && !value.startsWith("//") ? value : "/dashboard";
}

export function GET(request: NextRequest) {
  const redirect = safeRedirect(request.nextUrl.searchParams.get("redirect"));
  return NextResponse.redirect(
    `${authBackendUrl}/login?redirect=${encodeURIComponent(redirect)}`,
  );
}
