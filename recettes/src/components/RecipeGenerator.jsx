import { useState } from "react";
import RecipeDetail from "./RecipeDetail.jsx";
import { PROFILES } from "../data/profiles.js";

// Le générateur réordonne les occasions et précise une durée pour Express
// pour cadrer la demande utilisateur (différent du tri du filtre catalogue).
const OCCASIONS = [
  { id: "express", label: "Express (< 20min)" },
  { id: "quotidien", label: "Quotidien" },
  { id: "weekend", label: "Week-end" },
  { id: "reception", label: "Réception" },
];

export default function RecipeGenerator() {
  const [profile, setProfile] = useState("epicurien");
  const [occasion, setOccasion] = useState("quotidien");
  const [servings, setServings] = useState(2);
  const [ingredientInput, setIngredientInput] = useState("");
  const [ingredients, setIngredients] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [recipe, setRecipe] = useState(null);

  const addIngredient = () => {
    const v = ingredientInput.trim();
    if (!v || v.length < 2 || v.length > 60) return;
    if (ingredients.length >= 12) return;
    if (ingredients.includes(v)) return;
    setIngredients([...ingredients, v]);
    setIngredientInput("");
  };

  const removeIngredient = (i) => {
    setIngredients(ingredients.filter((_, idx) => idx !== i));
  };

  const onIngredientKey = (e) => {
    if (e.key === "Enter" || e.key === ",") {
      e.preventDefault();
      addIngredient();
    }
  };

  const canSubmit = ingredients.length >= 1 && !loading;

  const submit = async () => {
    setError(null);
    setRecipe(null);
    setLoading(true);
    try {
      const res = await fetch("/api/recipe-generate", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ profile, occasion, servings, ingredients }),
      });
      const data = await res.json();
      if (!res.ok || !data.ok) {
        throw new Error(data.error || "Erreur de génération");
      }
      setRecipe(data.recipe);
    } catch (err) {
      setError(String(err.message || err));
    } finally {
      setLoading(false);
    }
  };

  return (
    <section className="generator">
      <div className="generator-intro">
        <h2>Créez votre recette personnalisée</h2>
        <p>
          Dites-nous quelle sauce LFDS vous inspire et ce qu'il y a dans votre frigo.
          Notre chef IA imagine une recette unique pour vous.
        </p>
      </div>

      <div className="generator-form">
        <div className="form-group">
          <label className="form-label">Profil de sauce</label>
          <div className="profile-cards">
            {PROFILES.map((p) => (
              <button
                key={p.id}
                type="button"
                className={`profile-card ${profile === p.id ? "active" : ""} ${p.id}`}
                onClick={() => setProfile(p.id)}
                aria-pressed={profile === p.id}
              >
                <strong>{p.label}</strong>
                <span>{p.desc}</span>
              </button>
            ))}
          </div>
        </div>

        <div className="form-row">
          <div className="form-group">
            <label className="form-label" htmlFor="gen-occasion">Occasion</label>
            <select
              id="gen-occasion"
              className="form-select"
              value={occasion}
              onChange={(e) => setOccasion(e.target.value)}
            >
              {OCCASIONS.map((o) => (
                <option key={o.id} value={o.id}>{o.label}</option>
              ))}
            </select>
          </div>

          <div className="form-group">
            <label className="form-label" htmlFor="gen-servings">Portions</label>
            <input
              id="gen-servings"
              className="form-input"
              type="number"
              min="1"
              max="8"
              value={servings}
              onChange={(e) => setServings(Math.max(1, Math.min(8, Number(e.target.value) || 1)))}
            />
          </div>
        </div>

        <div className="form-group">
          <label className="form-label" htmlFor="gen-ingredient">Vos ingrédients (1 à 12)</label>
          <div className="ingredient-input-row">
            <input
              id="gen-ingredient"
              className="form-input"
              type="text"
              placeholder="Ex: poulet, courgettes, riz... (Entrée pour ajouter)"
              value={ingredientInput}
              onChange={(e) => setIngredientInput(e.target.value)}
              onKeyDown={onIngredientKey}
              maxLength={60}
            />
            <button
              type="button"
              className="btn-add-ingredient"
              onClick={addIngredient}
              disabled={!ingredientInput.trim() || ingredients.length >= 12}
            >
              Ajouter
            </button>
          </div>

          {ingredients.length > 0 && (
            <div className="ingredient-tags">
              {ingredients.map((ing, i) => (
                <span key={i} className="ingredient-tag">
                  {ing}
                  <button
                    type="button"
                    onClick={() => removeIngredient(i)}
                    aria-label={`Retirer ${ing}`}
                  >
                    ×
                  </button>
                </span>
              ))}
            </div>
          )}
        </div>

        <button
          type="button"
          className="btn-generate"
          onClick={submit}
          disabled={!canSubmit}
        >
          {loading ? "Le chef réfléchit…" : "Générer ma recette ✨"}
        </button>

        {error && (
          <div className="generator-error" role="alert">
            <strong>Une erreur est survenue.</strong> {error}
          </div>
        )}

        {loading && (
          <div className="generator-loading" aria-live="polite">
            <div className="loading-pulse"></div>
            <p>Notre chef compose une recette unique avec vos ingrédients…</p>
          </div>
        )}
      </div>

      {recipe && (
        <RecipeDetail recipe={recipe} onClose={() => setRecipe(null)} />
      )}
    </section>
  );
}
