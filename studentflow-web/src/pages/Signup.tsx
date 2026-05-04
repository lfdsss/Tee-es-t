import { FormEvent, useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";

import { api } from "../api";
import type { ContractType, StudentCreate } from "../types";

const CONTRACT_CHOICES: { value: ContractType; label: string }[] = [
  { value: "internship", label: "Stage" },
  { value: "apprenticeship", label: "Alternance" },
  { value: "cdd", label: "CDD" },
  { value: "cdi", label: "CDI" },
  { value: "part_time", label: "Temps partiel / job étudiant" },
  { value: "freelance", label: "Freelance" },
];

export default function Signup() {
  const nav = useNavigate();
  const [email, setEmail] = useState("");
  const [fullName, setFullName] = useState("");
  const [city, setCity] = useState("");
  const [coords, setCoords] = useState<{ lat: number; lng: number } | null>(null);
  const [remoteOk, setRemoteOk] = useState(true);
  const [skills, setSkills] = useState("");
  const [contracts, setContracts] = useState<ContractType[]>(["internship", "apprenticeship"]);
  const [maxHours, setMaxHours] = useState(35);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [locating, setLocating] = useState(false);
  const [vocabulary, setVocabulary] = useState<string[]>([]);
  const [cvText, setCvText] = useState("");
  const [cvBusy, setCvBusy] = useState(false);

  // Fetch the canonical skill vocabulary once so the <datalist> shows the
  // exact terms the matcher understands. Silent fallback if the API is cold.
  useEffect(() => {
    api
      .getSkillVocabulary()
      .then((r) => setVocabulary(r.skills))
      .catch(() => undefined);
  }, []);

  async function parseCv() {
    if (!cvText.trim()) return;
    setCvBusy(true);
    try {
      const { skills: detected } = await api.extractSkills(cvText);
      if (detected.length === 0) return;
      // Merge with what the student already typed, deduped on lowercase.
      const existing = skills
        .split(",")
        .map((s) => s.trim().toLowerCase())
        .filter(Boolean);
      const merged = Array.from(new Set([...existing, ...detected]));
      setSkills(merged.join(", "));
    } catch {
      /* silent — extraction is a nice-to-have */
    } finally {
      setCvBusy(false);
    }
  }

  function toggleContract(c: ContractType) {
    setContracts((prev) =>
      prev.includes(c) ? prev.filter((x) => x !== c) : [...prev, c],
    );
  }

  /**
   * Browser geolocation → OSM Nominatim reverse geocoding → city name + coords.
   *
   * We store both the human-readable city (for display) and the raw lat/lng
   * (for the Haversine distance scorer server-side). Zero API key required.
   */
  async function detectLocation() {
    if (!("geolocation" in navigator)) {
      setError("La géolocalisation n'est pas disponible dans ce navigateur.");
      return;
    }
    setLocating(true);
    setError(null);
    try {
      const pos = await new Promise<GeolocationPosition>((resolve, reject) => {
        navigator.geolocation.getCurrentPosition(resolve, reject, {
          enableHighAccuracy: false,
          timeout: 10_000,
          maximumAge: 60_000,
        });
      });
      const { latitude, longitude } = pos.coords;
      setCoords({ lat: latitude, lng: longitude });
      const resp = await fetch(
        `https://nominatim.openstreetmap.org/reverse?format=json&lat=${latitude}&lon=${longitude}&zoom=10&addressdetails=1`,
        { headers: { Accept: "application/json" } },
      );
      if (!resp.ok) throw new Error("Nominatim HTTP " + resp.status);
      const data = await resp.json();
      const addr = data.address ?? {};
      const resolved: string =
        addr.city || addr.town || addr.village || addr.municipality || addr.county || "";
      if (resolved) {
        setCity(resolved);
      } else {
        setError("Ville introuvable. Saisis-la à la main.");
      }
    } catch (err) {
      setError(
        err instanceof GeolocationPositionError
          ? "Autorise la localisation dans ton navigateur, ou saisis la ville à la main."
          : err instanceof Error
            ? err.message
            : String(err),
      );
    } finally {
      setLocating(false);
    }
  }

  async function onSubmit(e: FormEvent) {
    e.preventDefault();
    setError(null);
    setSubmitting(true);
    const payload: StudentCreate = {
      email,
      full_name: fullName,
      city,
      remote_ok: remoteOk,
      skills: skills
        .split(",")
        .map((s) => s.trim())
        .filter(Boolean),
      accepted_contracts: contracts,
      max_hours_per_week: maxHours,
      latitude: coords?.lat ?? null,
      longitude: coords?.lng ?? null,
    };
    try {
      const resp = await api.createStudent(payload);
      localStorage.setItem("studentflow.student_id", resp.id);
      // The API already returns the cold-start matches. Hand them to
      // the /matches page via navigation state so they show instantly.
      nav(`/matches/${resp.id}`, { state: { bootstrap: resp.matches } });
    } catch (err) {
      setError(err instanceof Error ? err.message : String(err));
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <div>
      <h2>Créer mon profil</h2>
      <p style={{ color: "var(--fg-muted)", marginTop: 0 }}>
        60 secondes. Dès le clic sur "Créer mon profil", tu vois tes meilleurs matches
        — on ne te fait pas attendre.
      </p>
      {error && <div className="alert error">{error}</div>}
      <form onSubmit={onSubmit} className="card">
        <label>
          Email
          <input
            type="email"
            required
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            placeholder="tonemail@exemple.fr"
          />
        </label>
        <label>
          Nom complet
          <input
            type="text"
            value={fullName}
            onChange={(e) => setFullName(e.target.value)}
            placeholder="Prénom Nom"
          />
        </label>
        <label>
          Ville
          <input
            type="text"
            value={city}
            onChange={(e) => setCity(e.target.value)}
            placeholder="Paris"
          />
          <button
            type="button"
            className="geo-btn"
            onClick={detectLocation}
            disabled={locating}
          >
            {locating ? "Localisation…" : "📍 Utiliser ma position"}
          </button>
          {coords && (
            <span style={{ fontSize: "0.8rem", color: "var(--fg-muted)", marginLeft: "0.5rem" }}>
              ✓ coordonnées captées ({coords.lat.toFixed(2)}, {coords.lng.toFixed(2)})
            </span>
          )}
        </label>
        <label>
          Compétences (séparées par des virgules)
          <input
            type="text"
            value={skills}
            onChange={(e) => setSkills(e.target.value)}
            placeholder="react, javascript, python"
            list="skill-vocabulary"
          />
          <datalist id="skill-vocabulary">
            {vocabulary.map((s) => (
              <option key={s} value={s} />
            ))}
          </datalist>
        </label>
        <label>
          Ou colle ton CV (on détecte tes skills tout seul)
          <textarea
            rows={4}
            value={cvText}
            onChange={(e) => setCvText(e.target.value)}
            placeholder="Colle ici le texte de ton CV ou une description de ton profil…"
          />
          <button
            type="button"
            className="geo-btn"
            onClick={parseCv}
            disabled={cvBusy || !cvText.trim()}
          >
            {cvBusy ? "Analyse…" : "✨ Extraire mes compétences"}
          </button>
        </label>
        <label>
          Heures max / semaine
          <input
            type="number"
            min={1}
            max={40}
            value={maxHours}
            onChange={(e) => setMaxHours(Number(e.target.value))}
          />
        </label>
        <label>
          <input
            type="checkbox"
            checked={remoteOk}
            onChange={(e) => setRemoteOk(e.target.checked)}
            style={{ width: "auto", marginRight: "0.5rem" }}
          />
          J'accepte le télétravail
        </label>
        <fieldset style={{ border: "1px solid var(--border)", borderRadius: "var(--radius)", padding: "1rem", marginBottom: "1rem" }}>
          <legend style={{ color: "var(--fg-muted)", fontSize: "0.9rem" }}>Types de contrat acceptés</legend>
          {CONTRACT_CHOICES.map((c) => (
            <label key={c.value} style={{ flexDirection: "row", alignItems: "center", marginBottom: "0.5rem" }}>
              <input
                type="checkbox"
                checked={contracts.includes(c.value)}
                onChange={() => toggleContract(c.value)}
                style={{ width: "auto", marginRight: "0.5rem" }}
              />
              {c.label}
            </label>
          ))}
        </fieldset>
        <button type="submit" disabled={submitting}>
          {submitting ? "Envoi…" : "Créer mon profil & voir mes matches →"}
        </button>
      </form>
    </div>
  );
}
