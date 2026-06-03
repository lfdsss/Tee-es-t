export const PROFILES = [
  {
    id: "epicurien",
    label: "Épicurien",
    desc: "Gastronomique, riche, raffinée",
    gradient: "linear-gradient(135deg, #be185d, #831843)",
  },
  {
    id: "artisan",
    label: "Artisan",
    desc: "Généreuse, rustique, traditionnelle",
    gradient: "linear-gradient(135deg, #c2410c, #7c2d12)",
  },
  {
    id: "pragmatique",
    label: "Pragmatique",
    desc: "Légère, rapide, équilibrée",
    gradient: "linear-gradient(135deg, #15803d, #052e16)",
  },
];

export const PROFILE_BY_ID = Object.fromEntries(PROFILES.map((p) => [p.id, p]));

export const DEFAULT_GRADIENT = "linear-gradient(135deg, #ea580c, #7c2d12)";

export const OCCASIONS = [
  { id: "quotidien", label: "Quotidien" },
  { id: "weekend", label: "Week-end" },
  { id: "reception", label: "Réception" },
  { id: "express", label: "Express" },
];
