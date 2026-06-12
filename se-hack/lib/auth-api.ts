export const authBackendUrl =
  process.env.BACKEND_URL ?? process.env.NEXT_PUBLIC_BACKEND_URL ?? "http://localhost:8000";

export async function readBackendResponse(response: Response) {
  const contentType = response.headers.get("content-type") ?? "";
  if (contentType.includes("application/json")) {
    return response.json();
  }
  return { detail: await response.text() };
}

export function publicAuthPayload(payload: Record<string, unknown>) {
  const publicPayload = { ...payload };
  delete publicPayload.access_token;
  delete publicPayload.refresh_token;
  return publicPayload;
}
