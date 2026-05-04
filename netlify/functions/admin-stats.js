// ─────────────────────────────────────────────────────────
// Netlify Function — Admin Stats
// Protected by API key (x-api-key header)
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
    return new Response(
      JSON.stringify({ error: "Unauthorized", message: "Invalid or missing API key" }),
      { status: 401, headers: { "Content-Type": "application/json" } }
    );
  }

  try {
    const store = getStore("quiz-submissions");
    const indexStore = getStore("quiz-index");
    const index = (await indexStore.get("all", { type: "json" })) || [];

    const stats = {
      total_submissions: index.length,
      emails_collected: 0,
      consents_given: 0,
      profiles: { epicurien: 0, artisan: 0, pragmatique: 0, curieux: 0, social: 0 },
      devices: { mobile: 0, tablet: 0, desktop: 0, unknown: 0 },
      avg_time_seconds: 0,
      utm_sources: {},
      top_values: {},
      purchase_channels: {},
      discovery_channels: {},
    };

    let totalTime = 0;

    for (const id of index) {
      const d = await store.get(id, { type: "json" });
      if (!d) continue;

      if (d.contact?.email) stats.emails_collected++;
      if (d.contact?.consent_given) stats.consents_given++;
      if (d.profile?.primary) stats.profiles[d.profile.primary]++;
      if (d.device?.deviceType) stats.devices[d.device.deviceType]++;
      if (d.engagement?.total_time_seconds) totalTime += d.engagement.total_time_seconds;

      if (d.utm?.utm_source) {
        stats.utm_sources[d.utm.utm_source] = (stats.utm_sources[d.utm.utm_source] || 0) + 1;
      }
      if (d.segments?.core_value) {
        stats.top_values[d.segments.core_value] = (stats.top_values[d.segments.core_value] || 0) + 1;
      }
      if (d.segments?.purchase_channel) {
        stats.purchase_channels[d.segments.purchase_channel] =
          (stats.purchase_channels[d.segments.purchase_channel] || 0) + 1;
      }
      if (d.segments?.discovery_channel) {
        stats.discovery_channels[d.segments.discovery_channel] =
          (stats.discovery_channels[d.segments.discovery_channel] || 0) + 1;
      }
    }

    stats.avg_time_seconds = index.length ? Math.round(totalTime / index.length) : 0;
    stats.email_conversion_rate = index.length
      ? +((stats.emails_collected / index.length) * 100).toFixed(1) + "%"
      : "0%";

    return new Response(JSON.stringify(stats, null, 2), {
      status: 200,
      headers: { "Content-Type": "application/json" },
    });
  } catch (err) {
    return new Response(
      JSON.stringify({ error: "Internal error", message: err.message }),
      { status: 500, headers: { "Content-Type": "application/json" } }
    );
  }
};

export const config = {
  path: "/api/admin/stats",
};
