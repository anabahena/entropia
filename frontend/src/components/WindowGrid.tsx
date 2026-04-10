import type { WindowRecord } from "@/types/window";

import { WindowCard } from "./WindowCard";

type Props = {
  windows: WindowRecord[];
  apiBaseUrl: string;
};

export function WindowGrid({ windows, apiBaseUrl }: Props) {
  if (windows.length === 0) {
    return (
      <p className="rounded-lg border border-dashed border-zinc-300 p-8 text-center text-zinc-500 dark:border-zinc-700">
        Todavía no hay ventanas. Sube una desde la página principal.
      </p>
    );
  }

  return (
    <ul className="grid gap-6 sm:grid-cols-2 lg:grid-cols-3">
      {windows.map((w) => (
        <li key={w.id}>
          <WindowCard window={w} apiBaseUrl={apiBaseUrl} />
        </li>
      ))}
    </ul>
  );
}
