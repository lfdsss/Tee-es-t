// ─────────────────────────────────────────────────────────
// ANALYTICS & DATA COLLECTION UTILITIES
// Collecte enrichie, session tracking, export
// ─────────────────────────────────────────────────────────

/**
 * Generates a unique session ID (UUID v4-like)
 */
export function generateSessionId() {
  if (typeof crypto !== "undefined" && crypto.randomUUID) {
    return crypto.randomUUID();
  }
  return "xxxx-xxxx-4xxx-yxxx-xxxx".replace(/[xy]/g, (c) => {
    const r = (Math.random() * 16) | 0;
    return (c === "x" ? r : (r & 0x3) | 0x8).toString(16);
  });
}

/**
 * Collects non-PII device & context metadata
 */
export function collectDeviceContext() {
  if (typeof window === "undefined") return {};

  const nav = window.navigator || {};
  const screen = window.screen || {};

  return {
    viewport: {
      width: window.innerWidth,
      height: window.innerHeight,
    },
    screen: {
      width: screen.width,
      height: screen.height,
    },
    deviceType: getDeviceType(),
    language: nav.language || null,
    platform: nav.platform || null,
    userAgent: nav.userAgent || null,
    timezone: Intl?.DateTimeFormat?.()?.resolvedOptions?.()?.timeZone || null,
    timestamp: new Date().toISOString(),
  };
}

/**
 * Parses UTM parameters from current URL
 */
export function parseUTMParams() {
  if (typeof window === "undefined") return {};

  const params = new URLSearchParams(window.location.search);
  const utmKeys = ["utm_source", "utm_medium", "utm_campaign", "utm_term", "utm_content"];
  const utm = {};

  utmKeys.forEach((key) => {
    const val = params.get(key);
    if (val) utm[key] = val;
  });

  // Also capture referrer
  if (document.referrer) {
    utm.referrer = document.referrer;
  }

  return utm;
}

/**
 * Determines device type from viewport
 */
function getDeviceType() {
  if (typeof window === "undefined") return "unknown";
  const w = window.innerWidth;
  if (w < 768) return "mobile";
  if (w < 1024) return "tablet";
  return "desktop";
}

/**
 * Builds the complete data payload for submission
 */
export function buildDataPayload({
  sessionId,
  answers,
  profileScores,
  topProfile,
  secondProfile,
  questionTimes,
  totalTimeSeconds,
  email,
  consentGiven,
  deviceContext,
  utmParams,
  interactionEvents,
}) {
  return {
    // Session
    session_id: sessionId,
    completed_at: new Date().toISOString(),
    quiz_version: "2.0",

    // Answers (structured for CRM/analytics)
    answers: answers.map((a) => ({
      question_id: a.questionId,
      category: a.category,
      data_label: a.dataLabel,
      value: a.value,
      label: a.label,
      time_seconds: a.timeSeconds,
    })),

    // Profile
    profile: {
      primary: topProfile,
      secondary: secondProfile,
      scores: profileScores,
    },

    // Segments (pre-computed for CRM)
    segments: {
      purchase_channel: answers.find((a) => a.questionId === "lieu_achat")?.value || null,
      price_sensitivity: answers.find((a) => a.questionId === "budget")?.value || null,
      discovery_channel: answers.find((a) => a.questionId === "decouverte")?.value || null,
      cooking_frequency: answers.find((a) => a.questionId === "cuisine_freq")?.value || null,
      sauce_relationship: answers.find((a) => a.questionId === "sauce_usage")?.value || null,
      core_value: answers.find((a) => a.questionId === "valeurs")?.value || null,
    },

    // Engagement metrics
    engagement: {
      total_time_seconds: totalTimeSeconds,
      question_times: questionTimes,
      avg_time_per_question: questionTimes.length
        ? +(questionTimes.reduce((s, t) => s + t.seconds, 0) / questionTimes.length).toFixed(1)
        : 0,
      hesitation_questions: questionTimes
        .filter((t) => t.seconds > 10)
        .map((t) => t.question),
      fast_answers: questionTimes
        .filter((t) => t.seconds < 2)
        .map((t) => t.question),
      interaction_count: interactionEvents?.length || 0,
    },

    // Contact
    contact: {
      email: email || null,
      consent_given: consentGiven,
      consent_timestamp: consentGiven ? new Date().toISOString() : null,
    },

    // Context
    device: deviceContext,
    utm: utmParams,

    // Interaction events (option hovers, back navigations, etc.)
    interactions: interactionEvents || [],
  };
}

