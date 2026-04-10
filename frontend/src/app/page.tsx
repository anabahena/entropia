import Link from "next/link";

import { WindowUploadForm } from "@/components/WindowUploadForm";

export default function HomePage() {
  return (
    <div className="mx-auto flex min-h-screen max-w-2xl flex-col gap-10 px-6 py-16">
      <header className="space-y-2">
        <p className="text-sm font-medium uppercase tracking-wide text-zinc-500">
          Entropia
        </p>
        <h1 className="text-3xl font-semibold tracking-tight text-zinc-900 dark:text-zinc-50">
          Sube una imagen de ventana
        </h1>
        <p className="text-zinc-600 dark:text-zinc-400">
          Las imágenes se guardan en la API y se identifican con un hash perceptual.
        </p>
        <nav className="pt-2">
          <Link
            href="/feed"
            className="text-sm font-medium text-emerald-700 underline-offset-4 hover:underline dark:text-emerald-400"
          >
            Ver feed →
          </Link>
        </nav>
      </header>
      <WindowUploadForm />
    </div>
  );
}
