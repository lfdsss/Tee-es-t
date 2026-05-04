const USERS = {
  baptiste: { password: 'snb2026bt', role: 'tech', name: 'Baptiste Thevenot' },
  sacha: { password: 'snb2026sa', role: 'admin', name: 'Sacha Zekri' },
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
