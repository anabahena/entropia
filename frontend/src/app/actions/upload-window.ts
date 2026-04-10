"use server";

import { revalidatePath } from "next/cache";

import { getApiBaseUrl } from "@/lib/api";

export type UploadState =
  | { status: "idle" }
  | { status: "error"; message: string }
  | {
      status: "success";
      data: {
        id: number;
        sha256: string;
        path: string;
        size_bytes: number;
      };
    };

export async function uploadWindow(
  _prev: UploadState,
  formData: FormData,
): Promise<UploadState> {
  const file = formData.get("image");
  if (!file || !(file instanceof File)) {
    return { status: "error", message: "Elige un archivo de imagen." };
  }
  if (file.size === 0) {
    return { status: "error", message: "El archivo está vacío." };
  }

  const outgoing = new FormData();
  outgoing.append("image", file);

  const base = getApiBaseUrl().replace(/\/$/, "");
  let res: Response;
  try {
    res = await fetch(`${base}/api/windows`, {
      method: "POST",
      body: outgoing,
    });
  } catch {
    return {
      status: "error",
      message: "No se pudo conectar con la API. ¿Está corriendo el backend?",
    };
  }

  const text = await res.text();
  if (!res.ok) {
    let message = text || res.statusText;
    try {
      const parsed = JSON.parse(text) as { detail?: unknown };
      if (typeof parsed.detail === "string") {
        message = parsed.detail;
      } else if (Array.isArray(parsed.detail)) {
        message = parsed.detail.map((d) => JSON.stringify(d)).join(", ");
      }
    } catch {
      /* keep message */
    }
    return { status: "error", message };
  }

  const data = JSON.parse(text) as {
    id: number;
    sha256: string;
    path: string;
    size_bytes: number;
  };

  revalidatePath("/feed");

  return { status: "success", data };
}
