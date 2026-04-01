/**
 * API client — single Axios instance for all backend calls.
 * Per guardrails §9: API calls live exclusively here.
 */
import axios from "axios";

export const api = axios.create({
  baseURL: "",
  timeout: 120_000, // 2 min for long AI operations
  // Do NOT set a default Content-Type here.
  // Axios auto-detects: JSON for objects, multipart/form-data for FormData.
});

// Response interceptor for consistent error handling
api.interceptors.response.use(
  (res) => res,
  (err) => {
    const status = err.response?.status;
    const message =
      err.response?.data?.error || err.message || "Something went sideways";
    console.error("[API]", status ? `HTTP ${status}:` : "Network error:", message, err.response?.data || "");
    return Promise.reject(new Error(message));
  }
);
