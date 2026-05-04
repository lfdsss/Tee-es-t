// ─────────────────────────────────────────────────────────
// Netlify Function — Generateur de devis instant (public)
// Port JS de commercial-agent/document_generator.py (generate_devis)
// Permet a un visiteur de simuler un devis sans contact prealable.
// Securite : input strictement valide cote serveur.
// ─────────────────────────────────────────────────────────

const COMPANY = {
  name: "SNB Consulting",
  owner: "Baptiste Thevenot",
  email: "bp.thevenot@gmail.com",
  status: "Entrepreneur Individuel",
  tva: "Franchise en base de TVA - Art. 293 B du CGI",
  address: "France",
};

const MISSION_TYPES = {
  "agent-commercial": "Agent commercial autonome (CRM + emails + relances)",
  "automation-python": "Automatisation Python de taches recurrentes",
  "scraping": "Pipeline de scraping et collecte de donnees",
  "dashboard": "Dashboard temps reel multi-source",
  "rag": "Systeme RAG (recherche semantique sur documents)",
  "integration-hubspot": "Integration et structuration HubSpot",
  "autre": "Mission sur-mesure (a cadrer)",
};

const PHASE_RATIOS = [
  { name: "Cadrage et validation du perimetre", ratio: 0.15 },
  { name: "Developpement et implementation", ratio: 0.60 },
  { name: "Tests et recette", ratio: 0.15 },
  { name: "Documentation et transfert", ratio: 0.10 },
];

const CSS_PRINT = `
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');
* { margin: 0; padding: 0; box-sizing: border-box; }
body { font-family: 'Inter', sans-serif; font-size: 13px; color: #1e293b; padding: 40px; max-width: 800px; margin: 0 auto; }
@media print { body { padding: 20px; } .no-print { display: none; } @page { margin: 1.5cm; } }
.header { display: flex; justify-content: space-between; align-items: flex-start; padding-bottom: 24px; border-bottom: 3px solid #0ea5e9; margin-bottom: 24px; }
.header-left h1 { font-size: 22px; font-weight: 800; color: #0f172a; }
.header-left p { font-size: 11px; color: #64748b; margin-top: 2px; }
.header-right { text-align: right; font-size: 11px; color: #64748b; line-height: 1.6; }
.doc-title { text-align: center; margin: 24px 0; }
.doc-title h2 { font-size: 18px; font-weight: 700; color: #0f172a; }
.doc-title .doc-num { font-size: 12px; color: #0ea5e9; font-weight: 600; margin-top: 4px; }
.info-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 20px; margin-bottom: 24px; }
.info-box { background: #f8fafc; border: 1px solid #e2e8f0; border-radius: 8px; padding: 16px; }
.info-box h3 { font-size: 10px; font-weight: 700; text-transform: uppercase; letter-spacing: 0.5px; color: #0ea5e9; margin-bottom: 8px; }
.info-box p { font-size: 12px; line-height: 1.6; color: #334155; }
table { width: 100%; border-collapse: collapse; margin: 20px 0; }
th { background: #0f172a; color: white; padding: 10px 12px; font-size: 11px; font-weight: 600; text-align: left; text-transform: uppercase; letter-spacing: 0.3px; }
td { padding: 10px 12px; font-size: 12px; border-bottom: 1px solid #e2e8f0; }
tr:nth-child(even) { background: #f8fafc; }
.total-row td { font-weight: 700; font-size: 14px; border-top: 2px solid #0f172a; background: white; }
.section { margin: 24px 0; }
.section h3 { font-size: 14px; font-weight: 700; color: #0f172a; margin-bottom: 8px; padding-bottom: 6px; border-bottom: 1px solid #e2e8f0; }
.section p, .section li { font-size: 12px; line-height: 1.7; color: #475569; }
.section ul { padding-left: 20px; }
.footer { margin-top: 40px; padding-top: 16px; border-top: 1px solid #e2e8f0; font-size: 10px; color: #94a3b8; text-align: center; }
.badge { display: inline-block; padding: 3px 10px; border-radius: 12px; font-size: 10px; font-weight: 700; }
.badge-devis { background: #dbeafe; color: #1d4ed8; }
.notice { background: #fef3c7; border-left: 3px solid #f59e0b; padding: 12px 16px; margin: 16px 0; font-size: 11px; color: #78350f; border-radius: 4px; }
.btn-print { display: inline-block; padding: 10px 24px; background: #0ea5e9; color: white; border: none; border-radius: 8px; font-size: 13px; font-weight: 600; cursor: pointer; margin: 8px 4px; text-decoration: none; }
.btn-print:hover { background: #0284c7; }
`;

