import { Link } from "react-router-dom";

/**
 * Illustrated walkthrough of the StudentFlow pipeline.
 *
 * Pure inline SVG + CSS, no image assets, no external deps — so it ships
 * to Netlify in one build with zero extra config and renders instantly
 * on mobile.
 */
export default function HowItWorks() {
  return (
    <section className="howto">
      <header className="howto-hero">
        <span className="eyebrow">Comment ça marche</span>
        <h1>
          4 sources scannées. Un score. <br />
          Une alerte directe au bon étudiant.
        </h1>
        <p>
          Pas de feed à scroller, pas de CV à réuploader 10 fois.
          <br />
          Tu crées ton profil une fois, StudentFlow fait le reste en boucle, 24/7.
        </p>
      </header>

      <Pipeline />

      <div className="steps">
        <Step
          n={1}
          title="Tu crées ton profil en 60 secondes"
          body="Ville, skills, contrats acceptés, heures max/semaine, dispo télétravail. C'est tout. Pas de CV à uploader, pas de lettre de motivation."
          icon={<IconProfile />}
        />
        <Step
          n={2}
          title="On scanne 4 sources en continu"
          body="France Travail, Adzuna, HelloWork et Jooble sont interrogés toutes les 15 minutes. Nouvelles offres agrégées, dédupliquées, normalisées en base."
          icon={<IconScrape />}
        />
        <Step
          n={3}
          title="Chaque offre est scorée contre ton profil"
          body="Moteur de matching déterministe : skills (40 %), ville (25 %), contrat (15 %), heures (10 %), dispo (10 %). Sous 10 ms par paire. Pas de LLM dans le hot path, donc pas de hallucinations."
          icon={<IconMatch />}
        />
        <Step
          n={4}
          title="Tu reçois une alerte directe si le score dépasse 60 %"
          body="Email SMTP direct à ton inbox (Gmail, OVH, Infomaniak…) avec le titre, l'entreprise, la ville, le score et les raisons du match. Un clic sur le lien, tu postules."
          icon={<IconNotify />}
        />
      </div>

      <section className="why">
        <h2>Pourquoi ça marche</h2>
        <div className="why-grid">
          <WhyCard
            title="Temps réel"
            body="Les agents tournent indépendamment. Une offre créée à 14h23 chez France Travail peut arriver dans ta boîte mail à 14h24."
          />
          <WhyCard
            title="Déterministe"
            body="Le moteur de matching est pur, testé, auditable. Même score pour les mêmes inputs, pas de black box LLM."
          />
          <WhyCard
            title="Résilient"
            body="Si un scraper tombe, les autres continuent. Si l'email échoue, le match est retenté au tick suivant. La pipeline ne casse pas."
          />
          <WhyCard
            title="Zéro vendor lock-in"
            body="SMTP standard, Postgres (Supabase), Python/FastAPI. Tu peux migrer où tu veux en une après-midi."
          />
        </div>
      </section>

      <div className="cta">
        <h2>Prêt à tester ?</h2>
        <div className="cta-buttons">
          <Link to="/signup">
            <button>Créer mon profil</button>
          </Link>
          <Link to="/stats">
            <button className="ghost">Voir les stats live</button>
          </Link>
        </div>
      </div>

      <style>{CSS}</style>
    </section>
  );
}

/* ----------------------------------------------------------------------- */
/* Pipeline diagram                                                         */
/* ----------------------------------------------------------------------- */

