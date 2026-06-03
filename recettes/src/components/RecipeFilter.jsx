import { PROFILES, OCCASIONS } from "../data/profiles.js";

const DIFFICULTY_LABELS = {
  1: "Facile",
  2: "Intermédiaire",
  3: "Avancé",
};

export default function RecipeFilter({
  search,
  onSearch,
  profile,
  onProfile,
  occasion,
  onOccasion,
  maxDifficulty,
  onMaxDifficulty,
  count,
  total,
}) {
  return (
    <div className="filter-bar" role="region" aria-label="Filtres des recettes">
      <div className="filter-group">
        <span className="filter-label">Profil</span>
        <button
          className={`filter-pill ${!profile ? "active" : ""}`}
          onClick={() => onProfile(null)}
          aria-pressed={!profile}
        >
          Tous
        </button>
        {PROFILES.map((p) => (
          <button
            key={p.id}
            className={`filter-pill ${profile === p.id ? "active" : ""}`}
            onClick={() => onProfile(profile === p.id ? null : p.id)}
            aria-pressed={profile === p.id}
          >
            {p.label}
          </button>
        ))}
      </div>

      <div className="filter-group">
        <span className="filter-label">Occasion</span>
        <button
          className={`filter-pill ${!occasion ? "active" : ""}`}
          onClick={() => onOccasion(null)}
          aria-pressed={!occasion}
        >
          Toutes
        </button>
        {OCCASIONS.map((o) => (
          <button
            key={o.id}
            className={`filter-pill ${occasion === o.id ? "active" : ""}`}
            onClick={() => onOccasion(occasion === o.id ? null : o.id)}
            aria-pressed={occasion === o.id}
          >
            {o.label}
          </button>
        ))}
      </div>

      <div className="filter-group">
        <span className="filter-label">Difficulté max</span>
        {[1, 2, 3].map((d) => (
          <button
            key={d}
            className={`filter-pill ${maxDifficulty === d ? "active" : ""}`}
            onClick={() => onMaxDifficulty(d)}
            aria-pressed={maxDifficulty === d}
            title={DIFFICULTY_LABELS[d]}
          >
            {"●".repeat(d)}
          </button>
        ))}
      </div>

      <input
        className="filter-search"
        type="search"
        placeholder="Rechercher (ex: poulet, weekend, sauce...)"
        value={search}
        onChange={(e) => onSearch(e.target.value)}
        aria-label="Rechercher une recette"
      />

      <span className="filter-count">
        {count} / {total}
      </span>
    </div>
  );
}
