/**
 * Base URL for the FastAPI backend (server-side and public).
 * Prefer API_URL on the server; NEXT_PUBLIC_API_URL for client-side if needed.
 */
export function getApiBaseUrl(): string {
  return (
    process.env.API_URL ??
    process.env.NEXT_PUBLIC_API_URL ??
    "http://localhost:8000"
  );
}
