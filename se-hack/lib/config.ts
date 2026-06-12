const backendUrl =
  process.env.NEXT_PUBLIC_BACKEND_URL ?? process.env.BACKEND_URL ?? "http://localhost:8000";

const derivedWsUrl = backendUrl.startsWith("https://")
  ? backendUrl.replace("https://", "wss://")
  : backendUrl.replace("http://", "ws://");

export const config = {
  backendUrl,
  wsUrl: process.env.NEXT_PUBLIC_WS_URL ?? derivedWsUrl,
  appUrl: process.env.NEXT_PUBLIC_APP_URL ?? "http://localhost:3000",
  appName: process.env.NEXT_PUBLIC_APP_NAME ?? "Evalvate",
} as const;
