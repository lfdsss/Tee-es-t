// ─────────────────────────────────────────────────────────
// Netlify Function — Quiz Submit
// Public endpoint to receive quiz submissions
// Storage: Netlify Blobs
// ─────────────────────────────────────────────────────────

import { getStore } from "@netlify/blobs";

export default async (req) => {
  if (req.method !== "POST") {
    return new Response(JSON.stringify({ error: "Method not allowed" }), {
      status: 405,
      headers: { "Content-Type": "application/json" },
    });
  }

  try {
    const data = await req.json();

    if (!data || !data.session_id) {
      return new Response(JSON.stringify({ error: "Missing session_id" }), {
        status: 400,
        headers: { "Content-Type": "application/json" },
      });
    }

    const store = getStore("quiz-submissions");
    await store.setJSON(data.session_id, data);

    // Also maintain an index of session IDs
    const indexStore = getStore("quiz-index");
    const existingIndex = (await indexStore.get("all", { type: "json" })) || [];
    if (!existingIndex.includes(data.session_id)) {
      existingIndex.push(data.session_id);
      await indexStore.setJSON("all", existingIndex);
    }

    console.log(
      `[quiz-submit] ${data.session_id} | ${data.profile?.primary} | ${data.contact?.email || "no-email"}`
    );

    return new Response(
      JSON.stringify({ success: true, session_id: data.session_id }),
      {
        status: 200,
        headers: {
          "Content-Type": "application/json",
          "Access-Control-Allow-Origin": "*",
        },
      }
    );
  } catch (err) {
    console.error("[quiz-submit] error:", err);
    return new Response(
      JSON.stringify({ error: "Internal error", message: err.message }),
      { status: 500, headers: { "Content-Type": "application/json" } }
    );
  }
};

export const config = {
  path: "/api/quiz/submit",
};
