// ─────────────────────────────────────────────────────────
// QUIZ APP — La Française des Sauces
// Data collection quiz with elegant, conservative design
// ─────────────────────────────────────────────────────────

import { useState, useEffect } from "react";
import { COLORS, QUESTIONS, PROFILES } from "../data/quizData";
import { getAllStoredSessions, exportSessionsAsCSV } from "../utils/analytics";
import useQuizEngine from "../hooks/useQuizEngine";

// ─── CONFIG ───
// Points to the local API server (proxied via Vite in dev, or direct in prod)
const API_ENDPOINT = "/api/quiz/submit";

export default function QuizApp() {
  const quiz = useQuizEngine({ apiEndpoint: API_ENDPOINT });
  const [showDashboard, setShowDashboard] = useState(false);
  const [fadeKey, setFadeKey] = useState(0);

  // Trigger fade animation on question change
  useEffect(() => {
    setFadeKey((k) => k + 1);
  }, [quiz.currentQ]);

  // ─── INTRO ───
  if (quiz.phase === "intro") {
    return (
      <div style={styles.container}>
        <style>{keyframeStyles}</style>
        <div style={styles.introCard}>
          <div style={styles.introTopAccent} />
          <div style={styles.introContent}>
            <p style={styles.eyebrow}>LA FRANÇAISE DES SAUCES</p>
            <h1 style={styles.introTitle}>
              Quel épicurien
              <br />
              êtes-vous ?
            </h1>
            <Divider />
            <p style={styles.introDesc}>
              8 questions — 2 minutes — un profil qui vous ressemble.
              <br />
              <span style={styles.introDescSub}>
                Découvrez votre identité gourmande et recevez des recommandations
                personnalisées.
              </span>
            </p>
            <HoverButton style={styles.ctaButton} onClick={quiz.startQuiz}>
              Commencer le quiz
            </HoverButton>
            <p style={styles.footerNote}>
              Vos données restent confidentielles · Conforme RGPD
            </p>
          </div>
        </div>
      </div>
    );
  }

  // ─── QUIZ ───
  if (quiz.phase === "quiz") {
    const q = quiz.currentQuestion;
    return (
      <div style={styles.container}>
        <style>{keyframeStyles}</style>
        <div style={styles.quizCard}>
          {/* Progress */}
          <div style={styles.progressContainer}>
            {quiz.currentQ > 0 && (
              <button
                onClick={quiz.goBack}
                style={styles.backButton}
                aria-label="Question précédente"
              >
                ←
              </button>
            )}
            <div style={styles.progressBar}>
              <div
                style={{ ...styles.progressFill, width: `${quiz.progress}%` }}
              />
            </div>
            <span style={styles.progressText}>
              {quiz.currentQ + 1} / {QUESTIONS.length}
            </span>
          </div>

          {/* Question with fade animation */}
          <div key={fadeKey} style={styles.questionSection}>
            <h2 style={styles.questionText}>{q.question}</h2>
            <div style={styles.optionsGrid}>
              {q.options.map((opt, i) => (
                <OptionButton
                  key={`${quiz.currentQ}-${i}`}
                  option={opt}
                  index={i}
                  selected={quiz.selectedOption === i}
                  disabled={quiz.animating}
                  delay={i * 60}
                  onClick={() => quiz.handleAnswer(opt, i)}
                  onHover={() =>
                    quiz.trackInteraction("option_hover", {
                      option_value: opt.value,
                    })
                  }
                />
              ))}
            </div>
          </div>
        </div>
      </div>
    );
  }

  // ─── EMAIL CAPTURE ───
  if (quiz.phase === "email") {
    return (
      <div style={styles.container}>
        <style>{keyframeStyles}</style>
        <div style={{ ...styles.emailCard, animation: "fadeSlideUp 0.5s ease" }}>
          <div style={styles.emailIconWrap}>
            <span style={{ fontSize: 48 }}>{quiz.topProfile.emoji}</span>
          </div>
          <h2 style={styles.emailTitle}>Votre profil est prêt !</h2>
          <p style={styles.emailDesc}>
            Entrez votre email pour découvrir votre résultat et recevoir une
            recommandation personnalisée.
          </p>
          <div style={styles.emailInputWrap}>
            <input
              type="email"
              placeholder="votre@email.com"
              value={quiz.email}
              onChange={(e) => quiz.setEmail(e.target.value)}
              onKeyDown={(e) => {
                if (e.key === "Enter" && quiz.email) quiz.handleEmailSubmit();
              }}
              style={styles.emailInput}
              autoFocus
            />
            {/* Consent checkbox */}
            <label style={styles.consentLabel}>
              <input
                type="checkbox"
                checked={quiz.consentGiven}
                onChange={(e) => quiz.setConsentGiven(e.target.checked)}
                style={styles.consentCheckbox}
              />
              <span style={styles.consentText}>
                J’accepte de recevoir des communications de La Française des Sauces.
                Désinscription possible à tout moment.
              </span>
            </label>
            <HoverButton
              style={{
                ...styles.ctaButton,
                opacity: quiz.email && quiz.consentGiven ? 1 : 0.5,
                pointerEvents:
                  quiz.email && quiz.consentGiven ? "auto" : "none",
              }}
              onClick={quiz.handleEmailSubmit}
            >
              Voir mon profil
            </HoverButton>
          </div>
          <button onClick={quiz.skipEmail} style={styles.skipButton}>
            Continuer sans email →
          </button>
          <p style={styles.rgpdNote}>
            Conforme RGPD · Données hébergées en France · Aucune revente à des tiers
          </p>
        </div>
      </div>
    );
  }

  // ─── RESULT ───
  if (quiz.phase === "result") {
    if (showDashboard) {
      return (
        <DataDashboard
          quiz={quiz}
          onBack={() => setShowDashboard(false)}
        />
      );
    }

    return (
      <div style={styles.container}>
        <style>{keyframeStyles}</style>
        <div style={{ ...styles.resultCard, animation: "fadeSlideUp 0.5s ease" }}>
          <p style={styles.eyebrow}>VOTRE PROFIL</p>

          {/* Main profile */}
          <div style={styles.resultProfileWrap}>
            <div
              style={{
                ...styles.resultEmojiCircle,
                borderColor: quiz.topProfile.color,
              }}
            >
              <span style={{ fontSize: 52 }}>{quiz.topProfile.emoji}</span>
            </div>
            <h1
              style={{
                ...styles.resultName,
                color: quiz.topProfile.color,
              }}
            >
              {quiz.topProfile.name}
            </h1>
            <p style={styles.resultDesc}>{quiz.topProfile.description}</p>
          </div>

          {/* Secondary profile hint */}
          <p style={styles.secondaryHint}>
            Avec une touche de{" "}
            <strong style={{ color: quiz.secondProfile.color }}>
              {quiz.secondProfile.name}
            </strong>{" "}
            {quiz.secondProfile.emoji}
          </p>

          {/* Score bars */}
          <div style={styles.resultBars}>
            {quiz.sortedProfiles.map(([key, val]) => (
              <div key={key} style={styles.resultBarRow}>
                <span style={styles.resultBarLabel}>
                  {PROFILES[key].emoji}{" "}
                  {key.charAt(0).toUpperCase() + key.slice(1)}
                </span>
                <div style={styles.resultBarBg}>
                  <div
                    style={{
                      ...styles.resultBarFill,
                      width: `${(val / quiz.maxScore) * 100}%`,
                      background: PROFILES[key].color,
                      animation: "barGrow 0.8s ease forwards",
                    }}
                  />
                </div>
              </div>
            ))}
          </div>

          {/* Sauce match */}
          <div style={styles.sauceMatchCard}>
            <p style={styles.sauceMatchLabel}>Notre sauce & vous</p>
            <p style={styles.sauceMatchText}>
              {quiz.topProfile.sauce_match}
            </p>
            <HoverButton
              style={{ ...styles.ctaButton, background: COLORS.rouge }}
              hoverBg={COLORS.noir}
              onClick={() =>
                window.open &&
                window.open(
                  quiz.topProfile.cta_url || "https://l-fds.com",
                  "_blank"
                )
              }
            >
              Découvrir la sauce →
            </HoverButton>
          </div>

          {/* Share & Restart */}
          <div style={styles.resultActions}>
            <HoverButton
              style={styles.secondaryButton}
              onClick={quiz.restartQuiz}
            >
              Refaire le quiz
            </HoverButton>
          </div>

          {/* Admin dashboard toggle */}
          <button
            onClick={() => setShowDashboard(true)}
            style={styles.dashboardToggle}
          >
            Voir les données récoltées (vue admin)
          </button>
        </div>
      </div>
    );
  }

  return null;
}