function Pipeline() {
  return (
    <div className="pipeline">
      <svg viewBox="0 0 900 260" role="img" aria-label="Pipeline StudentFlow">
        <defs>
          <linearGradient id="flow" x1="0" x2="1" y1="0" y2="0">
            <stop offset="0%" stopColor="#7c5cff" stopOpacity="0.1" />
            <stop offset="50%" stopColor="#7c5cff" stopOpacity="1" />
            <stop offset="100%" stopColor="#7c5cff" stopOpacity="0.1" />
          </linearGradient>
          <filter id="glow">
            <feGaussianBlur stdDeviation="3" result="coloredBlur" />
            <feMerge>
              <feMergeNode in="coloredBlur" />
              <feMergeNode in="SourceGraphic" />
            </feMerge>
          </filter>
        </defs>

        {/* Sources */}
        <PipeNode x={40} y={30} label="France Travail" sub="OAuth2" />
        <PipeNode x={40} y={95} label="Adzuna" sub="REST key" />
        <PipeNode x={40} y={160} label="HelloWork" sub="RSS" />
        <PipeNode x={40} y={225} label="Jooble" sub="POST JSON" />

        {/* Arrows sources → scraper */}
        <PipeArrow x1={220} y1={55} x2={330} y2={130} />
        <PipeArrow x1={220} y1={120} x2={330} y2={130} />
        <PipeArrow x1={220} y1={185} x2={330} y2={130} />
        <PipeArrow x1={220} y1={250} x2={330} y2={130} />

        {/* Scraper agent */}
        <PipeBox x={330} y={100} w={140} h={60} label="ScraperAgent" sub="toutes les 15 min" />

        {/* Arrow scraper → matcher */}
        <PipeArrow x1={470} y1={130} x2={540} y2={130} />

        {/* Matcher */}
        <PipeBox x={540} y={100} w={140} h={60} label="MatcherAgent" sub="score ∈ [0, 1]" />

        {/* Arrow matcher → notifier */}
        <PipeArrow x1={680} y1={130} x2={750} y2={130} />

        {/* Notifier */}
        <PipeBox x={750} y={100} w={120} h={60} label="Notifier" sub="email / hook" />

        {/* Student icon */}
        <g transform="translate(810,210)">
          <circle r="18" fill="#14181d" stroke="#31c48d" strokeWidth="2" />
          <text x="0" y="5" textAnchor="middle" fontSize="18" fill="#31c48d">
            ✓
          </text>
          <text x="0" y="42" textAnchor="middle" fontSize="11" fill="#8a94a3">
            étudiant
          </text>
        </g>
        <PipeArrow x1={810} y1={160} x2={810} y2={190} vertical />
      </svg>
    </div>
  );
}

function PipeNode({ x, y, label, sub }: { x: number; y: number; label: string; sub: string }) {
  return (
    <g transform={`translate(${x},${y})`}>
      <rect
        width={180}
        height={48}
        rx={10}
        fill="#14181d"
        stroke="#23292f"
        strokeWidth={1}
      />
      <circle cx={18} cy={24} r={5} fill="#7c5cff" filter="url(#glow)" />
      <text x={32} y={22} fill="#e9edf2" fontSize={13} fontWeight={600}>
        {label}
      </text>
      <text x={32} y={38} fill="#8a94a3" fontSize={11}>
        {sub}
      </text>
    </g>
  );
}

function PipeBox({
  x,
  y,
  w,
  h,
  label,
  sub,
}: {
  x: number;
  y: number;
  w: number;
  h: number;
  label: string;
  sub: string;
}) {
  return (
    <g transform={`translate(${x},${y})`}>
      <rect
        width={w}
        height={h}
        rx={12}
        fill="#1a1f27"
        stroke="#7c5cff"
        strokeWidth={1.5}
      />
      <text x={w / 2} y={h / 2 - 4} textAnchor="middle" fill="#e9edf2" fontSize={14} fontWeight={700}>
        {label}
      </text>
      <text x={w / 2} y={h / 2 + 14} textAnchor="middle" fill="#8a94a3" fontSize={11}>
        {sub}
      </text>
    </g>
  );
}

function PipeArrow({
  x1,
  y1,
  x2,
  y2,
  vertical,
}: {
  x1: number;
  y1: number;
  x2: number;
  y2: number;
  vertical?: boolean;
}) {
  const mid = vertical ? `M${x1},${y1} L${x2},${y2}` : `M${x1},${y1} C${(x1 + x2) / 2},${y1} ${(x1 + x2) / 2},${y2} ${x2},${y2}`;
  return (
    <g>
      <path d={mid} stroke="url(#flow)" strokeWidth={2} fill="none" />
      <circle cx={x2} cy={y2} r={3} fill="#7c5cff" />
    </g>
  );
}

/* ----------------------------------------------------------------------- */
/* Step block                                                               */
/* ----------------------------------------------------------------------- */

function Step({
  n,
  title,
  body,
  icon,
}: {
  n: number;
  title: string;
  body: string;
  icon: React.ReactNode;
}) {
  return (
    <div className="step">
      <div className="step-icon">{icon}</div>
      <div className="step-body">
        <span className="step-num">Étape {n}</span>
        <h3>{title}</h3>
        <p>{body}</p>
      </div>
    </div>
  );
}

function WhyCard({ title, body }: { title: string; body: string }) {
  return (
    <div className="why-card">
      <h3>{title}</h3>
      <p>{body}</p>
    </div>
  );
}

/* ----------------------------------------------------------------------- */
/* Inline icons                                                             */
/* ----------------------------------------------------------------------- */

