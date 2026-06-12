import axios from "axios";

import { config } from "@/lib/config";

export const backendBaseUrl = config.backendUrl;

export const backendWebSocketBaseUrl = config.wsUrl;

export const backendClient = axios.create({
  baseURL: backendBaseUrl,
  withCredentials: true,
});
