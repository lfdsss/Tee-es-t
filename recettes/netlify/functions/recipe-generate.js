// ─────────────────────────────────────────────────────────
// Netlify Function — Recipe Generator (Claude API)
// Génère une recette personnalisée à partir d'une sauce LFDS,
// d'ingrédients du frigo, d'un nombre de portions et d'une occasion.
// Env requis : ANTHROPIC_API_KEY
// Path : POST /api/recipe-generate
// ─────────────────────────────────────────────────────────

const ANTHROPIC_API = "https://api.anthropic.com/v1/messages";
const ANTHROPIC_VERSION = "2023-06-01";
const MODEL = "claude-sonnet-4-6";

const LFDS_SAUCES = {
  epicurien: {
    label: "Épicurien",
    profile_text: "raffinée, gastronomique, riche, à base de réductions, de truffe, de cerise, de porto ou de beurre blanc. Sublime les viandes nobles, les poissons fins et les plats de fête.",
  },
  artisan: {
    label: "Artisan",
    profile_text: "généreuse, rustique, corsée, à base de moutarde ancienne, de vin rouge, de champignons forestiers. Idéale sur les viandes mijotées, les volailles et les plats traditionnels français.",
  },
  pragmatique: {
    label: "Pragmatique",
    profile_text: "fraîche, légère, parfumée, à base de yaourt, de citron, d'estragon, de thaï citronnelle ou de tamarin cacahuète. Parfaite pour les bowls, les wraps, les salades et les repas équilibrés rapides.",
  },
};

const ALLOWED_OCCASIONS = new Set(["quotidien", "weekend", "reception", "express"]);

// ─── Validation ─────────────────────────────────────────

function validatePayload(body) {
  if (!body || typeof body !== "object") return "invalid body";

  if (!body.profile || !LFDS_SAUCES[body.profile]) {
    return "invalid profile (epicurien|artisan|pragmatique)";
  }

  if (!Array.isArray(body.ingredients) || body.ingredients.length < 1 || body.ingredients.length > 12) {
    return "ingredients must be array of 1-12 items";
  }
  for (const ing of body.ingredients) {
    if (typeof ing !== "string" || ing.length < 2 || ing.length > 60) {
      return "each ingredient must be string of 2-60 chars";
    }
  }

  const servings = Number(body.servings);
  if (!Number.isFinite(servings) || servings < 1 || servings > 8) {
    return "servings must be 1-8";
  }

  if (body.occasion && !ALLOWED_OCCASIONS.has(body.occasion)) {
    return "invalid occasion (quotidien|weekend|reception|express)";
  }

  return null;
}

// ─── Prompt builder ─────────────────────────────────────

function buildPrompt(payload) {
  const sauce = LFDS_SAUCES[payload.profile];
  const ingredientsList = payload.ingredients.map((i) => `- ${i.trim()}`).join("\n");
  const occasion = payload.occasion || "quotidien";
  const servings = Math.round(Number(payload.servings));

  const occasionGuide = {
    express: "très rapide (moins de 20 minutes), peu d'ustensiles, technique simple",
    quotidien: "moyen (20 à 35 minutes), équilibrée, réalisable en semaine",
    weekend: "généreux (35 à 60 minutes), un peu plus travaillée, gourmande",
    reception: "élégant (40 à 75 minutes), dressage soigné, qualité réception",
  };

  return `Tu es un chef cuisinier français qui crée des recettes pour La Française des Sauces (LFDS).
Tu dois inventer UNE seule recette originale qui met en valeur une sauce LFDS du profil ${sauce.label}.

CONTRAINTES STRICTES :
- La recette doit utiliser une Sauce LFDS ${sauce.label} (${sauce.profile_text})
- Le nombre de portions doit être exactement ${servings}
- L'occasion est "${occasion}" → recette ${occasionGuide[occasion]}
- Tu dois utiliser au maximum les ingrédients fournis par l'utilisateur, et compléter uniquement avec des produits de base courants (sel, poivre, huile, beurre, oignon, ail, herbes, etc.)
- Réponds UNIQUEMENT en JSON valide, sans texte avant ou après, sans bloc markdown
- La recette doit être réalisable, savoureuse et cohérente
- Les étapes doivent être numérotées implicitement (array d'étapes), claires et concises (1-2 phrases chacune)

INGRÉDIENTS DE L'UTILISATEUR :
${ingredientsList}

FORMAT DE RÉPONSE OBLIGATOIRE (JSON strict) :
{
  "title": "Titre court et appétissant",
  "description": "Une phrase qui donne envie (max 180 caractères)",
  "sauce_name": "Nom précis de la sauce LFDS ${sauce.label} utilisée",
  "emoji": "Un seul emoji représentant le plat",
  "difficulty": 1 | 2 | 3,
  "time_min": entier (temps total en minutes),
  "ingredients": ["liste détaillée avec quantités précises pour ${servings} personnes"],
  "steps": ["étape 1", "étape 2", "..."],
  "tip": "Une astuce de chef pratique (max 200 caractères)"
}`;
}