function IconProfile() {
  return (
    <svg viewBox="0 0 64 64" width="56" height="56">
      <circle cx="32" cy="32" r="30" fill="#1a1f27" stroke="#7c5cff" />
      <circle cx="32" cy="26" r="8" fill="#7c5cff" />
      <path d="M16 50 C18 40 46 40 48 50 Z" fill="#7c5cff" />
    </svg>
  );
}

function IconScrape() {
  return (
    <svg viewBox="0 0 64 64" width="56" height="56">
      <circle cx="32" cy="32" r="30" fill="#1a1f27" stroke="#7c5cff" />
      <rect x="16" y="18" width="32" height="6" rx="2" fill="#7c5cff" />
      <rect x="16" y="29" width="22" height="4" rx="2" fill="#8a94a3" />
      <rect x="16" y="37" width="28" height="4" rx="2" fill="#8a94a3" />
      <rect x="16" y="45" width="18" height="4" rx="2" fill="#8a94a3" />
    </svg>
  );
}

function IconMatch() {
  return (
    <svg viewBox="0 0 64 64" width="56" height="56">
      <circle cx="32" cy="32" r="30" fill="#1a1f27" stroke="#7c5cff" />
      <circle cx="24" cy="32" r="10" fill="none" stroke="#7c5cff" strokeWidth="2" />
      <circle cx="40" cy="32" r="10" fill="none" stroke="#31c48d" strokeWidth="2" />
      <path d="M24 32 a10 10 0 0 0 16 0" fill="#7c5cff" opacity="0.3" />
    </svg>
  );
}

function IconNotify() {
  return (
    <svg viewBox="0 0 64 64" width="56" height="56">
      <circle cx="32" cy="32" r="30" fill="#1a1f27" stroke="#7c5cff" />
      <path d="M20 24 L44 24 L44 44 L20 44 Z" fill="none" stroke="#7c5cff" strokeWidth="2" />
      <path d="M20 24 L32 34 L44 24" fill="none" stroke="#7c5cff" strokeWidth="2" />
      <circle cx="44" cy="24" r="5" fill="#31c48d" />
    </svg>
  );
}

/* ----------------------------------------------------------------------- */
/* Scoped CSS                                                               */
/* ----------------------------------------------------------------------- */

const CSS = `
.howto { max-width: 960px; margin: 0 auto; padding: 0 0 4rem; }
.howto-hero { text-align: center; padding: 2.5rem 0 2rem; }
.howto-hero .eyebrow {
  display: inline-block;
  background: rgba(124, 92, 255, 0.12);
  color: var(--accent);
  font-size: 0.75rem;
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: 0.1em;
  padding: 0.35rem 0.75rem;
  border-radius: 99px;
  margin-bottom: 1rem;
}
.howto-hero h1 { font-size: 2.1rem; line-height: 1.2; margin: 0 0 1rem; }
.howto-hero p  { color: var(--fg-muted); max-width: 620px; margin: 0 auto; line-height: 1.6; }

.pipeline {
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: var(--radius);
  padding: 1rem;
  margin: 2rem 0 3rem;
  overflow-x: auto;
}
.pipeline svg { width: 100%; height: auto; min-width: 640px; }

.steps { display: grid; gap: 1.25rem; margin-bottom: 3rem; }
.step {
  display: flex;
  gap: 1.25rem;
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: var(--radius);
  padding: 1.25rem 1.5rem;
  align-items: flex-start;
}
.step-icon { flex: 0 0 56px; }
.step-body { flex: 1; }
.step-num {
  font-size: 0.7rem;
  font-weight: 700;
  color: var(--accent);
  text-transform: uppercase;
  letter-spacing: 0.1em;
}
.step-body h3 { margin: 0.35rem 0 0.4rem; font-size: 1.15rem; }
.step-body p  { margin: 0; color: var(--fg-muted); line-height: 1.55; font-size: 0.95rem; }

.why h2 { text-align: center; margin-bottom: 1.5rem; }
.why-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
  gap: 1rem;
  margin-bottom: 3rem;
}
.why-card {
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: var(--radius);
  padding: 1.1rem 1.25rem;
}
.why-card h3 { margin: 0 0 0.4rem; font-size: 1rem; color: var(--accent); }
.why-card p  { margin: 0; color: var(--fg-muted); font-size: 0.9rem; line-height: 1.5; }

.cta { text-align: center; padding: 2rem 0 1rem; }
.cta h2 { margin-bottom: 1.5rem; }
.cta-buttons { display: flex; gap: 1rem; justify-content: center; flex-wrap: wrap; }
.cta button.ghost { background: transparent; border: 1px solid var(--border); }

@media (max-width: 640px) {
  .howto-hero h1 { font-size: 1.6rem; }
  .step { flex-direction: column; }
}
`;