function escapeHtml(s) {
  if (s == null) return "";
  return String(s)
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;")
    .replace(/'/g, "&#39;");
}

function fmtEur(v) {
  return Math.round(v).toLocaleString("fr-FR") + " EUR";
}

function fmtDate(d) {
  const dd = String(d.getUTCDate()).padStart(2, "0");
  const mm = String(d.getUTCMonth() + 1).padStart(2, "0");
  return `${dd}/${mm}/${d.getUTCFullYear()}`;
}

function devisNumber(seed) {
  const ts = new Date().toISOString().slice(0, 10).replace(/-/g, "");
  const short = (seed || "PUBLIC").replace(/[^A-Z0-9]/gi, "").slice(0, 8).toUpperCase().padEnd(4, "X");
  return `DEV-${ts}-${short}`;
}

function renderDevis(input) {
  const days = Number(input.days);
  const tjm = Number(input.tjm);
  const total = days * tjm;
  const missionType = input.mission_type;
  const missionLabel = MISSION_TYPES[missionType] || MISSION_TYPES["autre"];
  const today = new Date();
  const validUntil = new Date(today.getTime() + 30 * 86400000);
  const num = devisNumber(input.email || input.name);

  let totalDays = 0;
  const rows = PHASE_RATIOS.map((p, idx) => {
    const phaseDays = +(days * p.ratio).toFixed(2);
    const phasePrice = Math.round(total * p.ratio);
    totalDays += phaseDays;
    return `<tr>
      <td>Phase ${idx + 1}</td>
      <td>${escapeHtml(p.name)}</td>
      <td style="text-align:center">${phaseDays}</td>
      <td style="text-align:right">${fmtEur(phasePrice)}</td>
    </tr>`;
  }).join("\n");

  const clientName = input.name ? escapeHtml(input.name) : "A completer";
  const clientEmail = input.email ? escapeHtml(input.email) : "";

  return `<!DOCTYPE html>
<html lang="fr">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Devis ${num} | SNB Consulting</title>
<style>${CSS_PRINT}</style>
</head>
<body>
<div class="no-print" style="text-align:center;margin-bottom:20px">
    <button class="btn-print" onclick="window.print()">Imprimer / PDF</button>
    <a class="btn-print" href="/devis-instant.html" style="background:#64748b">Nouveau devis</a>
</div>

<div class="header">
    <div class="header-left">
        <h1>${COMPANY.name}</h1>
        <p>${COMPANY.owner} - ${COMPANY.status}</p>
        <p>${COMPANY.email}</p>
    </div>
    <div class="header-right">
        <strong>DEVIS INDICATIF</strong><br>
        N. ${num}<br>
        Date : ${fmtDate(today)}<br>
        Validite : ${fmtDate(validUntil)}
    </div>
</div>

<div class="doc-title">
    <span class="badge badge-devis">DEVIS INDICATIF</span>
    <h2>${escapeHtml(missionLabel)}</h2>
    <div class="doc-num">Reference : ${num}</div>
</div>

<div class="notice">
    Ce devis est <strong>indicatif</strong> et a ete genere en quelques secondes a partir de
    parametres declaratifs. Il est confirme apres echange de cadrage de 30 minutes.
</div>

<div class="info-grid">
    <div class="info-box">
        <h3>Prestataire</h3>
        <p><strong>${COMPANY.owner}</strong><br>
        ${COMPANY.name}<br>
        ${COMPANY.email}<br>
        ${COMPANY.address}<br>
        ${COMPANY.status}</p>
    </div>
    <div class="info-box">
        <h3>Demandeur</h3>
        <p><strong>${clientName}</strong>${clientEmail ? "<br>" + clientEmail : ""}<br>
        TJM applique : ${fmtEur(tjm)} / jour<br>
        Volume estime : ${days} jour(s)</p>
    </div>
</div>

<table>
    <thead>
        <tr>
            <th style="width:80px">Phase</th>
            <th>Description</th>
            <th style="width:80px;text-align:center">Jours</th>
            <th style="width:120px;text-align:right">Montant HT</th>
        </tr>
    </thead>
    <tbody>
        ${rows}
        <tr class="total-row">
            <td colspan="2" style="text-align:right">TOTAL HT</td>
            <td style="text-align:center">${totalDays.toFixed(2)}</td>
            <td style="text-align:right">${fmtEur(total)}</td>
        </tr>
    </tbody>
</table>

<div class="section">
    <h3>Conditions</h3>
    <ul>
        <li>${COMPANY.tva}</li>
        <li>Acompte de 30% a la commande, solde a la livraison</li>
        <li>Devis valable 30 jours</li>
        <li>Cadrage final apres echange de 30 minutes</li>
        <li>Reponse personnalisee sous 10 minutes par le robot SNB</li>
    </ul>
</div>

<div class="footer">
    ${COMPANY.name} - ${COMPANY.owner} - ${COMPANY.status} | ${COMPANY.email}
</div>
</body>
</html>`;
}

export default async (req) => {
  if (req.method !== "POST") {
    return new Response("Method Not Allowed", { status: 405 });
  }

  let body;
  try {
    body = await req.json();
  } catch {
    return new Response(JSON.stringify({ error: "Invalid JSON body" }), {
      status: 400,
      headers: { "Content-Type": "application/json" },
    });
  }

  // Validation stricte
  const days = Number(body.days);
  const tjm = Number(body.tjm);
  if (!Number.isFinite(days) || days < 0.5 || days > 60) {
    return new Response(JSON.stringify({ error: "days must be between 0.5 and 60" }), {
      status: 400, headers: { "Content-Type": "application/json" },
    });
  }
  if (!Number.isFinite(tjm) || tjm < 200 || tjm > 2500) {
    return new Response(JSON.stringify({ error: "tjm must be between 200 and 2500" }), {
      status: 400, headers: { "Content-Type": "application/json" },
    });
  }
  if (!body.mission_type || !MISSION_TYPES[body.mission_type]) {
    return new Response(JSON.stringify({ error: "mission_type invalid" }), {
      status: 400, headers: { "Content-Type": "application/json" },
    });
  }
  // Email/name optionnels mais bornes
  const name = body.name ? String(body.name).slice(0, 80) : "";
  const email = body.email ? String(body.email).slice(0, 120) : "";

  const html = renderDevis({
    mission_type: body.mission_type,
    days,
    tjm,
    name,
    email,
  });

  return new Response(html, {
    status: 200,
    headers: {
      "Content-Type": "text/html; charset=utf-8",
      "Cache-Control": "no-store",
    },
  });
};

export const config = {
  path: "/api/devis-generate",
};
