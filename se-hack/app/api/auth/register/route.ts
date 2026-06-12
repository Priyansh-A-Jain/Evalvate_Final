import { NextResponse } from "next/server";

import { authBackendUrl, readBackendResponse } from "@/lib/auth-api";

export async function POST(request: Request) {
  const response = await fetch(`${authBackendUrl}/auth/register`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(await request.json()),
    cache: "no-store",
  });
  return NextResponse.json(await readBackendResponse(response), { status: response.status });
}