// ─────────────────────────────────────────────────────────
// SUB-COMPONENTS
// ─────────────────────────────────────────────────────────

function Divider() {
  return (
    <div style={styles.divider}>
      <div style={styles.dividerLine} />
      <span style={styles.dividerIcon}>✦</span>
      <div style={styles.dividerLine} />
    </div>
  );
}

function HoverButton({
  children,
  style,
  onClick,
  hoverBg = COLORS.noirLight,
  ...props
}) {
  const [hovered, setHovered] = useState(false);
  return (
    <button
      style={{
        ...style,
        ...(hovered
          ? { background: hoverBg, transform: "translateY(-2px)" }
          : {}),
      }}
      onClick={onClick}
      onMouseEnter={() => setHovered(true)}
      onMouseLeave={() => setHovered(false)}
      {...props}
    >
      {children}
    </button>
  );
}

function OptionButton({ option, index, selected, disabled, delay, onClick, onHover }) {
  const [hovered, setHovered] = useState(false);

  return (
    <button
      onClick={() => !disabled && onClick()}
      onMouseEnter={() => {
        setHovered(true);
        onHover?.();
      }}
      onMouseLeave={() => setHovered(false)}
      style={{
        ...styles.optionCard,
        ...(selected ? styles.optionSelected : {}),
        ...(hovered && !selected
          ? {
              borderColor: COLORS.or,
              transform: "translateY(-3px)",
              boxShadow: "0 8px 24px rgba(10,9,8,0.08)",
            }
          : {}),
        animation: `fadeSlideUp 0.4s ease ${delay}ms both`,
      }}
    >
      <span style={styles.optionIcon}>{option.icon}</span>
      <span style={styles.optionText}>{option.text}</span>
    </button>
  );
}