// ─── Claude API call ────────────────────────────────────

async function callClaude(apiKey, prompt) {
  const res = await fetch(ANTHROPIC_API, {
    method: "POST",
    headers: {
      "x-api-key": apiKey,
      "anthropic-version": ANTHROPIC_VERSION,
      "Content-Type": "application/json",
    },
    body: JSON.stringify({
      model: MODEL,
      max_tokens: 1500,
      temperature: 0.8,
      messages: [{ role: "user", content: prompt }],
    }),
  });

  if (!res.ok) {
    const txt = await res.text();
    throw new Error(`anthropic ${res.status}: ${txt.slice(0, 300)}`);
  }

  const data = await res.json();
  const text = data?.content?.[0]?.text;
  if (!text) throw new Error("anthropic empty response");
  return text;
}

function extractJson(raw) {
  const trimmed = raw.trim();
  // Si réponse encapsulée dans un bloc markdown, on extrait
  const match = trimmed.match(/```(?:json)?\s*([\s\S]*?)```/);
  const candidate = match ? match[1].trim() : trimmed;
  return JSON.parse(candidate);
}

function normalizeRecipe(raw, payload) {
  const id = `ai-${Date.now().toString(36)}`;
  const profile = payload.profile;

  return {
    id,
    title: String(raw.title || "Recette personnalisée").slice(0, 120),
    description: String(raw.description || "").slice(0, 220),
    profile,
    sauce_name: String(raw.sauce_name || `LFDS ${LFDS_SAUCES[profile].label}`).slice(0, 80),
    sauce_url: `https://l-fds.com/${profile}`,
    emoji: String(raw.emoji || "🍽️").slice(0, 4),
    occasion: payload.occasion || "quotidien",
    difficulty: [1, 2, 3].includes(raw.difficulty) ? raw.difficulty : 2,
    time_min: Math.max(5, Math.min(180, Number(raw.time_min) || 30)),
    servings: Math.round(Number(payload.servings)),
    ingredients: Array.isArray(raw.ingredients)
      ? raw.ingredients.slice(0, 25).map((i) => String(i).slice(0, 200))
      : [],
    steps: Array.isArray(raw.steps)
      ? raw.steps.slice(0, 15).map((s) => String(s).slice(0, 400))
      : [],
    tip: raw.tip ? String(raw.tip).slice(0, 240) : null,
    tags: ["ia", profile, payload.occasion || "quotidien"],
    generated: true,
  };
}

// ─── Handler ────────────────────────────────────────────

export default async (req) => {
  if (req.method !== "POST") {
    return new Response(JSON.stringify({ error: "method not allowed" }), {
      status: 405,
      headers: { "Content-Type": "application/json" },
    });
  }

  let body;
  try {
    body = await req.json();
  } catch {
    return new Response(JSON.stringify({ error: "invalid json" }), {
      status: 400,
      headers: { "Content-Type": "application/json" },
    });
  }

  const validationError = validatePayload(body);
  if (validationError) {
    return new Response(JSON.stringify({ error: validationError }), {
      status: 400,
      headers: { "Content-Type": "application/json" },
    });
  }

  const apiKey = process.env.ANTHROPIC_API_KEY;
  if (!apiKey) {
    return new Response(
      JSON.stringify({ error: "ANTHROPIC_API_KEY not configured on server" }),
      { status: 503, headers: { "Content-Type": "application/json" } }
    );
  }

  const prompt = buildPrompt(body);

  try {
    const raw = await callClaude(apiKey, prompt);
    const parsed = extractJson(raw);
    const recipe = normalizeRecipe(parsed, body);
    return new Response(JSON.stringify({ ok: true, recipe }), {
      status: 200,
      headers: {
        "Content-Type": "application/json",
        "Cache-Control": "no-store",
      },
    });
  } catch (err) {
    return new Response(
      JSON.stringify({
        ok: false,
        error: "generation failed",
        detail: String(err).slice(0, 300),
      }),
      { status: 502, headers: { "Content-Type": "application/json" } }
    );
  }
};

export const config = {
  path: "/api/recipe-generate",
};
