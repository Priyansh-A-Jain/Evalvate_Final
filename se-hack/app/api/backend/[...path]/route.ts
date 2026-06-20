import { NextRequest, NextResponse } from "next/server";

const backendBaseUrl =
  process.env.BACKEND_URL ?? process.env.NEXT_PUBLIC_BACKEND_URL ?? "http://localhost:8000";

async function proxy(request: NextRequest, path: string[]) {
  const targetUrl = new URL(`${backendBaseUrl}/${path.join("/")}`);
  targetUrl.search = request.nextUrl.search;

  const headers = new Headers(request.headers);
  headers.delete("host");
  headers.delete("content-length");
  // request.headers already contains the browser's Cookie header for
  // www.evalvate.dev (this route IS www.evalvate.dev) — we just forward it
  // server-to-server, where cross-origin/SameSite rules don't apply.

  const init: RequestInit = { method: request.method, headers, redirect: "manual" };
  if (!["GET", "HEAD"].includes(request.method)) {
    init.body = await request.arrayBuffer();
  }

  const backendResponse = await fetch(targetUrl.toString(), init);

  const responseHeaders = new Headers(backendResponse.headers);
  responseHeaders.delete("content-encoding");
  responseHeaders.delete("transfer-encoding");

  return new NextResponse(backendResponse.body, {
    status: backendResponse.status,
    headers: responseHeaders,
  });
}

type RouteCtx = { params: Promise<{ path: string[] }> };

export async function GET(req: NextRequest, { params }: RouteCtx) {
  return proxy(req, (await params).path);
}
export async function POST(req: NextRequest, { params }: RouteCtx) {
  return proxy(req, (await params).path);
}
export async function PUT(req: NextRequest, { params }: RouteCtx) {
  return proxy(req, (await params).path);
}
export async function DELETE(req: NextRequest, { params }: RouteCtx) {
  return proxy(req, (await params).path);
}