// ─────────────────────────────────────────────────────────
// DATA DASHBOARD (Admin View)
// ─────────────────────────────────────────────────────────

function DataDashboard({ quiz, onBack }) {
  const [storedSessions, setStoredSessions] = useState([]);

  useEffect(() => {
    setStoredSessions(getAllStoredSessions());
  }, []);

  function handleExportCSV() {
    const csv = exportSessionsAsCSV();
    if (!csv) return;
    const blob = new Blob([csv], { type: "text/csv;charset=utf-8;" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `lfds_quiz_data_${new Date().toISOString().slice(0, 10)}.csv`;
    a.click();
    URL.revokeObjectURL(url);
  }

  function handleCopyJSON() {
    const payload = {
      session_id: quiz.sessionId,
      answers: quiz.answers,
      profile: {
        primary: quiz.topProfileKey,
        secondary: quiz.secondProfileKey,
        scores: quiz.profileScores,
      },
      engagement: {
        total_time_seconds: quiz.totalTimeSeconds,
        question_times: quiz.questionTimes,
      },
      email: quiz.email || null,
    };
    navigator.clipboard?.writeText(JSON.stringify(payload, null, 2));
  }

  return (
    <div style={styles.container}>
      <style>{keyframeStyles}</style>
      <div style={{ ...styles.quizCard, maxWidth: 720 }}>
        {/* Header */}
        <div
          style={{
            display: "flex",
            justifyContent: "space-between",
            alignItems: "center",
            marginBottom: 24,
            flexWrap: "wrap",
            gap: 12,
          }}
        >
          <h2 style={{ ...styles.questionText, fontSize: 20, marginBottom: 0 }}>
            Données récoltées
          </h2>
          <div style={{ display: "flex", gap: 8 }}>
            <button onClick={handleCopyJSON} style={styles.dashAction}>
              Copier JSON
            </button>
            <button onClick={handleExportCSV} style={styles.dashAction}>
              Export CSV ({storedSessions.length} sessions)
            </button>
            <button onClick={onBack} style={styles.skipButton}>
              ← Retour
            </button>
          </div>
        </div>

        {/* Session info */}
        <DashSection title="Session">
          <DashRow label="Session ID" value={quiz.sessionId} />
          <DashRow
            label="Durée totale"
            value={`${quiz.totalTimeSeconds}s`}
          />
          <DashRow
            label="Email"
            value={quiz.email || "Non renseigné"}
          />
          <DashRow
            label="Consentement"
            value={quiz.consentGiven ? "Oui" : "Non"}
          />
        </DashSection>

        {/* Answers */}
        <DashSection title="Réponses">
          {quiz.answers.map((a, i) => (
            <DashRow
              key={i}
              label={`${a.dataLabel}`}
              value={a.value}
              sublabel={`${a.timeSeconds}s`}
            />
          ))}
        </DashSection>

        {/* Profile scores */}
        <DashSection title="Scores profils">
          {quiz.sortedProfiles.map(([key, val]) => (
            <div key={key} style={styles.dashRow}>
              <span style={styles.dashKey}>
                {PROFILES[key].emoji} {PROFILES[key].name}
              </span>
              <div
                style={{
                  display: "flex",
                  alignItems: "center",
                  gap: 8,
                  flex: 1,
                  justifyContent: "flex-end",
                }}
              >
                <div style={styles.dashBarBg}>
                  <div
                    style={{
                      ...styles.dashBarFill,
                      width: `${(val / quiz.maxScore) * 100}%`,
                      background: PROFILES[key].color,
                    }}
                  />
                </div>
                <span
                  style={{
                    ...styles.dashValue,
                    minWidth: 24,
                    textAlign: "right",
                  }}
                >
                  {val}
                </span>
              </div>
            </div>
          ))}
        </DashSection>

        {/* Engagement metrics */}
        <DashSection title="Engagement">
          {quiz.questionTimes.map((t, i) => (
            <DashRow
              key={i}
              label={`Q${i + 1} — ${QUESTIONS[i]?.dataLabel || ""}`}
              value={`${t.seconds}s`}
              highlight={t.seconds > 10}
            />
          ))}
          <div style={{ ...styles.dashRow, borderTop: `1px solid ${COLORS.cremeDark}`, paddingTop: 8, marginTop: 8 }}>
            <span style={{ ...styles.dashKey, fontWeight: 600 }}>
              Temps moyen / question
            </span>
            <span style={{ ...styles.dashValue, fontWeight: 600 }}>
              {quiz.questionTimes.length
                ? (
                    quiz.questionTimes.reduce((s, t) => s + t.seconds, 0) /
                    quiz.questionTimes.length
                  ).toFixed(1)
                : 0}
              s
            </span>
          </div>
          <DashRow
            label="Interactions trackées"
            value={quiz.interactionEvents.length}
          />
          <DashRow
            label="Questions hésitantes (>10s)"
            value={
              quiz.questionTimes.filter((t) => t.seconds > 10).length || "Aucune"
            }
          />
        </DashSection>

        {/* CRM Segment */}
        <div
          style={{
            ...styles.dashSection,
            background: COLORS.noir,
            borderRadius: 12,
            padding: 20,
          }}
        >
          <h3 style={{ ...styles.dashLabel, color: COLORS.or }}>
            Segment CRM suggéré
          </h3>
          <p
            style={{
              fontFamily: "'DM Sans', sans-serif",
              color: COLORS.creme,
              fontSize: 14,
              lineHeight: 1.6,
              margin: 0,
            }}
          >
            Profil principal :{" "}
            <strong>{quiz.topProfile.name}</strong> · Secondaire :{" "}
            <strong>{quiz.secondProfile.name}</strong>
            <br />
            Canal d’achat :{" "}
            <strong>
              {quiz.answers.find((a) => a.questionId === "lieu_achat")?.value ||
                "—"}
            </strong>
            <br />
            Sensibilité prix :{" "}
            <strong>
              {quiz.answers.find((a) => a.questionId === "budget")?.value ||
                "—"}
            </strong>
            <br />
            Canal découverte :{" "}
            <strong>
              {quiz.answers.find((a) => a.questionId === "decouverte")?.value ||
                "—"}
            </strong>
            <br />
            Valeur clé :{" "}
            <strong>
              {quiz.answers.find((a) => a.questionId === "valeurs")?.value ||
                "—"}
            </strong>
          </p>
        </div>

        {/* Stored sessions count */}
        {storedSessions.length > 1 && (
          <p style={{ ...styles.footerNote, marginTop: 16 }}>
            {storedSessions.length} sessions stockées localement · Exportez en CSV
            pour analyse
          </p>
        )}
      </div>
    </div>
  );
}

function DashSection({ title, children }) {
  return (
    <div style={styles.dashSection}>
      <h3 style={styles.dashLabel}>{title}</h3>
      {children}
    </div>
  );
}

function DashRow({ label, value, sublabel, highlight }) {
  return (
    <div style={styles.dashRow}>
      <span
        style={{
          ...styles.dashKey,
          ...(highlight ? { color: COLORS.rouge } : {}),
        }}
      >
        {label}
      </span>
      <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
        {sublabel && (
          <span style={{ fontSize: 11, color: COLORS.gris }}>{sublabel}</span>
        )}
        <span style={styles.dashValue}>{value}</span>
      </div>
    </div>
  );
}

// ─────────────────────────────────────────────────────────
// CSS KEYFRAMES (injected via <style>)
// ─────────────────────────────────────────────────────────

const keyframeStyles = `
  @import url('https://fonts.googleapis.com/css2?family=Cormorant+Garamond:ital,wght@0,400;0,600;0,700;1,400&family=DM+Sans:wght@400;500;600&display=swap');

  @keyframes fadeSlideUp {
    from {
      opacity: 0;
      transform: translateY(16px);
    }
    to {
      opacity: 1;
      transform: translateY(0);
    }
  }

  @keyframes barGrow {
    from { width: 0; }
  }

  * { box-sizing: border-box; }
`;

// ─────────────────────────────────────────────────────────
// STYLES
// ─────────────────────────────────────────────────────────

const styles = {
  // ─── Layout ───
  container: {
    minHeight: "100vh",
    background: `linear-gradient(180deg, ${COLORS.creme} 0%, ${COLORS.cremeDark} 100%)`,
    display: "flex",
    alignItems: "center",
    justifyContent: "center",
    padding: "24px 16px",
    fontFamily: "'DM Sans', sans-serif",
  },

  // ─── Shared ───
  eyebrow: {
    fontFamily: "'DM Sans', sans-serif",
    fontSize: 11,
    letterSpacing: "3px",
    color: COLORS.or,
    fontWeight: 600,
    margin: "0 0 20px",
    textTransform: "uppercase",
  },
  divider: {
    display: "flex",
    alignItems: "center",
    gap: 12,
    justifyContent: "center",
    margin: "0 0 24px",
  },
  dividerLine: {
    height: 1,
    width: 60,
    background: COLORS.cremeDark,
  },
  dividerIcon: {
    color: COLORS.or,
    fontSize: 12,
  },
  footerNote: {
    fontSize: 11,
    color: COLORS.gris,
    marginTop: 20,
    marginBottom: 0,
    textAlign: "center",
  },
  ctaButton: {
    background: COLORS.noir,
    color: "#fff",
    border: "none",
    borderRadius: 10,
    padding: "16px 40px",
    fontSize: 15,
    fontWeight: 600,
    fontFamily: "'DM Sans', sans-serif",
    cursor: "pointer",
    transition: "all 0.25s ease",
    letterSpacing: "0.5px",
    width: "100%",
  },
  skipButton: {
    background: "none",
    border: "none",
    color: COLORS.gris,
    fontSize: 13,
    cursor: "pointer",
    marginTop: 16,
    fontFamily: "'DM Sans', sans-serif",
    textDecoration: "underline",
    textUnderlineOffset: 3,
    padding: 0,
  },
  rgpdNote: {
    fontSize: 11,
    color: COLORS.gris,
    lineHeight: 1.5,
    marginTop: 20,
    marginBottom: 0,
    textAlign: "center",
  },

  // ─── Intro ───
  introCard: {
    background: COLORS.blanc,
    borderRadius: 20,
    maxWidth: 520,
    width: "100%",
    overflow: "hidden",
    boxShadow: "0 12px 48px rgba(10,9,8,0.08)",
    position: "relative",
  },
  introTopAccent: {
    height: 5,
    background: `linear-gradient(90deg, ${COLORS.bleu}, ${COLORS.rouge}, ${COLORS.or})`,
  },
  introContent: {
    padding: "48px 40px 40px",
    textAlign: "center",
  },
  introTitle: {
    fontFamily: "'Cormorant Garamond', Georgia, serif",
    fontSize: 42,
    fontWeight: 700,
    color: COLORS.noir,
    lineHeight: 1.15,
    margin: "0 0 24px",
  },
  introDesc: {
    fontFamily: "'DM Sans', sans-serif",
    fontSize: 16,
    color: COLORS.noirLight,
    lineHeight: 1.6,
    margin: "0 0 32px",
  },
  introDescSub: {
    fontSize: 14,
    color: COLORS.gris,
  },

  // ─── Quiz ───
  quizCard: {
    background: COLORS.blanc,
    borderRadius: 20,
    maxWidth: 580,
    width: "100%",
    padding: "32px 36px 40px",
    boxShadow: "0 12px 48px rgba(10,9,8,0.08)",
  },
  progressContainer: {
    display: "flex",
    alignItems: "center",
    gap: 12,
    marginBottom: 32,
  },
  progressBar: {
    flex: 1,
    height: 4,
    background: COLORS.cremeDark,
    borderRadius: 2,
    overflow: "hidden",
  },
  progressFill: {
    height: "100%",
    background: `linear-gradient(90deg, ${COLORS.bleu}, ${COLORS.or})`,
    borderRadius: 2,
    transition: "width 0.5s ease",
  },
  progressText: {
    fontSize: 12,
    color: COLORS.gris,
    fontWeight: 500,
    whiteSpace: "nowrap",
  },
  backButton: {
    background: "none",
    border: `1px solid ${COLORS.cremeDark}`,
    borderRadius: 8,
    width: 36,
    height: 36,
    display: "flex",
    alignItems: "center",
    justifyContent: "center",
    cursor: "pointer",
    fontSize: 16,
    color: COLORS.gris,
    flexShrink: 0,
    transition: "all 0.2s ease",
    fontFamily: "'DM Sans', sans-serif",
  },
  questionSection: {
    animation: "fadeSlideUp 0.35s ease",
  },
  questionText: {
    fontFamily: "'Cormorant Garamond', Georgia, serif",
    fontSize: 26,
    fontWeight: 600,
    color: COLORS.noir,
    lineHeight: 1.3,
    marginBottom: 28,
    marginTop: 0,
  },
  optionsGrid: {
    display: "flex",
    flexDirection: "column",
    gap: 12,
  },
  optionCard: {
    display: "flex",
    alignItems: "center",
    gap: 14,
    padding: "18px 20px",
    background: COLORS.blanc,
    border: `1.5px solid ${COLORS.cremeDark}`,
    borderRadius: 12,
    cursor: "pointer",
    transition: "all 0.25s ease",
    textAlign: "left",
    fontFamily: "'DM Sans', sans-serif",
    boxShadow: "0 2px 8px rgba(10,9,8,0.04)",
    width: "100%",
  },
  optionSelected: {
    borderColor: COLORS.or,
    background: `${COLORS.or}10`,
    transform: "scale(0.98)",
    boxShadow: `0 0 0 2px ${COLORS.or}30`,
  },
  optionIcon: {
    fontSize: 24,
    flexShrink: 0,
    width: 36,
    textAlign: "center",
  },
  optionText: {
    fontSize: 15,
    color: COLORS.noir,
    lineHeight: 1.4,
    fontWeight: 450,
  },

  // ─── Email ───
  emailCard: {
    background: COLORS.blanc,
    borderRadius: 20,
    maxWidth: 480,
    width: "100%",
    padding: "48px 40px 36px",
    boxShadow: "0 12px 48px rgba(10,9,8,0.08)",
    textAlign: "center",
  },
  emailIconWrap: {
    width: 88,
    height: 88,
    borderRadius: "50%",
    background: COLORS.creme,
    display: "flex",
    alignItems: "center",
    justifyContent: "center",
    margin: "0 auto 24px",
  },
  emailTitle: {
    fontFamily: "'Cormorant Garamond', Georgia, serif",
    fontSize: 28,
    fontWeight: 700,
    color: COLORS.noir,
    marginBottom: 12,
    marginTop: 0,
  },
  emailDesc: {
    fontSize: 15,
    color: COLORS.gris,
    lineHeight: 1.6,
    marginBottom: 28,
  },
  emailInputWrap: {
    display: "flex",
    flexDirection: "column",
    gap: 12,
  },
  emailInput: {
    padding: "14px 18px",
    border: `1.5px solid ${COLORS.cremeDark}`,
    borderRadius: 10,
    fontSize: 15,
    fontFamily: "'DM Sans', sans-serif",
    outline: "none",
    transition: "border-color 0.2s ease",
    color: COLORS.noir,
  },
  consentLabel: {
    display: "flex",
    alignItems: "flex-start",
    gap: 10,
    textAlign: "left",
    cursor: "pointer",
    padding: "4px 0",
  },
  consentCheckbox: {
    marginTop: 3,
    accentColor: COLORS.or,
    flexShrink: 0,
  },
  consentText: {
    fontSize: 12,
    color: COLORS.gris,
    lineHeight: 1.5,
  },

  // ─── Result ───
  resultCard: {
    background: COLORS.blanc,
    borderRadius: 20,
    maxWidth: 560,
    width: "100%",
    padding: "40px 36px 36px",
    boxShadow: "0 12px 48px rgba(10,9,8,0.08)",
    textAlign: "center",
  },
  resultProfileWrap: {
    marginBottom: 20,
  },
  resultEmojiCircle: {
    width: 100,
    height: 100,
    borderRadius: "50%",
    border: "3px solid",
    display: "flex",
    alignItems: "center",
    justifyContent: "center",
    margin: "0 auto 20px",
    background: COLORS.creme,
  },
  resultName: {
    fontFamily: "'Cormorant Garamond', Georgia, serif",
    fontSize: 32,
    fontWeight: 700,
    margin: "0 0 14px",
  },
  resultDesc: {
    fontSize: 15,
    color: COLORS.noirLight,
    lineHeight: 1.65,
    maxWidth: 440,
    margin: "0 auto",
  },
  secondaryHint: {
    fontSize: 14,
    color: COLORS.gris,
    fontStyle: "italic",
    marginBottom: 24,
    marginTop: 0,
  },
  resultBars: {
    margin: "0 0 28px",
    display: "flex",
    flexDirection: "column",
    gap: 10,
  },
  resultBarRow: {
    display: "flex",
    alignItems: "center",
    gap: 12,
  },
  resultBarLabel: {
    fontSize: 12,
    color: COLORS.gris,
    fontWeight: 500,
    width: 110,
    textAlign: "left",
  },
  resultBarBg: {
    flex: 1,
    height: 8,
    background: COLORS.cremeDark,
    borderRadius: 4,
    overflow: "hidden",
  },
  resultBarFill: {
    height: "100%",
    borderRadius: 4,
    transition: "width 0.8s ease",
  },
  sauceMatchCard: {
    background: COLORS.creme,
    borderRadius: 14,
    padding: "24px 28px",
    textAlign: "center",
  },
  sauceMatchLabel: {
    fontSize: 13,
    fontWeight: 600,
    color: COLORS.or,
    letterSpacing: "1px",
    textTransform: "uppercase",
    margin: "0 0 10px",
  },
  sauceMatchText: {
    fontSize: 15,
    color: COLORS.noirLight,
    lineHeight: 1.6,
    fontStyle: "italic",
    margin: 0,
  },
  resultActions: {
    display: "flex",
    gap: 12,
    marginTop: 20,
    justifyContent: "center",
  },
  secondaryButton: {
    background: "transparent",
    color: COLORS.noir,
    border: `1.5px solid ${COLORS.cremeDark}`,
    borderRadius: 10,
    padding: "12px 28px",
    fontSize: 14,
    fontWeight: 500,
    fontFamily: "'DM Sans', sans-serif",
    cursor: "pointer",
    transition: "all 0.25s ease",
  },
  dashboardToggle: {
    background: "none",
    border: `1px dashed ${COLORS.cremeDark}`,
    borderRadius: 8,
    padding: "12px 20px",
    fontSize: 13,
    color: COLORS.gris,
    cursor: "pointer",
    fontFamily: "'DM Sans', sans-serif",
    marginTop: 24,
    width: "100%",
    transition: "all 0.2s ease",
  },

  // ─── Dashboard ───
  dashSection: {
    marginBottom: 24,
  },
  dashLabel: {
    fontSize: 11,
    letterSpacing: "2px",
    textTransform: "uppercase",
    color: COLORS.or,
    fontWeight: 600,
    fontFamily: "'DM Sans', sans-serif",
    margin: "0 0 12px",
  },
  dashRow: {
    display: "flex",
    justifyContent: "space-between",
    alignItems: "center",
    padding: "8px 0",
    borderBottom: `1px solid ${COLORS.creme}`,
    gap: 12,
  },
  dashKey: {
    fontSize: 13,
    color: COLORS.noirLight,
    fontWeight: 450,
  },
  dashValue: {
    fontSize: 13,
    color: COLORS.noir,
    fontWeight: 600,
    fontFamily: "'DM Sans', sans-serif",
  },
  dashBarBg: {
    width: 100,
    height: 6,
    background: COLORS.cremeDark,
    borderRadius: 3,
    overflow: "hidden",
  },
  dashBarFill: {
    height: "100%",
    borderRadius: 3,
  },
  dashAction: {
    background: COLORS.creme,
    border: `1px solid ${COLORS.cremeDark}`,
    borderRadius: 6,
    padding: "6px 14px",
    fontSize: 12,
    fontWeight: 500,
    fontFamily: "'DM Sans', sans-serif",
    cursor: "pointer",
    color: COLORS.noirLight,
    transition: "all 0.2s ease",
  },
};
