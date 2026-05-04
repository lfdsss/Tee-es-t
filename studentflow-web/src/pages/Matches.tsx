import { useEffect, useRef, useState } from "react";
import { useLocation, useParams } from "react-router-dom";

import { api } from "../api";
import MatchCard from "../components/MatchCard";
import type { Match } from "../types";

/**
 * Student match inbox.
 *
 * Three data paths feed this page:
 *   1. `location.state.bootstrap` — the cold-start matches returned inline by
 *      POST /students, so the first render after signup is never empty.
 *   2. REST GET /students/:id/matches — source of truth on refresh / reload.
 *   3. SSE /students/:id/stream — pushes new matches live so the inbox
 *      auto-refreshes without polling. A simple counter tells the student
 *      "un nouveau match vient d'arriver" before we refetch.
 */
export default function Matches() {
  const params = useParams();
  const location = useLocation() as { state?: { bootstrap?: Match[] } };
  const initialId =
    params.studentId ?? localStorage.getItem("studentflow.student_id") ?? "";
  const bootstrap = location.state?.bootstrap ?? null;

  const [studentId, setStudentId] = useState(initialId);
  const [matches, setMatches] = useState<Match[] | null>(bootstrap);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [livePing, setLivePing] = useState(0);
  const esRef = useRef<EventSource | null>(null);

  async function load(id: string) {
    if (!id) return;
    setLoading(true);
    setError(null);
    try {
      const data = await api.listMatchesForStudent(id);
      setMatches(data);
      localStorage.setItem("studentflow.student_id", id);
    } catch (err) {
      setError(err instanceof Error ? err.message : String(err));
      setMatches(null);
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    // If we got bootstrap matches from the signup flow, still fetch fresh
    // ones in the background so the inbox reflects later agent runs.
    if (initialId) void load(initialId);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [initialId]);

  // SSE subscription: close on unmount, open on mount if we have an id.
  useEffect(() => {
    if (!initialId) return;
    const es = api.streamForStudent(initialId);
    esRef.current = es;
    es.onmessage = (evt) => {
      try {
        const ev = JSON.parse(evt.data);
        if (ev.type === "match") {
          setLivePing((n) => n + 1);
          void load(initialId);
        }
      } catch {
        /* ignore keep-alives */
      }
    };
    es.onerror = () => {
      // Browser will retry automatically; nothing to do beyond logging.
    };
    return () => {
      es.close();
      esRef.current = null;
    };
  }, [initialId]);

  return (
    <div>
      <h2>Mes matches</h2>
      <div className="robot-strip" title="Scoring live 24/7">
        <span className="robot-dot" />
        Flux temps réel · {livePing > 0 ? `${livePing} nouveau(x) match(es) pendant ta session` : "en attente de nouveaux matches"}
      </div>
      <div className="card">
        <label>
          ID étudiant
          <input
            type="text"
            value={studentId}
            onChange={(e) => setStudentId(e.target.value)}
            placeholder="collez votre id reçu à l'inscription"
          />
        </label>
        <button onClick={() => load(studentId)} disabled={!studentId || loading}>
          {loading ? "Chargement…" : "Rafraîchir"}
        </button>
      </div>

      {error && <div className="alert error">{error}</div>}
      {loading && !matches && <div className="loading">Chargement des matches…</div>}
      {matches && matches.length === 0 && (
        <div className="empty">
          Aucun match pour l'instant. Les agents tournent en continu —
          la page se mettra à jour toute seule dès qu'une offre matche.
        </div>
      )}
      {matches && matches.length > 0 && (
        <div>
          {matches.map((m, i) => (
            <MatchCard
              key={m.match_id ?? `${m.offer_id}-${i}`}
              match={m}
              onAccepted={() => void load(initialId)}
              onDeclined={() => void load(initialId)}
            />
          ))}
        </div>
      )}
    </div>
  );
}
