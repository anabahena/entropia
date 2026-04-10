import type { WindowRecord } from "@/types/window";

type Props = {
  window: WindowRecord;
  apiBaseUrl: string;
};

function imageUrl(path: string, base: string): string {
  const b = base.replace(/\/$/, "");
  const p = path.replace(/^\//, "");
  return `${b}/${p}`;
}

function shortenHex(s: string, n = 10): string {
  if (s.length <= n * 2) return s;
  return `${s.slice(0, n)}…`;
}

export function WindowCard({ window: w, apiBaseUrl }: Props) {
  const src = imageUrl(w.image_path, apiBaseUrl);
  const created = new Date(w.created_at).toLocaleString();

  return (
    <article className="flex flex-col overflow-hidden rounded-xl border border-zinc-200 bg-white shadow-sm dark:border-zinc-800 dark:bg-zinc-950">
      <div className="relative h-56 w-full overflow-hidden bg-zinc-100 dark:bg-zinc-900">
        <img
          src={src}
          alt={`Ventana ${w.id}`}
          className="h-full w-full object-cover object-center"
          loading="lazy"
        />
      </div>
      <div className="flex flex-col gap-1 p-4 text-sm">
        <h2 className="font-semibold text-zinc-900 dark:text-zinc-100">
          Ventana #{w.id}
        </h2>
        <p className="text-zinc-500 dark:text-zinc-400">{created}</p>
        <dl className="mt-2 space-y-1 font-mono text-xs text-zinc-600 dark:text-zinc-400">
          <div>
            <dt className="inline text-zinc-500">SHA-256 </dt>
            <dd className="inline break-all">{shortenHex(w.sha256, 12)}</dd>
          </div>
          <div>
            <dt className="inline text-zinc-500">dHash </dt>
            <dd className="inline break-all">
              {shortenHex(w.perceptual_hash, 8)}
            </dd>
          </div>
        </dl>
        {w.description && (
          <p className="mt-2 line-clamp-3 text-zinc-700 dark:text-zinc-300">
            {w.description}
          </p>
        )}
      </div>
    </article>
  );
}
