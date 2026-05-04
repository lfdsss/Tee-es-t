import { Link } from "react-router-dom";

/**
 * Gate "Je suis étudiant / Je suis une entreprise".
 *
 * Deux funnels distincts derrière une seule landing. Tout passe par ici
 * pour éviter l'utilisateur perdu qui ne sait pas où cliquer.
 */
export default function Home() {
  return (
    <>
      <section className="hero">
        <h1>Le bon job étudiant, envoyé au bon étudiant, en temps réel.</h1>
        <p>
          StudentFlow scanne en continu France Travail, Adzuna, HelloWork et Jooble,
          score chaque offre contre ton profil, et te notifie dès qu'une correspondance
          dépasse 60&nbsp;%. Zéro chasse, zéro perte de temps.
        </p>
        <div className="robot-strip" title="3 agents autonomes">
          <span className="robot-dot" />
          Robot en ligne · 4 sources scannées 24/7
        </div>
      </section>

      <section className="gate">
        <Link to="/student" className="gate-card">
          <div className="gate-icon" aria-hidden>
            <svg viewBox="0 0 64 64" width="64" height="64">
              <circle cx="32" cy="32" r="30" fill="#1a1f27" stroke="#7c5cff" strokeWidth="2" />
              <circle cx="32" cy="26" r="9" fill="#7c5cff" />
              <path d="M14 52 C16 40 48 40 50 52 Z" fill="#7c5cff" />
            </svg>
          </div>
          <h2>Je suis étudiant</h2>
          <p>
            Crée ton profil en 60&nbsp;secondes. Reçois les meilleures missions autour
            de toi par email, sans rien chercher.
          </p>
          <span className="gate-cta">Commencer →</span>
        </Link>

        <Link to="/company" className="gate-card">
          <div className="gate-icon" aria-hidden>
            <svg viewBox="0 0 64 64" width="64" height="64">
              <circle cx="32" cy="32" r="30" fill="#1a1f27" stroke="#31c48d" strokeWidth="2" />
              <rect x="16" y="22" width="32" height="26" rx="2" fill="#31c48d" />
              <rect x="22" y="28" width="5" height="5" fill="#0b0d10" />
              <rect x="30" y="28" width="5" height="5" fill="#0b0d10" />
              <rect x="38" y="28" width="5" height="5" fill="#0b0d10" />
              <rect x="22" y="36" width="5" height="5" fill="#0b0d10" />
              <rect x="30" y="36" width="5" height="5" fill="#0b0d10" />
              <rect x="38" y="36" width="5" height="5" fill="#0b0d10" />
            </svg>
          </div>
          <h2>Je suis une entreprise</h2>
          <p>
            Poste ta mission en 2&nbsp;min. StudentFlow la score contre nos étudiants
            actifs et te sort les meilleurs profils dispos.
          </p>
          <span className="gate-cta">Publier une mission →</span>
        </Link>
      </section>

      <section className="how">
        <h2>Comment ça marche</h2>
        <p>
          <Link to="/how-it-works">Voir le pipeline illustré →</Link>
        </p>
      </section>
    </>
  );
}
