import { PROFILE_BY_ID, DEFAULT_GRADIENT } from "../data/profiles.js";

export default function RecipeCard({ recipe, onOpen }) {
  const profile = PROFILE_BY_ID[recipe.profile];
  return (
    <article className="recipe-card" onClick={onOpen} onKeyDown={(e) => (e.key === "Enter" || e.key === " ") && onOpen()} tabIndex={0} role="button" aria-label={`Voir la recette ${recipe.title}`}>
      <div
        className="recipe-thumb"
        style={{ background: profile?.gradient || DEFAULT_GRADIENT }}
      >
        <span className={`recipe-profile-badge ${recipe.profile}`}>{profile?.label}</span>
        <div className="recipe-difficulty" aria-label={`Difficulté ${recipe.difficulty} sur 3`}>
          {[1, 2, 3].map((i) => (
            <span key={i} className={`pip ${i <= recipe.difficulty ? "on" : ""}`}></span>
          ))}
        </div>
        <span className="recipe-thumb-emoji" aria-hidden>{recipe.emoji}</span>
      </div>
      <div className="recipe-body">
        <h3 className="recipe-title">{recipe.title}</h3>
        <p className="recipe-desc">{recipe.description}</p>
        <div className="recipe-meta">
          <span><strong>{recipe.time_min}</strong>min</span>
          <span><strong>{recipe.servings}</strong>pers.</span>
          <span style={{ marginLeft: "auto", textTransform: "capitalize" }}>{recipe.occasion}</span>
        </div>
      </div>
    </article>
  );
}
