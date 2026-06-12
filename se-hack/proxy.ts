import { NextResponse } from "next/server";
import type { NextRequest } from "next/server";

const protectedRoutes = [
  "/dashboard",
  "/pre-interview",
  "/interview",
  "/results",
  "/group-interview",
  "/resume",
  "/home",
  "/meeting-room",
  "/voice-analysis",
  "/video-demo",
  "/interview-agent",
];

export function proxy(request: NextRequest) {
  const { pathname, search } = request.nextUrl;

  const isProtected = protectedRoutes.some(
    (route) => pathname === route || pathname.startsWith(`${route}/`),
  );
  if (!isProtected) return NextResponse.next();

  const token = request.cookies.get("access_token")?.value;
  if (!token) {
    const loginUrl = new URL("/login", request.url);
    loginUrl.searchParams.set("redirect", `${pathname}${search}`);
    return NextResponse.redirect(loginUrl);
  }

  if (request.cookies.get("email_verified")?.value !== "true") {
    const verifyUrl = new URL("/auth/check-email", request.url);
    verifyUrl.searchParams.set("redirect", `${pathname}${search}`);
    return NextResponse.redirect(verifyUrl);
  }

  return NextResponse.next();
}

export const config = {
  matcher: ["/((?!_next/static|_next/image|favicon.ico).*)"],
};
