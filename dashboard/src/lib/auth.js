// Legacy hardcoded credentials — REDACTED 2026-05-07.
// Auth officielle désormais via Supabase Auth (snb-platform-v3).
// Ce dashboard Vite n'est plus déployé en prod.
const USERS = {
  baptiste: { password: 'REDACTED', role: 'tech', name: 'Baptiste Thevenot' },
  sacha: { password: 'REDACTED', role: 'admin', name: 'Sacha Zekri' },
};

export function login(username, password) {
  const user = USERS[username.toLowerCase()];
  if (user && user.password === password) {
    const session = { username: username.toLowerCase(), role: user.role, name: user.name };
    localStorage.setItem('snb_session', JSON.stringify(session));
    return session;
  }
  return null;
}

export function logout() {
  localStorage.removeItem('snb_session');
}

export function getSession() {
  try {
    return JSON.parse(localStorage.getItem('snb_session'));
  } catch {
    return null;
  }
}
