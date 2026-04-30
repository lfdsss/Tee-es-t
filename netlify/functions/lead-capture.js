// ─────────────────────────────────────────────────────────
// Netlify Function — Lead Capture (HubSpot + GitHub dispatch)
// Push un lead dans HubSpot et declenche optionnellement
// la routine 'morning' du commercial-agent via GitHub dispatch.
// Env requis : HUBSPOT_API_KEY (private key Netlify)
// Env optionnel : GITHUB_DISPATCH_TOKEN, GITHUB_REPO (owner/name)
// ─────────────────────────────────────────────────────────

const HUBSPOT_API = "https://api.hubapi.com";
const ALLOWED_SOURCES = new Set([
  "devis-instant",
  "contact-form",
  "portfolio-cta",
  "homepage",
]);

function isValidEmail(s) {
  if (typeof s !== "string" || s.length < 5 || s.length > 120) return false;
  return /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(s);
}

async function hubspotUpsertContact(props, apiKey) {
  // Tente de creer le contact. Si conflit (409), on le met a jour par email.
  const create = await fetch(`${HUBSPOT_API}/crm/v3/objects/contacts`, {
    method: "POST",
    headers: {
      Authorization: `Bearer ${apiKey}`,
      "Content-Type": "application/json",
    },
    body: JSON.stringify({ properties: props }),
  });

  if (create.status === 201) {
    const data = await create.json();
    return { ok: true, action: "created", id: data.id };
  }

  if (create.status === 409) {
    // Contact existe - PATCH par email
    const patch = await fetch(
      `${HUBSPOT_API}/crm/v3/objects/contacts/${encodeURIComponent(props.email)}?idProperty=email`,
      {
        method: "PATCH",
        headers: {
          Authorization: `Bearer ${apiKey}`,
          "Content-Type": "application/json",
        },
        body: JSON.stringify({ properties: props }),
      }
    );
    if (patch.ok) {
      const data = await patch.json();
      return { ok: true, action: "updated", id: data.id };
    }
    const txt = await patch.text();
    return { ok: false, error: `hubspot patch failed: ${patch.status} ${txt.slice(0, 200)}` };
  }

  const txt = await create.text();
  return { ok: false, error: `hubspot create failed: ${create.status} ${txt.slice(0, 200)}` };
}

async function githubDispatch(token, repo, payload) {
  if (!token || !repo) return { ok: false, skipped: true };
  const res = await fetch(`https://api.github.com/repos/${repo}/dispatches`, {
    method: "POST",
    headers: {
      Authorization: `Bearer ${token}`,
      Accept: "application/vnd.github+json",
      "Content-Type": "application/json",
    },
    body: JSON.stringify({
      event_type: "lead_captured",
      client_payload: payload,
    }),
  });
  if (res.status === 204) return { ok: true };
  const txt = await res.text();
  return { ok: false, error: `github dispatch ${res.status}: ${txt.slice(0, 200)}` };
}

export default async (req) => {
  if (req.method !== "POST") {
    return new Response(JSON.stringify({ error: "method not allowed" }), {
      status: 405, headers: { "Content-Type": "application/json" },
    });
  }

  let body;
  try { body = await req.json(); } catch {
    return new Response(JSON.stringify({ error: "invalid json" }), {
      status: 400, headers: { "Content-Type": "application/json" },
    });
  }

  // Validation
  if (!isValidEmail(body.email)) {
    return new Response(JSON.stringify({ error: "invalid email" }), {
      status: 400, headers: { "Content-Type": "application/json" },
    });
  }
  const source = String(body.source || "homepage");
  if (!ALLOWED_SOURCES.has(source)) {
    return new Response(JSON.stringify({ error: "invalid source" }), {
      status: 400, headers: { "Content-Type": "application/json" },
    });
  }

  const apiKey = process.env.HUBSPOT_API_KEY;
  if (!apiKey) {
    return new Response(JSON.stringify({
      ok: false,
      error: "HUBSPOT_API_KEY not configured on server",
    }), { status: 503, headers: { "Content-Type": "application/json" } });
  }

  // Construction des proprietes contact
  const props = {
    email: body.email.toLowerCase(),
    lifecyclestage: "lead",
    hs_lead_status: "NEW",
  };
  if (body.name) {
    const parts = String(body.name).slice(0, 80).trim().split(/\s+/);
    props.firstname = parts[0] || "";
    if (parts.length > 1) props.lastname = parts.slice(1).join(" ");
  }
  if (body.company) props.company = String(body.company).slice(0, 120);
  if (body.message) props.message = String(body.message).slice(0, 1000);

  // Tags personnalises (champs custom HubSpot a creer cote portail)
  // Si le portail HubSpot n'a pas ces champs, ils seront ignores silencieusement
  // par l'API HubSpot (selon les permissions du token).
  if (body.mission_type) props.mission_type = String(body.mission_type).slice(0, 60);
  if (body.budget) props.budget = String(body.budget).slice(0, 60);

  const hs = await hubspotUpsertContact(props, apiKey);

  // Trigger GitHub dispatch (ne bloque pas la reponse en cas d'echec)
  let gh = { ok: false, skipped: true };
  if (process.env.GITHUB_DISPATCH_TOKEN && process.env.GITHUB_REPO) {
    try {
      gh = await githubDispatch(
        process.env.GITHUB_DISPATCH_TOKEN,
        process.env.GITHUB_REPO,
        {
          email: props.email,
          source,
          mission_type: body.mission_type || null,
          captured_at: new Date().toISOString(),
        }
      );
    } catch (e) {
      gh = { ok: false, error: String(e).slice(0, 200) };
    }
  }

  return new Response(JSON.stringify({
    ok: hs.ok,
    hubspot: hs,
    github_dispatch: gh,
  }), {
    status: hs.ok ? 200 : 502,
    headers: {
      "Content-Type": "application/json",
      "Cache-Control": "no-store",
    },
  });
};

export const config = {
  path: "/api/lead-capture",
};
