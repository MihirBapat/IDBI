// Thin client for the DhanSaarthi backend (Part 3). Base URL is overridable via
// NEXT_PUBLIC_API_BASE; defaults to the local uvicorn dev server.

import type {
  AuditRow,
  ChatResponse,
  ConsentSummary,
  ProjectionScript,
} from "./types";

export const API =
  process.env.NEXT_PUBLIC_API_BASE || "http://localhost:8000";

export class ApiError extends Error {
  status: number;
  constructor(status: number, message: string) {
    super(message);
    this.status = status;
  }
}

async function toJson<T>(res: Response): Promise<T> {
  if (!res.ok) {
    let detail = res.statusText;
    try {
      detail = (await res.json()).detail ?? detail;
    } catch {
      /* non-JSON body */
    }
    throw new ApiError(res.status, detail);
  }
  return res.json() as Promise<T>;
}

const jsonPost = (path: string, body: unknown) =>
  fetch(`${API}${path}`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });

export function grantConsent(persona_id: string): Promise<{ consent: ConsentSummary }> {
  return jsonPost("/consent", { persona_id }).then((r) => toJson(r));
}

export function revokeConsent(persona_id: string): Promise<{ revoked: boolean }> {
  return fetch(`${API}/consent?persona_id=${encodeURIComponent(persona_id)}`, {
    method: "DELETE",
  }).then((r) => toJson(r));
}

export function chat(
  persona_id: string,
  text: string,
  lang = "en",
): Promise<ChatResponse> {
  return jsonPost("/chat", { persona_id, text, lang }).then((r) => toJson(r));
}

export function futureSelf(
  persona_id: string,
  branch: "good" | "bad",
): Promise<ProjectionScript> {
  return fetch(
    `${API}/future-self?persona_id=${encodeURIComponent(persona_id)}&branch=${branch}`,
  ).then((r) => toJson(r));
}

export function emitIntent(
  persona_id: string,
  recommendation_id: string,
  idempotency_key: string,
): Promise<{ deep_link: string; duplicate: boolean }> {
  return jsonPost("/intent", {
    persona_id,
    recommendation_id,
    idempotency_key,
  }).then((r) => toJson(r));
}

export function getAudit(persona_id: string): Promise<{ rows: AuditRow[] }> {
  return fetch(`${API}/audit?persona_id=${encodeURIComponent(persona_id)}`).then(
    (r) => toJson(r),
  );
}
