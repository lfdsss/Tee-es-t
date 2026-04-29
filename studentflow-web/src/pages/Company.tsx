import { FormEvent, useState } from "react";
import { useNavigate } from "react-router-dom";

import { api } from "../api";
import type { ContractType, OfferCreate } from "../types";

const CONTRACT_CHOICES: { value: ContractType; label: string }[] = [
  { value: "part_time", label: "Temps partiel / job étudiant" },
  { value: "internship", label: "Stage" },
  { value: "apprenticeship", label: "Alternance" },
  { value: "cdd", label: "CDD" },
  { value: "freelance", label: "Freelance" },
  { value: "cdi", label: "CDI" },
];

/**
 * Company-side onboarding: publish a mission.
 *
 * Writes an Offer via `POST /offers`. The offer lands in the same table as
 * scraped offers, so the MatcherAgent picks it up on its next tick and the
 * NotifierAgent emails the best student candidates. From the employer's POV
 * this is "post once, forget, receive candidates".
 */
export default function Company() {
  const nav = useNavigate();
  const [title, setTitle] = useState("");
  const [company, setCompany] = useState("");
  const [contactEmail, setContactEmail] = useState("");
  const [description, setDescription] = useState("");
  const [city, setCity] = useState("");
  const [coords, setCoords] = useState<{ lat: number; lng: number } | null>(null);
  const [locating, setLocating] = useState(false);
  const [remote, setRemote] = useState(false);
  const [contract, setContract] = useState<ContractType>("part_time");
  const [hoursPerWeek, setHoursPerWeek] = useState<number | "">(15);
  const [skills, setSkills] = useState("");
  const [url, setUrl] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function detectLocation() {
    if (!("geolocation" in navigator)) return;
    setLocating(true);
    try {
      const pos = await new Promise<GeolocationPosition>((resolve, reject) => {
        navigator.geolocation.getCurrentPosition(resolve, reject, {
          timeout: 10_000,
          maximumAge: 60_000,
        });
      });
      setCoords({ lat: pos.coords.latitude, lng: pos.coords.longitude });
      const resp = await fetch(
        `https://nominatim.openstreetmap.org/reverse?format=json&lat=${pos.coords.latitude}&lon=${pos.coords.longitude}&zoom=10&addressdetails=1`,
        { headers: { Accept: "application/json" } },
      );
      if (resp.ok) {
        const data = await resp.json();
        const addr = data.address ?? {};
        const resolved: string =
          addr.city || addr.town || addr.village || addr.municipality || addr.county || "";
        if (resolved && !city) setCity(resolved);
      }
    } catch {
      /* silently fallback to manual */
    } finally {
      setLocating(false);
    }
  }

  async function onSubmit(e: FormEvent) {
    e.preventDefault();
    setError(null);
    setSubmitting(true);
    const payload: OfferCreate = {
      title,
      company,
      description,
      city,
      remote,
      contract,
      hours_per_week: hoursPerWeek === "" ? null : Number(hoursPerWeek),
      skills: skills
        .split(",")
        .map((s) => s.trim())
        .filter(Boolean),
      url,
      contact_email: contactEmail,
      latitude: coords?.lat ?? null,
      longitude: coords?.lng ?? null,
    };
    try {
      const resp = await api.createOffer(payload);
      localStorage.setItem("studentflow.offer_id", resp.id);
      // Hand the inline candidates to the next page so the employer sees
      // value on the very first paint — no loading spinner, no "come back later".
      nav(`/company/matches/${resp.id}`, {
        state: { bootstrap: resp.candidates, enriched: resp.enriched_skills },
      });
    } catch (err) {
      setError(err instanceof Error ? err.message : String(err));
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <div>
      <h2>Publier une mission</h2>
      <p style={{ color: "var(--fg-muted)", marginTop: 0 }}>
        Décris ta mission. StudentFlow la score contre tous nos étudiants actifs
        et te sort les meilleurs profils immédiatement.
      </p>
      {error && <div className="alert error">{error}</div>}
      <form onSubmit={onSubmit} className="card">
        <label>
          Titre du poste
          <input
            type="text"
            required
            value={title}
            onChange={(e) => setTitle(e.target.value)}
            placeholder="Community manager · 10h / semaine"
          />
        </label>
        <label>
          Nom de l'entreprise
          <input
            type="text"
            required
            value={company}
            onChange={(e) => setCompany(e.target.value)}
            placeholder="Acme SAS"
          />
        </label>
        <label>
          Email de contact
          <input
            type="email"
            required
            value={contactEmail}
            onChange={(e) => setContactEmail(e.target.value)}
            placeholder="recrutement@acme.fr"
          />
        </label>
        <label>
          Description courte
          <textarea
            rows={4}
            value={description}
            onChange={(e) => setDescription(e.target.value)}
            placeholder="Tes missions, le contexte, les outils, ce que tu cherches…"
          />
        </label>
        <label>
          Ville
          <input
            type="text"
            value={city}
            onChange={(e) => setCity(e.target.value)}
            placeholder="Lyon"
          />
          <button
            type="button"
            className="geo-btn"
            onClick={detectLocation}
            disabled={locating}
          >
            {locating ? "Localisation…" : "📍 Utiliser la position de l'entreprise"}
          </button>
          {coords && (
            <span style={{ fontSize: "0.8rem", color: "var(--fg-muted)", marginLeft: "0.5rem" }}>
              ✓ coordonnées captées — distance calculée vers chaque candidat
            </span>
          )}
        </label>
        <label style={{ flexDirection: "row", alignItems: "center" }}>
          <input
            type="checkbox"
            checked={remote}
            onChange={(e) => setRemote(e.target.checked)}
            style={{ width: "auto", marginRight: "0.5rem" }}
          />
          Télétravail possible
        </label>
        <label>
          Type de contrat
          <select value={contract} onChange={(e) => setContract(e.target.value as ContractType)}>
            {CONTRACT_CHOICES.map((c) => (
              <option key={c.value} value={c.value}>
                {c.label}
              </option>
            ))}
          </select>
        </label>
        <label>
          Heures / semaine
          <input
            type="number"
            min={1}
            max={40}
            value={hoursPerWeek}
            onChange={(e) => setHoursPerWeek(e.target.value === "" ? "" : Number(e.target.value))}
          />
        </label>
        <label>
          Compétences recherchées (séparées par des virgules)
          <input
            type="text"
            value={skills}
            onChange={(e) => setSkills(e.target.value)}
            placeholder="community management, canva, réseaux sociaux"
          />
        </label>
        <label>
          URL de l'annonce (optionnel)
          <input
            type="url"
            value={url}
            onChange={(e) => setUrl(e.target.value)}
            placeholder="https://tonsite.fr/carriere/..."
          />
        </label>
        <button type="submit" disabled={submitting}>
          {submitting ? "Publication…" : "Publier la mission"}
        </button>
      </form>
    </div>
  );
}
