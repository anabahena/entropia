"use client";

import { useActionState } from "react";
import { useFormStatus } from "react-dom";

import {
  uploadWindow,
  type UploadState,
} from "@/app/actions/upload-window";

const initialState: UploadState = { status: "idle" };

function SubmitButton() {
  const { pending } = useFormStatus();
  return (
    <button
      type="submit"
      disabled={pending}
      className="rounded-lg bg-zinc-900 px-4 py-2 text-sm font-medium text-white hover:bg-zinc-800 disabled:opacity-50 dark:bg-zinc-100 dark:text-zinc-900 dark:hover:bg-white"
    >
      {pending ? "Subiendo…" : "Subir"}
    </button>
  );
}

export function WindowUploadForm() {
  const [state, formAction] = useActionState(uploadWindow, initialState);

  return (
    <form action={formAction} className="flex max-w-md flex-col gap-4">
      <div className="flex flex-col gap-2">
        <label htmlFor="image" className="text-sm font-medium text-zinc-700 dark:text-zinc-300">
          Imagen de ventana
        </label>
        <input
          id="image"
          name="image"
          type="file"
          accept="image/jpeg,image/png,image/webp,image/gif"
          required
          className="text-sm file:mr-3 file:rounded-md file:border-0 file:bg-zinc-200 file:px-3 file:py-1.5 file:text-sm dark:file:bg-zinc-700"
        />
      </div>
      <SubmitButton />
      {state.status === "error" && (
        <p className="text-sm text-red-600 dark:text-red-400" role="alert">
          {state.message}
        </p>
      )}
      {state.status === "success" && (
        <p className="text-sm text-emerald-700 dark:text-emerald-400" role="status">
          Ventana guardada #{state.data.id} · SHA-256{" "}
          <code className="rounded bg-zinc-100 px-1 dark:bg-zinc-800">
            {state.data.sha256.slice(0, 12)}…
          </code>
        </p>
      )}
    </form>
  );
}
