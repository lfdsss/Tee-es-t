// ─────────────────────────────────────────────────────────
// QUIZ DATA — La Française des Sauces
// Questions, profils, couleurs et configuration
// ─────────────────────────────────────────────────────────

export const COLORS = {
  noir: "#0A0908",
  creme: "#F8F5EF",
  bleu: "#0055A4",
  rouge: "#EF4135",
  or: "#C4A35A",
  cremeDark: "#EDE8DC",
  noirLight: "#2A2826",
  gris: "#8A8580",
  blanc: "#FFFFFF",
  vertDoux: "#6B8E5A",
  mauve: "#9B6B9E",
};

export const QUESTIONS = [
  {
    id: "cuisine_freq",
    question: "Vous rentrez du travail. Ce soir, c’est…",
    dataLabel: "Fréquence cuisine maison",
    category: "habitudes",
    options: [
      { text: "Un plat mijoté maison, même si ça prend du temps", value: "quotidien", icon: "🍲", profile: { artisan: 3, epicurien: 2 } },
      { text: "Quelque chose de rapide mais fait maison", value: "regulier", icon: "🍳", profile: { pragmatique: 2, curieux: 1 } },
      { text: "Un bon produit tout prêt, bien choisi", value: "occasionnel", icon: "🛒", profile: { pragmatique: 3 } },
      { text: "On commande, pas d’inspiration ce soir", value: "rare", icon: "📱", profile: { social: 2 } },
    ],
  },
  {
    id: "critere_achat",
    question: "Au rayon sauces, qu’est-ce qui attire votre œil en premier ?",
    dataLabel: "Critère d’achat dominant",
    category: "achat",
    options: [
      { text: "La liste d’ingrédients — courte et claire", value: "ingredients", icon: "🔍", profile: { artisan: 2, epicurien: 2 } },
      { text: "L’origine française, le terroir", value: "origine", icon: "🇫🇷", profile: { epicurien: 3, artisan: 1 } },
      { text: "Le packaging — s’il est beau, je regarde", value: "packaging", icon: "✨", profile: { curieux: 2, social: 1 } },
      { text: "Le prix, soyons honnêtes", value: "prix", icon: "💰", profile: { pragmatique: 3 } },
    ],
  },
  {
    id: "decouverte",
    question: "Comment découvrez-vous un nouveau produit alimentaire ?",
    dataLabel: "Canal de découverte",
    category: "marketing",
    options: [
      { text: "Recommandation d’un proche", value: "bouche_a_oreille", icon: "💬", profile: { social: 3 } },
      { text: "Réseaux sociaux / influenceurs", value: "reseaux", icon: "📲", profile: { curieux: 2, social: 1 } },
      { text: "En magasin, au hasard du rayon", value: "magasin", icon: "🏪", profile: { curieux: 3 } },
      { text: "Articles, blogs, émissions culinaires", value: "media", icon: "📰", profile: { epicurien: 2, artisan: 1 } },
    ],
  },
  {
    id: "reception",
    question: "Vous recevez des amis samedi. Votre approche ?",
    dataLabel: "Comportement réception",
    category: "habitudes",
    options: [
      { text: "Menu élaboré, rien n’est laissé au hasard", value: "elabore", icon: "🎩", profile: { artisan: 3, epicurien: 1 } },
      { text: "Un beau plat principal et de bons produits autour", value: "equilibre", icon: "🍽️", profile: { epicurien: 2, pragmatique: 1 } },
      { text: "Apéro dînatoire — convivial et sans prise de tête", value: "convivial", icon: "🥂", profile: { social: 3 } },
      { text: "Je commande chez un traiteur de qualité", value: "traiteur", icon: "📦", profile: { pragmatique: 2, social: 1 } },
    ],
  },
  {
    id: "sauce_usage",
    question: "Une sauce dans un plat, pour vous c’est…",
    dataLabel: "Rapport à la sauce",
    category: "produit",
    options: [
      { text: "L’élément qui fait toute la différence", value: "essentiel", icon: "⭐", profile: { epicurien: 3, artisan: 1 } },
      { text: "Un plus appréciable quand elle est bonne", value: "important", icon: "👍", profile: { curieux: 2, pragmatique: 1 } },
      { text: "J’en fais moi-même la plupart du temps", value: "fait_maison", icon: "👨‍🍳", profile: { artisan: 3 } },
      { text: "Pas indispensable, ça dépend du plat", value: "occasionnel", icon: "🤷", profile: { pragmatique: 2 } },
    ],
  },
  {
    id: "budget",
    question: "Pour un produit alimentaire de qualité, vous êtes prêt(e) à…",
    dataLabel: "Sensibilité prix",
    category: "achat",
    options: [
      { text: "Mettre le prix sans hésiter si c’est bon", value: "premium", icon: "💎", profile: { epicurien: 3 } },
      { text: "Payer un peu plus cher si ça se justifie", value: "raisonne", icon: "⚖️", profile: { artisan: 2, curieux: 1 } },
      { text: "Comparer et choisir le meilleur rapport qualité-prix", value: "compare", icon: "📊", profile: { pragmatique: 3 } },
      { text: "Craquer de temps en temps pour un produit d’exception", value: "plaisir", icon: "🎁", profile: { curieux: 2, social: 1 } },
    ],
  },
  {
    id: "valeurs",
    question: "Quelle valeur compte le plus dans votre alimentation ?",
    dataLabel: "Valeur alimentaire prioritaire",
    category: "valeurs",
    options: [
      { text: "Le goût avant tout", value: "gout", icon: "😋", profile: { epicurien: 3 } },
      { text: "Le naturel — pas d’additifs, pas de conservateurs", value: "naturel", icon: "🌿", profile: { artisan: 3 } },
      { text: "La praticité au quotidien", value: "praticite", icon: "⚡", profile: { pragmatique: 3 } },
      { text: "Le partage et la convivialité", value: "partage", icon: "❤️", profile: { social: 3 } },
    ],
  },
  {
    id: "lieu_achat",
    question: "Où faites-vous principalement vos courses alimentaires ?",
    dataLabel: "Canal d’achat",
    category: "achat",
    options: [
      { text: "Grandes surfaces (Carrefour, Leclerc, Auchan…)", value: "gms", icon: "🏬", profile: { pragmatique: 2 } },
      { text: "Marchés, producteurs locaux, épiceries fines", value: "epicerie", icon: "🧺", profile: { artisan: 2, epicurien: 2 } },
      { text: "En ligne — livraison ou drive", value: "online", icon: "💻", profile: { pragmatique: 2, curieux: 1 } },
      { text: "Un mix de tout selon l’envie et le produit", value: "mix", icon: "🔄", profile: { curieux: 2, social: 1 } },
    ],
  },
];

