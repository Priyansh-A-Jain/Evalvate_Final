import type { NextResponse } from "next/server";

const ACCESS_TOKEN_MAX_AGE = 15 * 60;
const REFRESH_TOKEN_MAX_AGE = 7 * 24 * 60 * 60;

function cookieSecure(): boolean {
  const configured = process.env.AUTH_COOKIE_SECURE;
  if (configured !== undefined) {
    return configured.toLowerCase() === "true";
  }
  return process.env.NODE_ENV === "production";
}

const baseCookieOptions = {
  httpOnly: true,
  secure: cookieSecure(),
  sameSite: "lax" as const,
  path: "/",
};

export function setSessionCookies(
  response: NextResponse,
  tokens: { access_token: string; refresh_token: string },
) {
  response.cookies.set("access_token", tokens.access_token, {
    ...baseCookieOptions,
    maxAge: ACCESS_TOKEN_MAX_AGE,
  });
  response.cookies.set("refresh_token", tokens.refresh_token, {
    ...baseCookieOptions,
    maxAge: REFRESH_TOKEN_MAX_AGE,
  });
  response.cookies.set("email_verified", "true", {
    ...baseCookieOptions,
    maxAge: REFRESH_TOKEN_MAX_AGE,
  });
}

export function setAccessCookie(response: NextResponse, accessToken: string) {
  response.cookies.set("access_token", accessToken, {
    ...baseCookieOptions,
    maxAge: ACCESS_TOKEN_MAX_AGE,
  });
}

export function clearSessionCookies(response: NextResponse) {
  response.cookies.set("access_token", "", { ...baseCookieOptions, maxAge: 0 });
  response.cookies.set("refresh_token", "", { ...baseCookieOptions, maxAge: 0 });
  response.cookies.set("email_verified", "", { ...baseCookieOptions, maxAge: 0 });
}
