import Link from "next/link";

import { WindowGrid } from "@/components/WindowGrid";
import { getApiBaseUrl } from "@/lib/api";
import type { WindowRecord } from "@/types/window";

async function fetchWindows(base: string): Promise<WindowRecord[]> {
  const res = await fetch(`${base.replace(/\/$/, "")}/api/windows`, {
    cache: "no-store",
  });
  if (!res.ok) {
    throw new Error(`Falló la solicitud del feed: ${res.status}`);
  }
  return res.json() as Promise<WindowRecord[]>;
}

export default async function FeedPage() {
  const serverBase = getApiBaseUrl();
  const publicBase =
    process.env.NEXT_PUBLIC_API_URL ??
    (serverBase.includes("entropia-api")
      ? "http://localhost:8000"
      : serverBase);
  let windows: WindowRecord[] = [];
  let error: string | null = null;

  try {
    windows = await fetchWindows(serverBase);
  } catch (e) {
    error = e instanceof Error ? e.message : "Error desconocido";
  }

  return (
    <div className="mx-auto flex min-h-screen max-w-6xl flex-col gap-10 px-6 py-16">
      <header className="flex flex-col gap-2 sm:flex-row sm:items-end sm:justify-between">
        <div>
          <p className="text-sm font-medium uppercase tracking-wide text-zinc-500">
            Entropia
          </p>
          <h1 className="text-3xl font-semibold tracking-tight text-zinc-900 dark:text-zinc-50">
            Feed de ventanas
          </h1>
          <p className="mt-1 text-zinc-600 dark:text-zinc-400">
            Las cargas más recientes primero (desde <code className="text-xs">{publicBase}</code>
            ).
          </p>
        </div>
        <Link
          href="/"
          className="text-sm font-medium text-emerald-700 underline-offset-4 hover:underline dark:text-emerald-400"
        >
          ← Subir
        </Link>
      </header>

      {error ? (
        <div
          className="rounded-lg border border-red-200 bg-red-50 p-4 text-red-800 dark:border-red-900 dark:bg-red-950/40 dark:text-red-200"
          role="alert"
        >
          <p className="font-medium">No se pudieron cargar las ventanas</p>
          <p className="mt-1 text-sm">{error}</p>
        </div>
      ) : (
        <WindowGrid windows={windows} apiBaseUrl={publicBase} />
      )}
    </div>
  );
}
