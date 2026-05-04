// ─────────────────────────────────────────────────────────
// Netlify Function — Admin CSV Export
// Protected by API key
// ─────────────────────────────────────────────────────────

import { getStore } from "@netlify/blobs";

function checkAuth(req) {
  const key =
    req.headers.get("x-api-key") ||
    req.headers.get("authorization")?.replace("Bearer ", "");
  const expected = Netlify.env.get("LFDS_API_KEY");
  return expected && key === expected;
}

export default async (req) => {
  if (!checkAuth(req)) {
    return new Response("Unauthorized", { status: 401 });
  }

  try {
    const store = getStore("quiz-submissions");
    const indexStore = getStore("quiz-index");
    const index = (await indexStore.get("all", { type: "json" })) || [];

    const headers = [
      "session_id", "completed_at", "email", "consent",
      "primary_profile", "secondary_profile", "total_time_seconds",
      "device_type", "utm_source", "utm_medium", "utm_campaign",
      "cuisine_freq", "critere_achat", "decouverte", "reception",
      "sauce_usage", "budget", "valeurs", "lieu_achat",
      "score_epicurien", "score_artisan", "score_pragmatique", "score_curieux", "score_social",
    ];

    const rows = [];
    for (const id of index) {
      const d = await store.get(id, { type: "json" });
      if (!d) continue;

      const answerMap = {};
      (d.answers || []).forEach((a) => {
        answerMap[a.question_id] = a.value;
      });

      rows.push(
        [
          d.session_id, d.completed_at, d.contact?.email || "", d.contact?.consent_given ? "oui" : "non",
          d.profile?.primary, d.profile?.secondary, d.engagement?.total_time_seconds,
          d.device?.deviceType, d.utm?.utm_source || "", d.utm?.utm_medium || "", d.utm?.utm_campaign || "",
          answerMap.cuisine_freq, answerMap.critere_achat, answerMap.decouverte, answerMap.reception,
          answerMap.sauce_usage, answerMap.budget, answerMap.valeurs, answerMap.lieu_achat,
          d.profile?.scores?.epicurien || 0, d.profile?.scores?.artisan || 0,
          d.profile?.scores?.pragmatique || 0, d.profile?.scores?.curieux || 0, d.profile?.scores?.social || 0,
        ]
          .map((v) => `"${String(v ?? "").replace(/"/g, '""')}"`)
          .join(",")
      );
    }

    const csv = [headers.join(","), ...rows].join("\n");
    const filename = `lfds_quiz_export_${new Date().toISOString().slice(0, 10)}.csv`;

    return new Response(csv, {
      status: 200,
      headers: {
        "Content-Type": "text/csv; charset=utf-8",
        "Content-Disposition": `attachment; filename="${filename}"`,
      },
    });
  } catch (err) {
    return new Response(`Error: ${err.message}`, { status: 500 });
  }
};

export const config = {
  path: "/api/admin/export/csv",
};
