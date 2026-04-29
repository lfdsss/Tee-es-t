const SUPABASE_URL = 'https://vcchtbjfugzoyzzxbugs.supabase.co';
const SUPABASE_ANON_KEY = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InZjY2h0YmpmdWd6b3l6enhidWdzIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NzUwNDU1OTUsImV4cCI6MjA5MDYyMTU5NX0.gC66cbeZ4Do_TDIyD_vPerp43Ob6zU2dT4l57ibcERc';

const headers = {
  'apikey': SUPABASE_ANON_KEY,
  'Authorization': `Bearer ${SUPABASE_ANON_KEY}`,
  'Content-Type': 'application/json',
};

const RAILWAY_URL = 'https://web-production-610b0.up.railway.app';

function dedup(missions) {
  const seen = new Map();
  for (const m of missions) {
    const key = (m.title || '').trim().toLowerCase();
    if (!key) { seen.set(m.id, m); continue; }
    const existing = seen.get(key);
    if (!existing || (m.score || 0) > (existing.score || 0)) {
      seen.set(key, m);
    }
  }
  return [...seen.values()];
}

export async function fetchMissions({ limit = 50, offset = 0, status, minScore, search, type } = {}) {
  const fetchLimit = limit + 50;
  let url = `${SUPABASE_URL}/rest/v1/missions?select=*&order=found_at.desc&limit=${fetchLimit}&offset=${offset}`;
  if (status && status !== 'all') url += `&status=eq.${status}`;
  if (minScore) url += `&score=gte.${minScore}`;
  if (type && type !== 'all') url += `&type=eq.${type}`;
  const res = await fetch(url, { headers: { ...headers, 'Prefer': 'count=exact' } });
  const total = parseInt(res.headers.get('content-range')?.split('/')[1] || '0');
  let data = await res.json();
  data = dedup(data);
  if (search) {
    const q = search.toLowerCase();
    data = data.filter(m => m.title?.toLowerCase().includes(q) || m.company?.toLowerCase().includes(q) || m.description?.toLowerCase().includes(q));
  }
  return { data: data.slice(0, limit), total };
}

export async function fetchMission(id) {
  const res = await fetch(`${SUPABASE_URL}/rest/v1/missions?id=eq.${id}&select=*`, { headers });
  const data = await res.json();
  return data[0] || null;
}

export async function updateMission(id, updates) {
  const res = await fetch(`${SUPABASE_URL}/rest/v1/missions?id=eq.${id}`, {
    method: 'PATCH', headers: { ...headers, 'Prefer': 'return=representation' }, body: JSON.stringify(updates),
  });
  return res.json();
}

export async function fetchProposals({ limit = 50, missionId } = {}) {
  let url = `${SUPABASE_URL}/rest/v1/proposals?select=*,missions(title,company,source,score)&order=created_at.desc&limit=${limit}`;
  if (missionId) url += `&mission_id=eq.${missionId}`;
  const res = await fetch(url, { headers });
  return res.json();
}

export async function fetchStats() {
  try {
    const res = await fetch(`${RAILWAY_URL}/health`);
    return res.json();
  } catch {
    return { status: 'offline', missions_today: 0, proposals_today: 0, scans_total: 0 };
  }
}

export async function fetchScanLogs(limit = 20) {
  const res = await fetch(`${SUPABASE_URL}/rest/v1/scan_logs?select=*&order=started_at.desc&limit=${limit}`, { headers });
  return res.json();
}

export function getDevisUrl(missionId) {
  return `${RAILWAY_URL}/devis/${missionId}`;
}

export function getProposalPdfUrl(proposalId) {
  return `${RAILWAY_URL}/proposal/${proposalId}/pdf`;
}

export function getProposalPptxUrl(proposalId) {
  return `${RAILWAY_URL}/proposal/${proposalId}/pptx`;
}

export async function sendChatMessage(message, history = []) {
  const res = await fetch(`${RAILWAY_URL}/chat`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ message, history }),
  });
  const data = await res.json();
  if (data.error) throw new Error(data.error);
  return data;
}
