// ─────────────────────────────────────────────────────────
// QUIZ ENGINE HOOK
// State management, scoring, timing, interaction tracking
// ─────────────────────────────────────────────────────────

import { useState, useRef, useCallback, useEffect } from "react";
import { QUESTIONS, PROFILES, PROFILE_KEYS } from "../data/quizData";
import {
  generateSessionId,
  collectDeviceContext,
  parseUTMParams,
  buildDataPayload,
  submitData,
} from "../utils/analytics";

const INITIAL_SCORES = PROFILE_KEYS.reduce((acc, k) => ({ ...acc, [k]: 0 }), {});

const STORAGE_KEY = "lfds_quiz_progress";

export default function useQuizEngine({ apiEndpoint = null } = {}) {
  // ─── Core State ───
  const [phase, setPhase] = useState("intro");
  const [currentQ, setCurrentQ] = useState(0);
  const [answers, setAnswers] = useState([]);
  const [profileScores, setProfileScores] = useState({ ...INITIAL_SCORES });
  const [email, setEmail] = useState("");
  const [consentGiven, setConsentGiven] = useState(false);
  const [animating, setAnimating] = useState(false);
  const [selectedOption, setSelectedOption] = useState(null);
  const [submissionResult, setSubmissionResult] = useState(null);

  // ─── Tracking ───
  const sessionIdRef = useRef(generateSessionId());
  const startTimeRef = useRef(Date.now());
  const questionStartRef = useRef(Date.now());
  const [questionTimes, setQuestionTimes] = useState([]);
  const [interactionEvents, setInteractionEvents] = useState([]);
  const deviceContextRef = useRef(null);
  const utmParamsRef = useRef(null);

  // Collect device context and UTM on mount
  useEffect(() => {
    deviceContextRef.current = collectDeviceContext();
    utmParamsRef.current = parseUTMParams();

    // Attempt to restore progress
    try {
      const saved = JSON.parse(localStorage.getItem(STORAGE_KEY));
      if (saved && saved.sessionId && saved.answers?.length > 0) {
        // Only restore if less than 30 minutes old
        if (Date.now() - saved.timestamp < 30 * 60 * 1000) {
          sessionIdRef.current = saved.sessionId;
          setAnswers(saved.answers);
          setProfileScores(saved.profileScores);
          setQuestionTimes(saved.questionTimes);
          setCurrentQ(saved.currentQ);
          setPhase("quiz");
        } else {
          localStorage.removeItem(STORAGE_KEY);
        }
      }
    } catch {
      // ignore
    }
  }, []);

  // Save progress when quiz is in progress
  useEffect(() => {
    if (phase === "quiz" && answers.length > 0) {
      try {
        localStorage.setItem(
          STORAGE_KEY,
          JSON.stringify({
            sessionId: sessionIdRef.current,
            answers,
            profileScores,
            questionTimes,
            currentQ,
            timestamp: Date.now(),
          })
        );
      } catch {
        // ignore
      }
    }
  }, [phase, answers, profileScores, questionTimes, currentQ]);

  // ─── Computed ───
  const progress = (currentQ / QUESTIONS.length) * 100;
  const totalTimeSeconds = +((Date.now() - startTimeRef.current) / 1000).toFixed(0);
  const currentQuestion = QUESTIONS[currentQ] || null;

  function getSortedProfiles() {
    return Object.entries(profileScores).sort((a, b) => b[1] - a[1]);
  }

  const topProfileKey = getSortedProfiles()[0]?.[0] || "epicurien";
  const secondProfileKey = getSortedProfiles()[1]?.[0] || "artisan";
  const topProfile = PROFILES[topProfileKey];
  const secondProfile = PROFILES[secondProfileKey];
  const maxScore = Math.max(...Object.values(profileScores), 1);

  // ─── Actions ───
  const trackInteraction = useCallback((type, data = {}) => {
    setInteractionEvents((prev) => [
      ...prev,
      {
        type,
        timestamp: Date.now(),
        question_index: currentQ,
        ...data,
      },
    ]);
  }, [currentQ]);

  const startQuiz = useCallback(() => {
    setPhase("quiz");
    questionStartRef.current = Date.now();
    trackInteraction("quiz_started");
  }, [trackInteraction]);

  const handleAnswer = useCallback(
    (option, index) => {
      if (animating) return;
      setSelectedOption(index);
      setAnimating(true);

      const timeSpent = +((Date.now() - questionStartRef.current) / 1000).toFixed(1);
      const newTimes = [
        ...questionTimes,
        { question: QUESTIONS[currentQ].id, seconds: timeSpent },
      ];
      setQuestionTimes(newTimes);

      const newScores = { ...profileScores };
      Object.entries(option.profile).forEach(([key, val]) => {
        newScores[key] = (newScores[key] || 0) + val;
      });
      setProfileScores(newScores);

      const newAnswers = [
        ...answers,
        {
          questionId: QUESTIONS[currentQ].id,
          category: QUESTIONS[currentQ].category,
          dataLabel: QUESTIONS[currentQ].dataLabel,
          value: option.value,
          label: option.text,
          timeSeconds: timeSpent,
        },
      ];
      setAnswers(newAnswers);

      trackInteraction("answer_selected", {
        option_value: option.value,
        time_seconds: timeSpent,
      });

      setTimeout(() => {
        if (currentQ < QUESTIONS.length - 1) {
          setCurrentQ(currentQ + 1);
          setSelectedOption(null);
          questionStartRef.current = Date.now();
        } else {
          // Quiz complete — clear saved progress
          try {
            localStorage.removeItem(STORAGE_KEY);
          } catch {
            // ignore
          }
          setPhase("email");
        }
        setAnimating(false);
      }, 600);
    },
    [animating, answers, currentQ, profileScores, questionTimes, trackInteraction]
  );

  const goBack = useCallback(() => {
    if (currentQ > 0 && !animating) {
      trackInteraction("went_back");
      // Remove last answer
      setAnswers((prev) => prev.slice(0, -1));
      setQuestionTimes((prev) => prev.slice(0, -1));
      // Recalculate scores from remaining answers
      const remaining = answers.slice(0, -1);
      const recalculated = { ...INITIAL_SCORES };
      remaining.forEach((a) => {
        const q = QUESTIONS.find((q) => q.id === a.questionId);
        const opt = q?.options.find((o) => o.value === a.value);
        if (opt) {
          Object.entries(opt.profile).forEach(([k, v]) => {
            recalculated[k] += v;
          });
        }
      });
      setProfileScores(recalculated);
      setCurrentQ(currentQ - 1);
      setSelectedOption(null);
      questionStartRef.current = Date.now();
    }
  }, [currentQ, animating, answers, trackInteraction]);

  const handleEmailSubmit = useCallback(async () => {
    trackInteraction("email_submitted", { has_email: !!email });
    setPhase("result");

    const payload = buildDataPayload({
      sessionId: sessionIdRef.current,
      answers,
      profileScores,
      topProfile: topProfileKey,
      secondProfile: secondProfileKey,
      questionTimes,
      totalTimeSeconds: +((Date.now() - startTimeRef.current) / 1000).toFixed(0),
      email,
      consentGiven,
      deviceContext: deviceContextRef.current,
      utmParams: utmParamsRef.current,
      interactionEvents,
    });

    const result = await submitData(payload, apiEndpoint);
    setSubmissionResult(result);
  }, [
    email,
    consentGiven,
    answers,
    profileScores,
    topProfileKey,
    secondProfileKey,
    questionTimes,
    interactionEvents,
    apiEndpoint,
    trackInteraction,
  ]);

  const skipEmail = useCallback(() => {
    trackInteraction("email_skipped");
    setPhase("result");

    const payload = buildDataPayload({
      sessionId: sessionIdRef.current,
      answers,
      profileScores,
      topProfile: topProfileKey,
      secondProfile: secondProfileKey,
      questionTimes,
      totalTimeSeconds: +((Date.now() - startTimeRef.current) / 1000).toFixed(0),
      email: "",
      consentGiven: false,
      deviceContext: deviceContextRef.current,
      utmParams: utmParamsRef.current,
      interactionEvents,
    });

    submitData(payload, apiEndpoint).then(setSubmissionResult);
  }, [
    answers,
    profileScores,
    topProfileKey,
    secondProfileKey,
    questionTimes,
    interactionEvents,
    apiEndpoint,
    trackInteraction,
  ]);

  const restartQuiz = useCallback(() => {
    sessionIdRef.current = generateSessionId();
    startTimeRef.current = Date.now();
    questionStartRef.current = Date.now();
    setPhase("intro");
    setCurrentQ(0);
    setAnswers([]);
    setProfileScores({ ...INITIAL_SCORES });
    setQuestionTimes([]);
    setInteractionEvents([]);
    setEmail("");
    setConsentGiven(false);
    setSelectedOption(null);
    setSubmissionResult(null);
    try {
      localStorage.removeItem(STORAGE_KEY);
    } catch {
      // ignore
    }
  }, []);

  return {
    // State
    phase,
    currentQ,
    answers,
    profileScores,
    email,
    setEmail,
    consentGiven,
    setConsentGiven,
    animating,
    selectedOption,
    submissionResult,

    // Computed
    progress,
    totalTimeSeconds: +((Date.now() - startTimeRef.current) / 1000).toFixed(0),
    currentQuestion,
    topProfileKey,
    secondProfileKey,
    topProfile,
    secondProfile,
    maxScore,
    sortedProfiles: getSortedProfiles(),
    questionTimes,
    interactionEvents,
    sessionId: sessionIdRef.current,

    // Actions
    startQuiz,
    handleAnswer,
    goBack,
    handleEmailSubmit,
    skipEmail,
    restartQuiz,
    trackInteraction,
  };
}
