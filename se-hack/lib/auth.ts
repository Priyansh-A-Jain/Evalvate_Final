import { cookies } from "next/headers";

export type AuthUser = {
  id: string;
  email: string;
  name: string | null;
  picture: string | null;
  auth_providers: string[];
  email_verified: boolean;
  created_at: string;
  last_login: string;
};

const appBaseUrl = process.env.NEXT_PUBLIC_APP_URL ?? "http://localhost:3000";

export async function getCurrentUser(): Promise<AuthUser | null> {
  const cookieStore = await cookies();
  const cookieHeader = cookieStore.toString();

  if (!cookieHeader) {
    return null;
  }

  try {
    const response = await fetch(`${appBaseUrl}/api/auth/me`, {
      headers: {
        Cookie: cookieHeader,
      },
      cache: "no-store",
    });

    if (!response.ok) {
      return null;
    }

    return (await response.json()) as AuthUser;
  } catch {
    return null;
  }
}
