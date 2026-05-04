import { useState } from "react";

import { api } from "../api";
import type { Match } from "../types";

interface Props {
  match: Match;
  onAccepted?: () => void;
  onDeclined?: () => void;
}

/**
 * Student-facing match card with Accept / Pass one-click actions.
 *
 * Both buttons hit the same signed-token URLs the email uses
 * (`${api.base}/m/:token/:action`), so the UX is identical whether the
 * student clicks from their inbox or from the web dashboard. No token is
 * exposed in the client: the API returned `match_id`, we just call
 * /accept and /decline via an authenticated fetch against the state-change
 * endpoints.
 *
 * We hit the accept/decline HTML routes directly because they're idempotent
 * and the SSE stream will deliver the state change back to any other open
 * tab. Keeps the UI optimistic + in sync across devices.
 */
export default function MatchCard({ match, onAccepted, onDeclined }: Props) {
  const pct = Math.round(match.score * 100);
  const [state, setState] = useState(match.state ?? "pending");
  const [busy, setBusy] = useState<"accept" | "decline" | null>(null);
  const [error, setError] = useState<string | null>(null);

  async function act(action: "accept" | "decline") {
    if (!match.match_id) return;
    setBusy(action);
    setError(null);
    try {
      const resp = await fetch(`${api.base}/m/${match.match_id}/${action}`, {
        redirect: "manual",
      });
      // The routes return HTML even on success; we only care that it wasn't 5xx.
      if (!resp.ok && resp.type !== "opaqueredirect" && resp.status >= 400) {
        throw new Error(`${resp.status} ${resp.statusText}`);
      }
      if (action === "accept") {
        setState("accepted");
        onAccepted?.();
      } else {
        setState("declined");
        onDeclined?.();
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : String(err));
    } finally {
      setBusy(null);
    }
  }

  return (
    <div className="card match-card">
      <div className="match">
        <div>
          <h3>{match.title || "(sans titre)"}</h3>
          <div className="meta">
            {match.company || "—"} · {match.city || "lieu non précisé"}
            {typeof match.distance_km === "number" && (
              <> · {Math.round(match.distance_km)} km</>
            )}
          </div>
        </div>
        <span className="score">{pct}%</span>
        {match.reasons.length > 0 && (
          <div className="reasons">
            {match.reasons.map((r, i) => (
              <span key={i}>{r}</span>
            ))}
          </div>
        )}
      </div>
      {state === "accepted" ? (
        <div className="match-status ok">✓ Accepté — l'entreprise est prévenue</div>
      ) : state === "declined" ? (
        <div className="match-status">Passé</div>
      ) : match.match_id ? (
        <div className="match-actions">
          <button
            type="button"
            className="accept"
            onClick={() => act("accept")}
            disabled={busy !== null}
          >
            {busy === "accept" ? "…" : "✓ J'accepte"}
          </button>
          <button
            type="button"
            className="decline"
            onClick={() => act("decline")}
            disabled={busy !== null}
          >
            {busy === "decline" ? "…" : "Passer"}
          </button>
          {match.url && (
            <a href={match.url} target="_blank" rel="noopener noreferrer" className="match-link">
              Voir l'offre ↗
            </a>
          )}
          <ShareButton match={match} />
        </div>
      ) : null}
      {error && <div className="alert error" style={{ marginTop: "0.5rem" }}>{error}</div>}
    </div>
  );
}

/**
 * WhatsApp share — the #1 way French students circulate job tips.
 *
 * Builds a `wa.me` deep link with pre-filled text. On desktop falls back to
 * Web Share API when available (mobile Chrome, Safari iOS). Zero dependency.
 */
function ShareButton({ match }: { match: Match }) {
  const message = `🎯 ${match.title} chez ${match.company} (${Math.round(
    match.score * 100,
  )}% match via StudentFlow)${match.url ? `\n${match.url}` : ""}`;

  function share() {
    if (typeof navigator !== "undefined" && "share" in navigator) {
      void (navigator as Navigator & {
        share: (data: ShareData) => Promise<void>;
      }).share({
        title: match.title,
        text: message,
        url: match.url || undefined,
      });
      return;
    }
    const url = `https://wa.me/?text=${encodeURIComponent(message)}`;
    window.open(url, "_blank", "noopener,noreferrer");
  }

  return (
    <button type="button" className="share-btn" onClick={share} title="Partager à un pote">
      Partager ↗
    </button>
  );
}
