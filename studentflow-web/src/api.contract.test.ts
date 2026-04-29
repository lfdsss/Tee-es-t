/**
 * Contract test : vérifie que les fixtures qui *imitent les réponses réelles
 * du backend studentflow* se désérialisent dans les types TypeScript du
 * frontend sans dérive.
 *
 * Si ce test casse, l'API et le frontend ont divergé. Mettre à jour les deux
 * dans le même commit (cf. docs/INTEGRATION.md).
 */

import { afterEach, describe, expect, it, vi } from "vitest";
import { api } from "./api";
import type { FunnelStats, Stats } from "./types";

function mockFetchOnce(payload: unknown, status = 200) {
  vi.stubGlobal(
    "fetch",
    vi.fn(async () =>
      new Response(JSON.stringify(payload), {
        status,
        headers: { "Content-Type": "application/json" },
      }),
    ),
  );
}

afterEach(() => {
  vi.unstubAllGlobals();
});

describe("api contract — réponses backend", () => {
  it("GET /health → { status, version }", async () => {
    mockFetchOnce({ status: "ok", version: "0.1.0" });
    const res = await api.health();
    expect(res.status).toBe("ok");
    expect(res.version).toBe("0.1.0");
  });

  it("GET /stats → Stats", async () => {
    const fixture: Stats = {
      offers: 12,
      students: 5,
      matches: 30,
      matches_unnotified: 4,
      per_source: { manual: 30 },
    };
    mockFetchOnce(fixture);
    const res = await api.getStats();
    expect(res.offers).toBe(12);
    expect(res.matches_unnotified).toBe(4);
    expect(res.per_source.manual).toBe(30);
  });

  it("GET /stats/funnel → FunnelStats imbriqué", async () => {
    const fixture: FunnelStats = {
      offers: 12,
      students: 5,
      matches: { total: 30, pending: 20, accepted: 8, declined: 2 },
      acceptance_rate: 0.8,
      decision_rate: 0.33,
      per_source: { manual: 30 },
    };
    mockFetchOnce(fixture);
    const res = await api.getFunnel();
    expect(res.matches.total).toBe(30);
    expect(res.matches.pending + res.matches.accepted + res.matches.declined).toBe(
      res.matches.total,
    );
    expect(res.acceptance_rate).toBeCloseTo(0.8);
  });

  it("POST /students → StudentCreateResponse avec matches[]", async () => {
    mockFetchOnce({
      id: "stu_123",
      completeness: 0.9,
      matches: [
        {
          offer_id: "off_1",
          match_id: "m_1",
          title: "Stage backend",
          company: "Acme",
          city: "Paris",
          score: 0.87,
          reasons: ["python", "remote_ok"],
          distance_km: 12.4,
          state: "pending",
        },
      ],
    });
    const res = await api.createStudent({
      email: "a@b.c",
      full_name: "A B",
      city: "Paris",
      remote_ok: true,
      skills: ["python"],
      accepted_contracts: ["internship"],
      max_hours_per_week: 35,
    });
    expect(res.id).toBe("stu_123");
    expect(res.matches[0].offer_id).toBe("off_1");
    expect(res.matches[0].state).toBe("pending");
  });

  it("propage les erreurs HTTP avec le corps de la réponse", async () => {
    mockFetchOnce({ detail: "email already used" }, 409);
    await expect(
      api.createStudent({
        email: "dup@b.c",
        full_name: "Dup",
        city: "Paris",
        remote_ok: false,
        skills: [],
        accepted_contracts: ["internship"],
        max_hours_per_week: 20,
      }),
    ).rejects.toThrow(/409/);
  });
});
