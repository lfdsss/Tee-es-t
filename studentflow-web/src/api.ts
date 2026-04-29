import type {
  FunnelStats,
  Match,
  OfferCreate,
  OfferCreateResponse,
  Stats,
  StudentCreate,
  StudentCreateResponse,
  StudentMatch,
} from "./types";

/**
 * Base URL of the StudentFlow API.
 *
 * Configured via the `VITE_API_BASE_URL` build-time env var. Defaults to
 * `/api` so that the Vite dev proxy (see vite.config.ts) forwards requests
 * to http://localhost:8000 during development.
 */
const API_BASE = import.meta.env.VITE_API_BASE_URL ?? "/api";

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const resp = await fetch(`${API_BASE}${path}`, {
    ...init,
    headers: {
      "Content-Type": "application/json",
      ...(init?.headers ?? {}),
    },
  });
  if (!resp.ok) {
    const text = await resp.text();
    throw new Error(`${resp.status} ${resp.statusText}: ${text}`);
  }
  if (resp.status === 204) {
    return undefined as T;
  }
  return (await resp.json()) as T;
}

export const api = {
  base: API_BASE,

  health: () => request<{ status: string; version: string }>("/health"),

  createStudent: (payload: StudentCreate) =>
    request<StudentCreateResponse>("/students", {
      method: "POST",
      body: JSON.stringify(payload),
    }),

  listMatchesForStudent: (studentId: string) =>
    request<Match[]>(`/students/${encodeURIComponent(studentId)}/matches`),

  /**
   * SSE stream of live match events for this student. The returned
   * EventSource should be `.close()`d by the caller on unmount.
   */
  streamForStudent: (studentId: string): EventSource =>
    new EventSource(`${API_BASE}/students/${encodeURIComponent(studentId)}/stream`),

  getStats: () => request<Stats>("/stats"),

  getFunnel: () => request<FunnelStats>("/stats/funnel"),

  getSkillVocabulary: () => request<{ skills: string[] }>("/skills/vocabulary"),

  extractSkills: (text: string) =>
    request<{ skills: string[] }>("/skills/extract", {
      method: "POST",
      body: JSON.stringify({ text }),
    }),

  createOffer: (payload: OfferCreate) =>
    request<OfferCreateResponse>("/offers", {
      method: "POST",
      body: JSON.stringify(payload),
    }),

  listMatchesForOffer: (offerId: string) =>
    request<StudentMatch[]>(`/offers/${encodeURIComponent(offerId)}/matches`),

  streamForOffer: (offerId: string): EventSource =>
    new EventSource(`${API_BASE}/offers/${encodeURIComponent(offerId)}/stream`),
};
