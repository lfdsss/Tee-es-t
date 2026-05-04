// ─────────────────────────────────────────────────────────
// Netlify Function — Health Check (public)
// ─────────────────────────────────────────────────────────

export default async () => {
  return new Response(
    JSON.stringify({
      status: "ok",
      timestamp: new Date().toISOString(),
      service: "lfds-quiz",
    }),
    {
      status: 200,
      headers: { "Content-Type": "application/json" },
    }
  );
};

export const config = {
  path: "/api/health",
};
