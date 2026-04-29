import { useEffect, useState } from "react";

import { api } from "../api";
import type { Stats as StatsT } from "../types";

export default function Stats() {
  const [stats, setStats] = useState<StatsT | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    api
      .getStats()
      .then(setStats)
      .catch((err) => setError(err instanceof Error ? err.message : String(err)));
  }, []);

  if (error) return <div className="alert error">{error}</div>;
  if (!stats) return <div className="loading">Chargement…</div>;

  return (
    <div>
      <h2>Stats plateforme</h2>
      <div className="robot-strip" title="ScraperAgent, MatcherAgent, NotifierAgent">
        <span className="robot-dot" />
        Robot en ligne · scrape toutes les 15 min · 4 sources
      </div>
      <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(180px, 1fr))", gap: "1rem", marginBottom: "1.5rem" }}>
        <Metric label="Offres indexées" value={stats.offers} />
        <Metric label="Étudiants actifs" value={stats.students} />
        <Metric label="Matches créés" value={stats.matches} />
        <Metric label="Non-notifiés" value={stats.matches_unnotified} />
      </div>
      <h3>Offres par source</h3>
      <div className="card">
        {Object.entries(stats.per_source).length === 0 ? (
          <div className="empty">Aucune offre pour l'instant.</div>
        ) : (
          Object.entries(stats.per_source).map(([source, count]) => (
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

function Metric({ label, value }: { label: string; value: number }) {
  return (
    <div className="card" style={{ textAlign: "center", marginBottom: 0 }}>
      <div style={{ color: "var(--fg-muted)", fontSize: "0.85rem" }}>{label}</div>
      <div style={{ fontSize: "1.75rem", fontWeight: 700, marginTop: "0.25rem" }}>
        {value}
      </div>
    </div>
  );
}
