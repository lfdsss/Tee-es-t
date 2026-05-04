# PROMPT DEPLOIEMENT COMPLET — SNB Mission Hunter

## CONTEXTE

Tu es sur le Mac de Baptiste Thevenot. Tu as accès au terminal, à Chrome, et à tous les outils locaux. Ta mission : déployer le dashboard React sur Netlify et mettre à jour l'agent Python sur Railway. Tout le code est prêt sur GitHub.

---

## ÉTAPE 1 — Récupérer le code depuis GitHub

```bash
cd ~/Downloads
git clone https://github.com/them311/Tee-es-t.git snb-deploy
cd snb-deploy
git checkout claude/review-dev-prompt-ldVyF
```

Vérifie que ces dossiers existent :
- `dashboard/` — React + Vite + Tailwind (le nouveau dashboard)
- `snb-agent/` — Agent Python amélioré (v2 avec tous les fixes)
- `netlify.toml` — Config Netlify à la racine

---

## ÉTAPE 2 — Déployer le Dashboard sur Netlify

### Option A : Netlify CLI (recommandé)

```bash
cd ~/Downloads/snb-deploy/dashboard
npm install
npm run build

# Installer Netlify CLI si pas déjà fait
npm install -g netlify-cli

# Déployer
netlify deploy --prod --dir=dist --site=09972234-27c2-4e8b-9695-6d3b0d974e7b --auth=nfp_LEEuiqsx79MM5fzvv8XYmrTksufWmSNMcf3e
```

Après le deploy, vérifie que https://snb-consulting-platform.netlify.app charge bien la page de login.

### Option B : Connecter GitHub à Netlify (auto-deploy futur)

1. Ouvre Chrome → https://app.netlify.com
2. Va sur le site "snb-consulting-platform" 
3. Site configuration → Build & deploy → Link repository
4. Connecte `them311/Tee-es-t`, branche `claude/review-dev-prompt-ldVyF`
5. Le `netlify.toml` à la racine configure automatiquement :
   - Base: `dashboard`
   - Build: `npm install && npm run build`
   - Publish: `dashboard/dist`

---

## ÉTAPE 3 — Mettre à jour l'Agent sur Railway

L'agent tourne sur Railway depuis le repo `them311/snb-mission-hunter`. Il faut copier les fichiers améliorés.

```bash
# Cloner le repo agent actuel
cd ~/Downloads
git clone https://github.com/them311/snb-mission-hunter.git
cd snb-mission-hunter

# Copier les fichiers améliorés (écraser les anciens)
cp ~/Downloads/snb-deploy/snb-agent/main.py .
cp ~/Downloads/snb-deploy/snb-agent/api.py .
cp ~/Downloads/snb-deploy/snb-agent/config.py .
cp ~/Downloads/snb-deploy/snb-agent/db.py .
cp ~/Downloads/snb-deploy/snb-agent/scorer.py .
cp ~/Downloads/snb-deploy/snb-agent/proposer.py .
cp ~/Downloads/snb-deploy/snb-agent/profile.py .
cp ~/Downloads/snb-deploy/snb-agent/email_sender.py .
cp ~/Downloads/snb-deploy/snb-agent/notifier.py .
cp ~/Downloads/snb-deploy/snb-agent/models.py .
cp ~/Downloads/snb-deploy/snb-agent/requirements.txt .
cp ~/Downloads/snb-deploy/snb-agent/Procfile .
cp ~/Downloads/snb-deploy/snb-agent/railway.toml .

# Copier les scrapers
cp ~/Downloads/snb-deploy/snb-agent/scrapers/*.py scrapers/

# Commit et push
git add -A
git commit -m "v2: P0/P1/P2 fixes — health shared state, SMTP test, CDI penalty, proposal templates"
git push origin main
```

Railway redéploie automatiquement après le push. Vérifie :

```bash
# Attendre ~2 minutes puis tester
curl -s https://web-production-610b0.up.railway.app/health | python3 -m json.tool
```

Tu devrais voir `"status": "running"` avec `last_scan` non null et `scans_total > 0`.

