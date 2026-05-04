import { useEffect, useRef, useState } from "react";
import { Link, useLocation, useParams } from "react-router-dom";

import { api } from "../api";
import type { StudentMatch } from "../types";

/**
 * Top students ranked for a given mission — live.
 *
 * Three data paths (mirrors the student Matches page):
 *   1. `location.state.bootstrap` — inline candidates from POST /offers
 *   2. REST GET /offers/:id/matches — source of truth on refresh
 *   3. SSE GET /offers/:id/stream — live push when a student signs up and
 *      matches this offer, or when a student accepts. Uber-grade: the HR
 *      contact sees candidates appear in real-time.
 */
export default function CompanyMatches() {
  const { offerId: rawId } = useParams();
  const location = useLocation() as {
    state?: { bootstrap?: StudentMatch[]; enriched?: string[] };
  };
  const offerId = rawId ?? localStorage.getItem("studentflow.offer_id") ?? "";
  const bootstrap = location.state?.bootstrap ?? null;
  const enriched = location.state?.enriched ?? null;

  const [matches, setMatches] = useState<StudentMatch[] | null>(bootstrap);
  const [loading, setLoading] = useState(bootstrap === null);
  const [error, setError] = useState<string | null>(null);
  const [livePing, setLivePing] = useState(0);
  const esRef = useRef<EventSource | null>(null);

  function load() {
    if (!offerId) return;
    api
      .listMatchesForOffer(offerId)
      .then((data) => {
        setMatches(data);
        setError(null);
      })
      .catch((err: unknown) =>
        setError(err instanceof Error ? err.message : String(err)),
      )
      .finally(() => setLoading(false));
  }

  useEffect(() => {
    if (!offerId) {
      setError("Aucune mission. Publie-en une d'abord.");
      setLoading(false);
      return;
    }
    load();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [offerId]);

  // SSE subscription for live candidate events.
  useEffect(() => {
    if (!offerId) return;
    const es = api.streamForOffer(offerId);
    esRef.current = es;
    es.onmessage = (evt) => {
      try {
        const ev = JSON.parse(evt.data);
        if (ev.type === "candidate" || ev.type === "candidate_accepted") {
          setLivePing((n) => n + 1);
          load();
        }
      } catch {
        /* ignore keep-alives */
      }
    };
    return () => {
      es.close();
      esRef.current = null;
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [offerId]);

  if (loading && matches === null) return <div className="loading">Chargement des candidats…</div>;

  if (error)
    return (
      <div>
        <div className="alert error">{error}</div>
        <Link to="/company">
          <button>Publier une mission</button>
        </Link>
      </div>
    );

  return (
    <div>
      <h2>Candidats pour ta mission</h2>
      <div className="robot-strip" title="Flux candidats temps réel">
        <span className="robot-dot" />
        Flux temps réel · {livePing > 0 ? `${livePing} nouveau(x) candidat(s) pendant ta session` : "en attente de nouveaux candidats"}
      </div>
      <p style={{ color: "var(--fg-muted)" }}>
        Top étudiants scorés par StudentFlow. Quand un nouvel étudiant matche
        ta mission, il apparaît ici en direct.
      </p>
      {enriched && enriched.length > 0 && (
        <div className="card" style={{ background: "rgba(66,153,225,0.08)", borderColor: "var(--accent)" }}>
          <strong>Compétences détectées automatiquement dans ton annonce :</strong>
          <div className="reasons" style={{ marginTop: "0.5rem" }}>
            {enriched.map((s) => (
              <span key={s} style={{ borderColor: "var(--accent)", color: "var(--accent)" }}>
                {s}
              </span>
            ))}
          </div>
        </div>
      )}
      {matches && matches.length === 0 ? (
        <div className="empty">
          Aucun candidat pour l'instant. Les étudiants qui matcheront ta mission
          apparaîtront ici automatiquement — garde la page ouverte.
        </div>
      ) : (
        matches?.map((m) => (
          <div key={m.student_id} className="card match">
            <div>
              <h3>{m.full_name || "Étudiant"}</h3>
              <div className="meta">
                <a href={`mailto:${m.email}`}>{m.email}</a>
                {m.city ? ` · ${m.city}` : ""}
                {typeof m.distance_km === "number" && <> · {Math.round(m.distance_km)} km</>}
              </div>
            </div>
            <span className="score">{Math.round(m.score * 100)}%</span>
            <div className="reasons">
              {m.reasons.map((r, i) => (
                <span key={i}>{r}</span>
              ))}
              {m.skills.slice(0, 6).map((s, i) => (
                <span key={`sk-${i}`} style={{ borderColor: "var(--accent)", color: "var(--accent)" }}>
                  {s}
                </span>
              ))}
            </div>
          </div>
        ))
      )}
    </div>
  );
}