/**
 * Submits data to configured endpoint
 * Falls back to localStorage if network fails
 */
export async function submitData(payload, endpoint) {
  // Always save to localStorage as backup
  saveToLocalStorage(payload);

  if (!endpoint) {
    console.info("[LFDS Quiz] No endpoint configured. Data saved to localStorage only.");
    return { success: true, method: "localStorage" };
  }

  try {
    const res = await fetch(endpoint, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });

    if (!res.ok) throw new Error(`HTTP ${res.status}`);

    return { success: true, method: "api" };
  } catch (err) {
    console.warn("[LFDS Quiz] API submission failed, data saved locally:", err.message);
    return { success: true, method: "localStorage", error: err.message };
  }
}

/**
 * Saves quiz data to localStorage
 */
function saveToLocalStorage(payload) {
  try {
    const key = `lfds_quiz_${payload.session_id}`;
    localStorage.setItem(key, JSON.stringify(payload));

    // Also maintain an index of all sessions
    const index = JSON.parse(localStorage.getItem("lfds_quiz_sessions") || "[]");
    if (!index.includes(payload.session_id)) {
      index.push(payload.session_id);
      localStorage.setItem("lfds_quiz_sessions", JSON.stringify(index));
    }
  } catch {
    // localStorage might be full or unavailable
  }
}

/**
 * Retrieves all stored quiz sessions from localStorage
 */
export function getAllStoredSessions() {
  try {
    const index = JSON.parse(localStorage.getItem("lfds_quiz_sessions") || "[]");
    return index
      .map((id) => {
        try {
          return JSON.parse(localStorage.getItem(`lfds_quiz_${id}`));
        } catch {
          return null;
        }
      })
      .filter(Boolean);
  } catch {
    return [];
  }
}

/**
 * Exports all stored sessions as CSV
 */
export function exportSessionsAsCSV() {
  const sessions = getAllStoredSessions();
  if (!sessions.length) return "";

  const headers = [
    "session_id",
    "completed_at",
    "email",
    "primary_profile",
    "secondary_profile",
    "total_time_seconds",
    "device_type",
    "utm_source",
    "utm_medium",
    "utm_campaign",
    "cuisine_freq",
    "critere_achat",
    "decouverte",
    "reception",
    "sauce_usage",
    "budget",
    "valeurs",
    "lieu_achat",
    "score_epicurien",
    "score_artisan",
    "score_pragmatique",
    "score_curieux",
    "score_social",
  ];

  const rows = sessions.map((s) => {
    const answerMap = {};
    (s.answers || []).forEach((a) => {
      answerMap[a.question_id] = a.value;
    });

    return [
      s.session_id,
      s.completed_at,
      s.contact?.email || "",
      s.profile?.primary || "",
      s.profile?.secondary || "",
      s.engagement?.total_time_seconds || "",
      s.device?.deviceType || "",
      s.utm?.utm_source || "",
      s.utm?.utm_medium || "",
      s.utm?.utm_campaign || "",
      answerMap.cuisine_freq || "",
      answerMap.critere_achat || "",
      answerMap.decouverte || "",
      answerMap.reception || "",
      answerMap.sauce_usage || "",
      answerMap.budget || "",
      answerMap.valeurs || "",
      answerMap.lieu_achat || "",
      s.profile?.scores?.epicurien || 0,
      s.profile?.scores?.artisan || 0,
      s.profile?.scores?.pragmatique || 0,
      s.profile?.scores?.curieux || 0,
      s.profile?.scores?.social || 0,
    ]
      .map((v) => `"${String(v).replace(/"/g, '""')}"`)
      .join(",");
  });

  return [headers.join(","), ...rows].join("\n");
}
