import { useMemo, useState, useEffect } from "react";
import recipesData from "../data/recipes.json";
import RecipeCard from "./RecipeCard.jsx";
import RecipeFilter from "./RecipeFilter.jsx";
import RecipeDetail from "./RecipeDetail.jsx";

export default function RecipeApp() {
  const [search, setSearch] = useState("");
  const [profile, setProfile] = useState(null); // null | "epicurien" | "artisan" | "pragmatique"
  const [occasion, setOccasion] = useState(null);
  const [maxDifficulty, setMaxDifficulty] = useState(3);
  const [openId, setOpenId] = useState(null);

  // Lock body scroll when modal is open
  useEffect(() => {
    document.body.style.overflow = openId ? "hidden" : "";
    return () => {
      document.body.style.overflow = "";
    };
  }, [openId]);

  // Close on Escape
  useEffect(() => {
    if (!openId) return;
    const onKey = (e) => {
      if (e.key === "Escape") setOpenId(null);
    };
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [openId]);

  const filtered = useMemo(() => {
    const q = search.trim().toLowerCase();
    return recipesData.filter((r) => {
      if (profile && r.profile !== profile) return false;
      if (occasion && r.occasion !== occasion) return false;
      if (r.difficulty > maxDifficulty) return false;
      if (q) {
        const hay = (r.title + " " + r.description + " " + (r.tags || []).join(" ")).toLowerCase();
        if (!hay.includes(q)) return false;
      }
      return true;
    });
  }, [search, profile, occasion, maxDifficulty]);

  const openRecipe = openId ? recipesData.find((r) => r.id === openId) : null;

  return (
    <>
      <header className="site-header">
        <div className="site-header-inner">
          <a className="brand" href="/" aria-label="Accueil">
            <div className="brand-logo">R</div>
            <div className="brand-name">
              Recettes
              <small>La Française des Sauces</small>
            </div>
          </a>
          <a className="header-cta" href="https://l-fds.com" target="_blank" rel="noopener noreferrer">
            La boutique &rarr;
          </a>
        </div>
      </header>

      <section className="hero">
        <div className="hero-tag">Bibliothèque éditoriale</div>
        <h1>
          Cuisinez nos sauces, <em>révélez</em> vos ingrédients
        </h1>
        <p>
          Plus d'une dizaine de recettes simples, gourmandes, conçues pour mettre en valeur les sauces
          La Française des Sauces. Filtrez par profil, occasion ou difficulté.
        </p>
      </section>

      <RecipeFilter
        search={search}
        onSearch={setSearch}
        profile={profile}
        onProfile={setProfile}
        occasion={occasion}
        onOccasion={setOccasion}
        maxDifficulty={maxDifficulty}
        onMaxDifficulty={setMaxDifficulty}
        count={filtered.length}
        total={recipesData.length}
      />

      {filtered.length === 0 ? (
        <div className="empty">
          <p>Aucune recette ne correspond à ces filtres.</p>
          <p style={{ marginTop: 8, fontSize: 13 }}>Essayez de relâcher la difficulté ou de changer le profil.</p>
        </div>
      ) : (
        <div className="recipe-grid">
          {filtered.map((r) => (
            <RecipeCard key={r.id} recipe={r} onOpen={() => setOpenId(r.id)} />
          ))}
        </div>
      )}

      {openRecipe && <RecipeDetail recipe={openRecipe} onClose={() => setOpenId(null)} />}

      <footer className="site-footer">
        <div className="site-footer-line">
          <strong>Recettes — La Française des Sauces</strong>
        </div>
        <div className="site-footer-line">
          Découvrir la boutique : <a href="https://l-fds.com" target="_blank" rel="noopener noreferrer">l-fds.com</a> · Faire le quiz :{" "}
          <a href="https://quiz.l-fds.com" target="_blank" rel="noopener noreferrer">quiz.l-fds.com</a>
        </div>
      </footer>
    </>
  );
}
