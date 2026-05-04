// ─────────────────────────────────────────────────────────
// HubSpot integration — push quiz leads to HubSpot CRM
// ─────────────────────────────────────────────────────────
//
// Sends each quiz submission (with email + consent) to HubSpot:
//   1. Upsert contact by email (uses /crm/v3/objects/contacts/upsert pattern)
//   2. Set native fields (hs_persona, lifecyclestage, hs_analytics_source...)
//   3. Attach a Note containing the full quiz details
//
// Env: HUBSPOT_TOKEN (Private App access token). If absent, the integration
// is skipped silently — the quiz keeps working locally without HubSpot.
// ─────────────────────────────────────────────────────────

const HUBSPOT_API = "https://api.hubapi.com";
const HUBSPOT_TOKEN = process.env.HUBSPOT_TOKEN;

// Map quiz profile keys → human label for hs_persona
const PROFILE_LABELS = {
  epicurien: "Épicurien",
  artisan: "Artisan",
  pragmatique: "Pragmatique",
  curieux: "Curieux",
  social: "Social",
};

async function hsRequest(path, method, body) {
  const res = await fetch(`${HUBSPOT_API}${path}`, {
    method,
    headers: {
      Authorization: `Bearer ${HUBSPOT_TOKEN}`,
      "Content-Type": "application/json",
    },
    body: body ? JSON.stringify(body) : undefined,
  });

  const text = await res.text();
  let json;
  try {
    json = text ? JSON.parse(text) : {};
  } catch {
    json = { raw: text };
  }

  if (!res.ok) {
    const err = new Error(
      `HubSpot ${method} ${path} → ${res.status}: ${json.message || text}`
    );
    err.status = res.status;
    err.body = json;
    throw err;
  }
  return json;
}

// Search for an existing contact by email
async function findContactByEmail(email) {
  const result = await hsRequest("/crm/v3/objects/contacts/search", "POST", {
    filterGroups: [
      {
        filters: [{ propertyName: "email", operator: "EQ", value: email }],
      },
    ],
    properties: ["email", "firstname", "lastname", "hs_persona"],
    limit: 1,
  });
  return result.results?.[0] || null;
}

// Create or update a contact with quiz data
async function upsertContact(data) {
  const email = data.contact?.email;
  if (!email) return null;

  const profile = data.profile?.primary;
  const profileLabel = PROFILE_LABELS[profile] || profile || "";

  const properties = {
    email,
    hs_persona: profileLabel,
    lifecyclestage: "lead",
    hs_lead_status: "NEW",
    hs_analytics_source: "OFFLINE",
    hs_analytics_source_data_1: "LFDS Quiz",
    hs_analytics_source_data_2: `lfds_quiz_${profile || "unknown"}`,
  };

  // Pass UTM data if available
  if (data.utm?.utm_source) {
    properties.hs_analytics_source_data_2 += ` | utm:${data.utm.utm_source}`;
  }

  const existing = await findContactByEmail(email);

  if (existing) {
    await hsRequest(
      `/crm/v3/objects/contacts/${existing.id}`,
      "PATCH",
      { properties }
    );
    return { id: existing.id, action: "updated" };
  }

  const created = await hsRequest("/crm/v3/objects/contacts", "POST", {
    properties,
  });
  return { id: created.id, action: "created" };
}

// Attach a Note with the full quiz details to the contact
async function attachQuizNote(contactId, data) {
  const profile = data.profile?.primary;
  const scores = data.profile?.scores || {};
  const answers = data.answers || [];
  const eng = data.engagement || {};
  const utm = data.utm || {};

  const noteBody = [
    "🍷 LFDS Quiz — Soumission",
    "",
    `Profil principal : ${PROFILE_LABELS[profile] || profile || "?"}`,
    `Profil secondaire : ${PROFILE_LABELS[data.profile?.secondary] || data.profile?.secondary || "?"}`,
    "",
    "── Scores ──",
    Object.entries(scores)
      .map(([k, v]) => `  ${k}: ${v}`)
      .join("\n"),
    "",
    "── Engagement ──",
    `  Temps total : ${eng.total_time_seconds || 0}s`,
    `  Hésitations (>10s) : ${eng.hesitation_questions || 0}`,
    `  Réponses rapides (<2s) : ${eng.fast_answers || 0}`,
    "",
    "── Réponses au quiz ──",
    answers.map((a) => `  ${a.question_id} : ${a.value}`).join("\n"),
    "",
    "── Source ──",
    `  UTM source : ${utm.utm_source || "(direct)"}`,
    `  UTM medium : ${utm.utm_medium || "—"}`,
    `  UTM campaign : ${utm.utm_campaign || "—"}`,
    `  Referrer : ${data.device?.referrer || "—"}`,
    `  Device : ${data.device?.deviceType || "—"}`,
    "",
    `Session ID : ${data.session_id}`,
    `Date : ${data.completed_at || new Date().toISOString()}`,
  ].join("\n");

  // Create the note
  const note = await hsRequest("/crm/v3/objects/notes", "POST", {
    properties: {
      hs_note_body: noteBody,
      hs_timestamp: Date.now().toString(),
    },
  });

  // Associate the note to the contact (default association type id = 202 for note↔contact)
  await hsRequest(
    `/crm/v3/objects/notes/${note.id}/associations/contacts/${contactId}/note_to_contact`,
    "PUT"
  );

  return note.id;
}

// Public entry point — non-blocking, swallows errors
async function pushQuizLeadToHubSpot(data) {
  if (!HUBSPOT_TOKEN) {
    return { skipped: true, reason: "HUBSPOT_TOKEN not set" };
  }
  if (!data?.contact?.email) {
    return { skipped: true, reason: "no email collected" };
  }
  if (!data.contact.consent_given) {
    return { skipped: true, reason: "no RGPD consent" };
  }

  try {
    const contact = await upsertContact(data);
    let noteId = null;
    if (contact?.id) {
      try {
        noteId = await attachQuizNote(contact.id, data);
      } catch (noteErr) {
        // Note failure shouldn't block contact creation
        console.warn(
          `[hubspot] Note attach failed for contact ${contact.id}: ${noteErr.message}`
        );
      }
    }
    return { ok: true, contactId: contact?.id, action: contact?.action, noteId };
  } catch (err) {
    console.error(`[hubspot] Push failed: ${err.message}`);
    return { ok: false, error: err.message };
  }
}

module.exports = { pushQuizLeadToHubSpot };
