import { cookies } from "next/headers";

export type AuthUser = { /* unchanged */ };

const authBackendUrl =
  process.env.BACKEND_URL ?? process.env.NEXT_PUBLIC_BACKEND_URL ?? "http://localhost:8000";

export async function getCurrentUser(): Promise<AuthUser | null> {
  const cookieStore = await cookies();
  const accessToken = cookieStore.get("access_token")?.value;
  const refreshToken = cookieStore.get("refresh_token")?.value;
  if (!accessToken && !refreshToken) return null;

  try {
    if (accessToken) {
      const res = await fetch(`${authBackendUrl}/me`, {
        headers: { Cookie: `access_token=${accessToken}` },
        cache: "no-store",
      });
      if (res.ok) return (await res.json()) as AuthUser;
    }

    if (refreshToken) {
      const refreshRes = await fetch(`${authBackendUrl}/refresh`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ refresh_token: refreshToken }),
        cache: "no-store",
      });
      if (refreshRes.ok) {
        const { access_token } = (await refreshRes.json()) as { access_token: string };
        const retryRes = await fetch(`${authBackendUrl}/me`, {
          headers: { Cookie: `access_token=${access_token}` },
          cache: "no-store",
        });
        if (retryRes.ok) return (await retryRes.json()) as AuthUser;
      }
    }
    return null;
  } catch {
    return null;
  }
}