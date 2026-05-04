// ─────────────────────────────────────────────────────────
// LFDS QUIZ — API SERVER
// Receives quiz submissions, validates API key, stores data
// ─────────────────────────────────────────────────────────

const express = require("express");
const cors = require("cors");
const fs = require("fs");
const path = require("path");
const crypto = require("crypto");
const { pushQuizLeadToHubSpot } = require("./hubspot");

const app = express();
const PORT = process.env.PORT || 3001;

// ─── API KEY ───
// Generate a unique key on first run, or use the one in .env
const ENV_PATH = path.join(__dirname, "..", ".env");
let API_KEY = process.env.LFDS_API_KEY;

if (!API_KEY) {
  // Check if .env exists with a key
  if (fs.existsSync(ENV_PATH)) {
    const envContent = fs.readFileSync(ENV_PATH, "utf-8");
    const match = envContent.match(/LFDS_API_KEY=(.+)/);
    if (match) API_KEY = match[1].trim();
  }

  // Generate one if still missing
  if (!API_KEY) {
    API_KEY = "lfds_" + crypto.randomBytes(24).toString("hex");
    const envLine = `LFDS_API_KEY=${API_KEY}\n`;
    fs.appendFileSync(ENV_PATH, envLine);
    console.log("──────────────────────────────────────────────");
    console.log("  NEW API KEY GENERATED AND SAVED TO .env");
    console.log(`  ${API_KEY}`);
    console.log("──────────────────────────────────────────────");
  }
}

// ─── DATA STORAGE ───
const DATA_DIR = path.join(__dirname, "data");
if (!fs.existsSync(DATA_DIR)) {
  fs.mkdirSync(DATA_DIR, { recursive: true });
}

// ─── MIDDLEWARE ───
app.use(cors());
app.use(express.json({ limit: "1mb" }));

// API key validation middleware
function requireApiKey(req, res, next) {
  const key =
    req.headers["x-api-key"] ||
    req.headers["authorization"]?.replace("Bearer ", "");

  if (!key || key !== API_KEY) {
    return res.status(401).json({
      error: "Unauthorized",
      message: "Invalid or missing API key. Use header: x-api-key",
    });
  }
  next();
}

// ─── ROUTES ───

// Health check (no auth)
app.get("/api/health", (req, res) => {
  res.json({ status: "ok", timestamp: new Date().toISOString() });
});

// Submit quiz data (no auth — public endpoint for quiz takers)
app.post("/api/quiz/submit", (req, res) => {
  const data = req.body;

  if (!data || !data.session_id) {
    return res.status(400).json({ error: "Missing session_id" });
  }

  // Save to individual JSON file
  const filename = `${data.session_id}.json`;
  const filepath = path.join(DATA_DIR, filename);
  fs.writeFileSync(filepath, JSON.stringify(data, null, 2));

  // Append to daily aggregate file
  const today = new Date().toISOString().slice(0, 10);
  const dailyPath = path.join(DATA_DIR, `daily_${today}.jsonl`);
  fs.appendFileSync(dailyPath, JSON.stringify(data) + "\n");

  console.log(
    `[${new Date().toISOString()}] Quiz submitted: ${data.session_id} | Profile: ${data.profile?.primary} | Email: ${data.contact?.email || "none"}`
  );

  // Push to HubSpot CRM (fire-and-forget — don't block the quiz response)
  pushQuizLeadToHubSpot(data)
    .then((result) => {
      if (result.ok) {
        console.log(
          `[hubspot] Contact ${result.action} (id=${result.contactId})${result.noteId ? `, note=${result.noteId}` : ""}`
        );
      } else if (result.skipped) {
        // Silent skip — nothing to log in normal operation
      }
    })
    .catch((err) => {
      console.error(`[hubspot] Unexpected error: ${err.message}`);
    });

  res.json({ success: true, session_id: data.session_id });
});

// ─── PROTECTED ROUTES (require API key) ───

// List all submissions
app.get("/api/admin/submissions", requireApiKey, (req, res) => {
  const files = fs
    .readdirSync(DATA_DIR)
    .filter((f) => f.endsWith(".json") && !f.startsWith("daily_"))
    .sort()
    .reverse();

  const limit = parseInt(req.query.limit) || 50;
  const offset = parseInt(req.query.offset) || 0;

  const submissions = files.slice(offset, offset + limit).map((f) => {
    try {
      return JSON.parse(fs.readFileSync(path.join(DATA_DIR, f), "utf-8"));
    } catch {
      return null;
    }
  }).filter(Boolean);

  res.json({
    total: files.length,
    limit,
    offset,
    submissions,
  });
});

// Get single submission
app.get("/api/admin/submissions/:sessionId", requireApiKey, (req, res) => {
  const filepath = path.join(DATA_DIR, `${req.params.sessionId}.json`);
  if (!fs.existsSync(filepath)) {
    return res.status(404).json({ error: "Session not found" });
  }
  const data = JSON.parse(fs.readFileSync(filepath, "utf-8"));
  res.json(data);
});