---

## ÉTAPE 4 — Créer la table agent_status dans Supabase

L'agent v2 a besoin d'une nouvelle table pour partager l'état entre processus. Ouvre Chrome → https://supabase.com/dashboard → projet `vcchtbjfugzoyzzxbugs` → SQL Editor, et exécute :

```sql
CREATE TABLE IF NOT EXISTS agent_status (
  id TEXT PRIMARY KEY DEFAULT 'main_agent',
  status TEXT DEFAULT 'stopped',
  scans_total INTEGER DEFAULT 0,
  missions_total INTEGER DEFAULT 0,
  proposals_total INTEGER DEFAULT 0,
  last_scan_at TIMESTAMPTZ,
  updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Permettre l'accès en lecture pour le dashboard (anon key)
ALTER TABLE agent_status ENABLE ROW LEVEL SECURITY;
CREATE POLICY "Allow public read" ON agent_status FOR SELECT USING (true);
CREATE POLICY "Allow service write" ON agent_status FOR ALL USING (true);
```

---

## ÉTAPE 5 — Vérifications finales

### Dashboard
1. Ouvre https://snb-consulting-platform.netlify.app
2. Login avec `baptiste` / `snb2026bt`
3. Vérifie que la page Dashboard affiche les stats
4. Va dans Missions → vérifie que la liste charge
5. Clique sur une mission → vérifie le détail + pipeline
6. Va dans Documents → vérifie les liens de devis
7. Va dans Paramètres → vérifie le statut agent

### Agent Railway
```bash
# Health
curl -s https://web-production-610b0.up.railway.app/health | python3 -m json.tool

# Missions récentes
curl -s "https://web-production-610b0.up.railway.app/missions?limit=5" | python3 -m json.tool

# Devis pour une mission (remplace ID)
# https://web-production-610b0.up.railway.app/devis/{mission_id}
```

### Logs Railway
Ouvre Chrome → https://railway.app → Projet SNB Mission Hunter → Logs
Tu devrais voir :
- "SNB Mission Hunter v2 — Demarrage"
- "Supabase connecte"
- "SMTP connection test OK" (si App Password configuré)
- Des lignes "[source] Nouvelle mission (score XX)" toutes les 5 min

---

## RÉSUMÉ DES AMÉLIORATIONS DÉPLOYÉES

### P0 — Corrections critiques
- `/health` lit l'état réel depuis Supabase (plus de `null`)
- SMTP testé au démarrage, emails envoyés dans le pipeline
- Devis HTML générés et accessibles depuis le dashboard

### P1 — Améliorations
- 14 scrapers actifs dont 3 sources françaises (Codeur.com, Free-Work.com, Talent.com FR)
- Propositions adaptées par type de mission (IA, Web, Data, Consulting, Design)
- Templates de prompts différents selon le type détecté

### P2 — Améliorations
- Dashboard React complet (7 pages, Tailwind, responsive, PWA)
- Pipeline CRM visuel (new → proposal_ready → sent → won/lost)
- Pénalité CDI dans le scoring (-15 points)
- Credentials retirées du code (env vars uniquement)

---

## CREDENTIALS (pour référence, déjà dans Railway env vars)

- Supabase URL : `https://vcchtbjfugzoyzzxbugs.supabase.co`
- Netlify Site ID : `09972234-27c2-4e8b-9695-6d3b0d974e7b`
- Netlify Token : `nfp_LEEuiqsx79MM5fzvv8XYmrTksufWmSNMcf3e`
- Railway URL : `https://web-production-610b0.up.railway.app`
- Dashboard : `https://snb-consulting-platform.netlify.app`

## RÈGLE ABSOLUE

- Les propositions sont au nom de **Baptiste Thevenot, Consultant Web & IA**
- **NE JAMAIS mentionner S&B Consulting** dans les propositions, devis ou candidatures
- TJM : 450€/jour | Taux horaire : 60€/h
- Email : bp.thevenot@gmail.com | Tél : 06 86 50 43 79 | SIRET : 849 022 058
