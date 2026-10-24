import type { AudioItem, VoiceModel } from "./types";

function errorMessage(body: { detail?: unknown }) {
  if (typeof body.detail === "string") return body.detail;
  if (Array.isArray(body.detail))
    return body.detail
      .map((item) => `${item.loc?.slice(1).join(".")}: ${item.msg}`)
      .join(" · ");
  return "Die Anfrage konnte nicht verarbeitet werden.";
}

export async function api<T>(path: string, options?: RequestInit): Promise<T> {
  const response = await fetch(`/api${path}`, options);
  if (!response.ok) {
    let message = `Anfrage fehlgeschlagen (${response.status})`;
    try {
      message = errorMessage(await response.json());
    } catch {
      /* Preserve HTTP status for non-JSON errors. */
    }
    throw new Error(message);
  }
  return response.json();
}

export function send<T>(path: string, body?: unknown, method = "POST") {
  return api<T>(path, {
    method,
    headers: { "Content-Type": "application/json" },
    body: body === undefined ? undefined : JSON.stringify(body),
  });
}

export function upload<T>(
  path: string,
  file: File,
  progress: (value: number) => void,
): Promise<T> {
  return new Promise((resolve, reject) => {
    const form = new FormData();
    form.append("file", file);
    const request = new XMLHttpRequest();
    request.open("POST", `/api${path}`);
    request.upload.onprogress = (event) => {
      if (event.lengthComputable)
        progress(Math.round((event.loaded / event.total) * 100));
    };
    request.onerror = () =>
      reject(new Error("Verbindung unterbrochen. Bitte erneut versuchen."));
    request.onload = () => {
      try {
        const body = JSON.parse(request.responseText);
        if (request.status >= 400) reject(new Error(errorMessage(body)));
        else resolve(body);
      } catch {
        reject(new Error("Ungültige Serverantwort."));
      }
    };
    request.send(form);
  });
}

export const uploadAudio = (file: File, progress: (value: number) => void) =>
  upload<AudioItem>("/audio", file, progress);
export const uploadModel = (file: File, progress: (value: number) => void) =>
  upload<VoiceModel>("/models", file, progress);

export function duration(seconds: number) {
  const rounded = Math.floor(seconds);
  return rounded >= 3600
    ? `${Math.floor(rounded / 3600)}:${String(Math.floor(rounded / 60) % 60).padStart(2, "0")}:${String(rounded % 60).padStart(2, "0")}`
    : `${Math.floor(rounded / 60)}:${String(rounded % 60).padStart(2, "0")}`;
}

export function size(bytes: number) {
  return bytes > 1024 ** 3
    ? `${(bytes / 1024 ** 3).toFixed(1)} GB`
    : `${(bytes / 1024 ** 2).toFixed(1)} MB`;
}

export const message = (error: unknown) =>
  error instanceof Error
    ? error.message
    : "Ein unerwarteter Fehler ist aufgetreten.";