export const PROFILES = {
  epicurien: {
    name: "L’Épicurien Exigeant",
    emoji: "🍷",
    color: COLORS.rouge,
    description:
      "Le goût est votre boussole. Vous ne transigez pas sur la qualité et savez reconnaître un produit d’exception au premier regard. Pour vous, bien manger n’est pas un luxe — c’est un art de vivre.",
    sauce_match:
      "La Sauce Beurre & Herbes Fraîches by LFDS a été conçue pour des palais comme le vôtre : des ingrédients nobles, zéro compromis.",
    cta_url: "https://l-fds.com/epicurien",
  },
  artisan: {
    name: "L’Artisan du Quotidien",
    emoji: "👨‍🍳",
    color: COLORS.bleu,
    description:
      "Vous aimez mettre la main à la pâte et maîtriser ce que vous mangez. La liste d’ingrédients n’a pas de secrets pour vous, et le fait-maison est votre terrain de jeu favori.",
    sauce_match:
      "Avec 70% d’ingrédients français, sans additifs ni conservateurs, notre sauce parle votre langue : celle de l’authenticité.",
    cta_url: "https://l-fds.com/artisan",
  },
  pragmatique: {
    name: "Le Pragmatique Malin",
    emoji: "⚡",
    color: COLORS.or,
    description:
      "Vous cherchez l’efficacité sans sacrifier la qualité. Votre temps est précieux et vous savez exactement où mettre votre argent pour un maximum de satisfaction.",
    sauce_match:
      "Un produit prêt en 2 minutes qui élève n’importe quel plat ? C’est exactement ce que LFDS vous propose.",
    cta_url: "https://l-fds.com/pragmatique",
  },
  curieux: {
    name: "Le Curieux Gourmand",
    emoji: "🔍",
    color: COLORS.vertDoux,
    description:
      "Toujours à l’affût d’une nouvelle saveur, d’un produit qu’on ne connaît pas encore. Vous aimez sortir des sentiers battus et raconter vos découvertes.",
    sauce_match:
      "LFDS, c’est la pépite que vous allez adorer faire découvrir à votre entourage.",
    cta_url: "https://l-fds.com/curieux",
  },
  social: {
    name: "Le Convive Généreux",
    emoji: "🥂",
    color: COLORS.mauve,
    description:
      "Pour vous, la cuisine est avant tout un moment de partage. Ce qui compte, c’est le sourire autour de la table, et vous savez créer ces moments.",
    sauce_match:
      "Impressionnez vos invités sans effort : LFDS transforme un plat simple en moment mémorable.",
    cta_url: "https://l-fds.com/social",
  },
};

export const PROFILE_KEYS = Object.keys(PROFILES);
