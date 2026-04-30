const PROFILE_GRADIENTS = {
  epicurien: "linear-gradient(135deg, #be185d, #831843)",
  artisan: "linear-gradient(135deg, #c2410c, #7c2d12)",
  pragmatique: "linear-gradient(135deg, #15803d, #052e16)",
};

const PROFILE_LABELS = {
  epicurien: "Épicurien",
  artisan: "Artisan",
  pragmatique: "Pragmatique",
};

export default function RecipeCard({ recipe, onOpen }) {
  return (
    <article className="recipe-card" onClick={onOpen} onKeyDown={(e) => (e.key === "Enter" || e.key === " ") && onOpen()} tabIndex={0} role="button" aria-label={`Voir la recette ${recipe.title}`}>
      <div
        className="recipe-thumb"
        style={{ background: PROFILE_GRADIENTS[recipe.profile] || "linear-gradient(135deg, #ea580c, #7c2d12)" }}
      >
        <span className={`recipe-profile-badge ${recipe.profile}`}>{PROFILE_LABELS[recipe.profile]}</span>
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
