import { useEffect, useState } from "react";

import { api } from "../api";
import type { FunnelStats } from "../types";

/**
 * Operator dashboard — funnel metrics.
 *
 * Offers → matches → pending → accepted/declined. The acceptance rate is the
 * key health KPI: <30% = the matcher is too loose, >70% = we're
 * under-indexing candidates. The dashboard refreshes every 15s to double as
 * a live-ops display.
 */
export default function Admin() {
  const [funnel, setFunnel] = useState<FunnelStats | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const tick = () =>
      api
        .getFunnel()
        .then(setFunnel)
        .catch((err) => setError(err instanceof Error ? err.message : String(err)));
    void tick();
    const id = window.setInterval(tick, 15_000);
    return () => window.clearInterval(id);
  }, []);

  if (error) return <div className="alert error">{error}</div>;
  if (!funnel) return <div className="loading">Chargement du funnel…</div>;

  const m = funnel.matches;
  const accRatePct =
    funnel.acceptance_rate !== null ? Math.round(funnel.acceptance_rate * 100) : null;
  const decRatePct =
    funnel.decision_rate !== null ? Math.round(funnel.decision_rate * 100) : null;

  return (
    <div>
      <h2>Dashboard opérateur</h2>
      <div className="robot-strip" title="Rafraîchi toutes les 15s">
        <span className="robot-dot" />
        Live · offers → matches → accepts
      </div>

      <div
        style={{
          display: "grid",
          gridTemplateColumns: "repeat(auto-fit, minmax(160px, 1fr))",
          gap: "1rem",
          marginBottom: "1.5rem",
        }}
      >
        <Metric label="Offres" value={funnel.offers} />
        <Metric label="Étudiants" value={funnel.students} />
        <Metric label="Matches" value={m.total} />
        <Metric label="En attente" value={m.pending} />
        <Metric label="Acceptés" value={m.accepted} tone="ok" />
        <Metric label="Passés" value={m.declined} tone="muted" />
      </div>

      <div className="card">
        <h3 style={{ marginTop: 0 }}>KPIs</h3>
        <div className="match">
          <div>Taux d'acceptation</div>
          <span className="score">{accRatePct === null ? "—" : `${accRatePct}%`}</span>
        </div>
        <div className="match">
          <div>Taux de décision</div>
          <span className="score">{decRatePct === null ? "—" : `${decRatePct}%`}</span>
        </div>
      </div>

      <h3>Offres par source</h3>
      <div className="card">
        {Object.entries(funnel.per_source).length === 0 ? (
          <div className="empty">Aucune offre pour l'instant.</div>
        ) : (
          Object.entries(funnel.per_source)
            .sort((a, b) => b[1] - a[1])
            .map(([source, count]) => (
              <div key={source} className="match">
                <div>
                  <h3>{source}</h3>
                </div>
                <span className="score">{count}</span>
              </div>
            ))
        )}
      </div>
    </div>
  );
}

function Metric({
  label,
  value,
  tone,
}: {
  label: string;
  value: number;
  tone?: "ok" | "muted";
}) {
  const color =
    tone === "ok" ? "var(--ok, #31c48d)" : tone === "muted" ? "var(--fg-muted)" : "inherit";
  return (
    <div className="card" style={{ textAlign: "center", marginBottom: 0 }}>
      <div style={{ color: "var(--fg-muted)", fontSize: "0.85rem" }}>{label}</div>
      <div style={{ fontSize: "1.75rem", fontWeight: 700, marginTop: "0.25rem", color }}>
        {value}
      </div>
    </div>
  );
}