// Aggregated stats
app.get("/api/admin/stats", requireApiKey, (req, res) => {
  const files = fs
    .readdirSync(DATA_DIR)
    .filter((f) => f.endsWith(".json") && !f.startsWith("daily_"));

  const stats = {
    total_submissions: files.length,
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

  files.forEach((f) => {
    try {
      const d = JSON.parse(fs.readFileSync(path.join(DATA_DIR, f), "utf-8"));

      if (d.contact?.email) stats.emails_collected++;
      if (d.contact?.consent_given) stats.consents_given++;
      if (d.profile?.primary) stats.profiles[d.profile.primary]++;
      if (d.device?.deviceType) stats.devices[d.device.deviceType]++;
      if (d.engagement?.total_time_seconds) totalTime += d.engagement.total_time_seconds;

      // UTM sources
      if (d.utm?.utm_source) {
        stats.utm_sources[d.utm.utm_source] = (stats.utm_sources[d.utm.utm_source] || 0) + 1;
      }

      // Segments
      if (d.segments?.core_value) {
        stats.top_values[d.segments.core_value] = (stats.top_values[d.segments.core_value] || 0) + 1;
      }
      if (d.segments?.purchase_channel) {
        stats.purchase_channels[d.segments.purchase_channel] = (stats.purchase_channels[d.segments.purchase_channel] || 0) + 1;
      }
      if (d.segments?.discovery_channel) {
        stats.discovery_channels[d.segments.discovery_channel] = (stats.discovery_channels[d.segments.discovery_channel] || 0) + 1;
      }
    } catch {
      // skip corrupted files
    }
  });

  stats.avg_time_seconds = files.length ? Math.round(totalTime / files.length) : 0;
  stats.email_conversion_rate = files.length
    ? +(stats.emails_collected / files.length * 100).toFixed(1) + "%"
    : "0%";

  res.json(stats);
});

// Export CSV
app.get("/api/admin/export/csv", requireApiKey, (req, res) => {
  const files = fs
    .readdirSync(DATA_DIR)
    .filter((f) => f.endsWith(".json") && !f.startsWith("daily_"));

  const headers = [
    "session_id", "completed_at", "email", "consent",
    "primary_profile", "secondary_profile", "total_time_seconds",
    "device_type", "utm_source", "utm_medium", "utm_campaign",
    "cuisine_freq", "critere_achat", "decouverte", "reception",
    "sauce_usage", "budget", "valeurs", "lieu_achat",
    "score_epicurien", "score_artisan", "score_pragmatique", "score_curieux", "score_social",
  ];

  const rows = files.map((f) => {
    try {
      const d = JSON.parse(fs.readFileSync(path.join(DATA_DIR, f), "utf-8"));
      const answerMap = {};
      (d.answers || []).forEach((a) => { answerMap[a.question_id] = a.value; });

      return [
        d.session_id, d.completed_at, d.contact?.email || "", d.contact?.consent_given ? "oui" : "non",
        d.profile?.primary, d.profile?.secondary, d.engagement?.total_time_seconds,
        d.device?.deviceType, d.utm?.utm_source || "", d.utm?.utm_medium || "", d.utm?.utm_campaign || "",
        answerMap.cuisine_freq, answerMap.critere_achat, answerMap.decouverte, answerMap.reception,
        answerMap.sauce_usage, answerMap.budget, answerMap.valeurs, answerMap.lieu_achat,
        d.profile?.scores?.epicurien || 0, d.profile?.scores?.artisan || 0,
        d.profile?.scores?.pragmatique || 0, d.profile?.scores?.curieux || 0, d.profile?.scores?.social || 0,
      ].map((v) => `"${String(v ?? "").replace(/"/g, '""')}"`).join(",");
    } catch {
      return null;
    }
  }).filter(Boolean);

  const csv = [headers.join(","), ...rows].join("\n");

  res.setHeader("Content-Type", "text/csv; charset=utf-8");
  res.setHeader("Content-Disposition", `attachment; filename="lfds_quiz_export_${new Date().toISOString().slice(0, 10)}.csv"`);
  res.send(csv);
});

// Delete a submission
app.delete("/api/admin/submissions/:sessionId", requireApiKey, (req, res) => {
  const filepath = path.join(DATA_DIR, `${req.params.sessionId}.json`);
  if (!fs.existsSync(filepath)) {
    return res.status(404).json({ error: "Session not found" });
  }
  fs.unlinkSync(filepath);
  res.json({ success: true, deleted: req.params.sessionId });
});

// ─── SERVE FRONTEND IN PRODUCTION ───
const DIST_DIR = path.join(__dirname, "..", "dist");
if (fs.existsSync(DIST_DIR)) {
  app.use(express.static(DIST_DIR));
  // SPA fallback — serve index.html for all non-API routes
  app.get("*", (req, res) => {
    if (!req.path.startsWith("/api")) {
      res.sendFile(path.join(DIST_DIR, "index.html"));
    }
  });
}

// ─── START ───
app.listen(PORT, () => {
  const isProduction = fs.existsSync(DIST_DIR);
  console.log("");
  console.log("  ╔══════════════════════════════════════════╗");
  console.log("  ║     LFDS Quiz — API Server               ║");
  console.log("  ╚══════════════════════════════════════════╝");
  console.log("");
  console.log(`  Mode:     ${isProduction ? "PRODUCTION (serving frontend)" : "DEVELOPMENT (API only)"}`);
  console.log(`  URL:      http://localhost:${PORT}`);
  console.log(`  API Key:  ${API_KEY}`);
  console.log("");
  console.log("  Public:");
  console.log("    POST /api/quiz/submit");
  console.log("    GET  /api/health");
  console.log("");
  console.log("  Admin (x-api-key required):");
  console.log("    GET  /api/admin/submissions");
  console.log("    GET  /api/admin/stats");
  console.log("    GET  /api/admin/export/csv");
  console.log("    DEL  /api/admin/submissions/:id");
  console.log("");
});
