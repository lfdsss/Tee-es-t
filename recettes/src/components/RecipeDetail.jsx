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

export default function RecipeDetail({ recipe, onClose }) {
  const onOverlayClick = (e) => {
    if (e.target === e.currentTarget) onClose();
  };

  return (
    <div className="detail-overlay" onClick={onOverlayClick} role="dialog" aria-modal="true" aria-labelledby="detail-title">
      <div className="detail-card">
        <div className="detail-thumb" style={{ background: PROFILE_GRADIENTS[recipe.profile] || "linear-gradient(135deg,#ea580c,#7c2d12)" }}>
          <button className="detail-close" onClick={onClose} aria-label="Fermer">
            ×
          </button>
          <span className={`recipe-profile-badge ${recipe.profile}`} style={{ position: "absolute", top: 16, left: 16 }}>
            {PROFILE_LABELS[recipe.profile]}
          </span>
          <span className="recipe-thumb-emoji" aria-hidden style={{ position: "relative", zIndex: 1 }}>
            {recipe.emoji}
          </span>
        </div>

        <div className="detail-body">
          <h2 className="detail-title" id="detail-title">{recipe.title}</h2>
          <p className="detail-desc">{recipe.description}</p>

          <div className="detail-meta">
            <span><strong>⏱</strong> {recipe.time_min} min</span>
            <span><strong>👥</strong> {recipe.servings} personnes</span>
            <span><strong>🎯</strong> {recipe.occasion}</span>
            <span><strong>📊</strong> {"●".repeat(recipe.difficulty) + "○".repeat(3 - recipe.difficulty)} {recipe.difficulty}/3</span>
          </div>

          <div className="detail-section">
            <h3>Ingrédients</h3>
            <ul className="ingredients-list">
              {recipe.ingredients.map((ing, i) => (
                <li key={i}>{ing}</li>
              ))}
            </ul>
          </div>

          <div className="detail-section">
            <h3>Étapes</h3>
            <ol className="steps-list">
              {recipe.steps.map((s, i) => (
                <li key={i}>{s}</li>
              ))}
            </ol>
          </div>

          {recipe.tip && (
            <div className="detail-section">
              <h3>Astuce du chef</h3>
              <p style={{ fontSize: 14, color: "var(--ink-soft)", fontStyle: "italic" }}>{recipe.tip}</p>
            </div>
          )}

          <div className="detail-cta">
            <div className="detail-cta-text">
              Cette recette utilise notre <strong>Sauce {recipe.sauce_name}</strong> ({PROFILE_LABELS[recipe.profile]}).
            </div>
            <a
              className="detail-cta-button"
              href={recipe.sauce_url}
              target="_blank"
              rel="noopener noreferrer"
            >
              Acheter la sauce sur l-fds.com &rarr;
            </a>
          </div>
        </div>
      </div>
    </div>
  );
}
