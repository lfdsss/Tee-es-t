# Runbook — Migration LFDS vers WordPress + WooCommerce

> **Scope** : ce document concerne **uniquement** le site vitrine + boutique
> de La Française des Sauces (`l-fds.com`). Il n'a aucun impact sur SNB
> Consulting (`snbbm-consulting.com`) qui reste hébergé sur Netlify, ni sur
> le quiz LFDS (`quiz.l-fds.com`, Netlify + Fly.io) ou le site recettes
> (`recettes.l-fds.com`, Netlify) qui restent autonomes.

## Architecture cible

```
                        ┌─────────────────────────────────┐
                        │  l-fds.com  (WordPress sur O2switch)
                        │  Vitrine + WooCommerce B2C/B2B
                        └─────────────────────────────────┘
                          │             │              │
              embed iframe│   embed     │   embed      │ link sortant
                          ▼             ▼              ▼
        ┌─────────────────────┐ ┌──────────────────┐ ┌──────────────────┐
        │ quiz.l-fds.com      │ │ recettes.l-fds.com│ │ /epicurien       │
        │ Netlify + Fly.io    │ │ Netlify           │ │ /artisan         │
        │ (existant, INTACT)  │ │ (Sprint 3+5)      │ │ /pragmatique     │
        └─────────────────────┘ └──────────────────┘ │ pages WP natives │
                                                     └──────────────────┘
```

---

## Étape 1 — Préparation O2switch (~1h)

### 1.1 Souscription
- Offre **Unique** O2switch (~84 €/an, espace illimité, traffic illimité)
- Domaine principal : `l-fds.com`
- Région datacenter : France (par défaut chez O2switch)

### 1.2 Configuration DNS initiale
**Avant la bascule** : laisser les DNS pointer vers Netlify.
Préparer côté O2switch :
- Espace web vide associé au compte
- Certificat Let's Encrypt à activer dès que les DNS pointeront
- Alias mail `contact@l-fds.com` (forward vers boîte personnelle)

### 1.3 Installation WordPress
- Via Softaculous (one-click installer dans cPanel O2switch)
- WP version 6.x dernière stable
- Préfixe table : changer `wp_` → `lfds_` (sécurité)
- Compte admin avec mot de passe fort (gestionnaire de passwords)
- Activer 2FA admin via plugin **Wordfence Login Security**

---

## Étape 2 — Stack WordPress (~2h)

### 2.1 Plugins à installer

| Plugin | Rôle | Version |
|--------|------|---------|
| **Kadence** (thème) | Thème léger, performant, blocks Gutenberg | dernier |
| **Kadence Blocks** | Blocks supplémentaires (icon-box, accordion, hero) | dernier |
| **WooCommerce** | E-commerce B2C | dernier |
| **Stripe Payments for WooCommerce** | Paiement Stripe (CB, Apple Pay, Google Pay) | officiel |
| **WooCommerce PayPal Payments** | Paiement PayPal | officiel |
| **B2BKing Lite** | Mode B2B (rôles pro, prix HT, demande de compte) | gratuit |
| **Fluent Forms** | Formulaires (devis B2B, contact) | gratuit |
| **Wordfence** | Sécurité (WAF, brute-force, 2FA) | gratuit |
| **WP Rocket** *(optionnel)* | Cache page + minify | payant |
| **Yoast SEO** | SEO on-page, sitemap, meta | gratuit |
| **WP Mail SMTP** | Envoi email fiable (via Brevo/Sendinblue) | gratuit |

### 2.2 Configuration WooCommerce de base
- Devise : EUR
- Pays de vente : France (B2C), UE + Suisse (B2B)
- Taxes : TVA 20% incluse pour B2C, TVA HT pour B2B
- Stock : géré par produit
- Email : `commandes@l-fds.com` via WP Mail SMTP + Brevo (1k emails/mois gratuit)

### 2.3 Mode B2B (B2BKing Lite)
- Rôle WordPress `wholesale_customer` créé
- Page **"Espace Pro"** avec formulaire de demande (Fluent Forms)
- Validation manuelle des comptes pro (admin reçoit email, valide dans WP admin)
- Prix HT affichés pour les comptes pro, TTC pour B2C
- Catalogue B2B éventuellement séparé (ex: vente par carton de 6/12)

---

## Étape 3 — Pages critiques à créer (~3h)

> ⚠️ **Les slugs `/epicurien`, `/artisan`, `/pragmatique` sont
> NON-NÉGOCIABLES** — ce sont les destinations de redirection
> post-quiz codées dans `src/data/quizData.js:128,138,148`. Les
> changer casserait le quiz en production.

### 3.1 Pages vitrine
| Slug | Titre | Contenu |
|------|-------|---------|
| `/` | Accueil | Hero + 3 profils + CTA quiz + recettes mises en avant |
| `/epicurien` | Profil Épicurien | Description gamme + sauces concernées + recettes |
| `/artisan` | Profil Artisan | Description gamme + sauces concernées + recettes |
| `/pragmatique` | Profil Pragmatique | Description gamme + sauces concernées + recettes |
| `/notre-histoire` | À propos | Histoire de la marque, valeurs, équipe |
| `/contact` | Contact | Form Fluent Forms + adresse + horaires |
| `/quiz` | Faire le quiz | Iframe `quiz.l-fds.com` + intro |
| `/recettes` | Nos recettes | Iframe `recettes.l-fds.com` + intro |
| `/espace-pro` | Espace pro B2B | Form demande compte + bénéfices B2B |

### 3.2 Boutique WooCommerce
- Catégories : `Sauces Épicurien`, `Sauces Artisan`, `Sauces Pragmatique`, `Coffrets`
- Chaque produit : photo, description, prix TTC (B2C), prix HT (B2B), stock
- Page `/boutique` (shop par défaut WooCommerce)
- Page `/panier`, `/commande`, `/mon-compte` (auto par WooCommerce)

### 3.3 Embed quiz dans `/quiz`
Coller dans la page WP en bloc HTML :
```html
<iframe
  src="https://quiz.l-fds.com/?embed=1"
  width="100%"
  height="780"
  frameborder="0"
  style="max-width: 720px; margin: 0 auto; display: block; border-radius: 12px;"
  title="Quiz La Française des Sauces"
></iframe>
```
Snippet déjà documenté dans `docs/lfds-quiz-embed.html` (à vérifier après
bascule DNS pour mettre à jour les URLs).

### 3.4 Embed recettes dans `/recettes`
```html
<iframe
  src="https://recettes.l-fds.com/?embed=1"
  width="100%"
  height="900"
  frameborder="0"
  style="max-width: 1080px; margin: 0 auto; display: block; border-radius: 12px;"
  title="Recettes La Française des Sauces"
></iframe>
```

---

## Étape 4 — Bascule DNS (~30min + propagation)

> ⚠️ **À faire à un moment de faible trafic** (lundi matin tôt par ex.)
> et après que tout est testé en preprod O2switch.

### 4.1 Préparation
1. Vérifier tous les contenus migrés (boutique remplie, pages OK, embeds OK)
2. Site WP en mode maintenance désactivé
3. Backup complet du site Netlify actuel (au cas où rollback nécessaire)
4. Certificat Let's Encrypt **prêt à émettre** côté O2switch

### 4.2 Modifications DNS (registrar du domaine `l-fds.com`)

| Sous-domaine | Type | Valeur cible | Avant | Après |
|--------------|------|--------------|-------|-------|
| `l-fds.com` (apex) | A | IP serveur O2switch | Netlify Apex | O2switch |
| `www.l-fds.com` | CNAME | `l-fds.com` | Netlify | O2switch |
| `quiz.l-fds.com` | CNAME | `apex-loadbalancer.netlify.com` | (nouveau) | Netlify |
| `recettes.l-fds.com` | CNAME | `apex-loadbalancer.netlify.com` | (nouveau) | Netlify |

### 4.3 Côté Netlify
- Site quiz : ajouter `quiz.l-fds.com` comme custom domain
- Site recettes : ajouter `recettes.l-fds.com` comme custom domain
- Désactiver le custom domain `l-fds.com` du site Netlify actuel **APRÈS**
  vérification que WP est joignable

### 4.4 Vérification post-bascule
- Attendre 30 min à 4h pour propagation DNS
- `dig l-fds.com` → IP O2switch
- `dig quiz.l-fds.com` → CNAME Netlify
- `dig recettes.l-fds.com` → CNAME Netlify
- HTTPS valide sur les 3 domaines (Let's Encrypt auto-émis)

---

## Étape 5 — Tests end-to-end (~1h)

### 5.1 Vitrine WP
- [ ] Page d'accueil charge < 1.5s (PageSpeed Insights ≥ 80)
- [ ] Pages `/epicurien`, `/artisan`, `/pragmatique` accessibles
- [ ] SSL valide (cadenas vert), pas de mixed content
- [ ] Mobile responsive OK (test sur iPhone et Android réels)

### 5.2 WooCommerce
- [ ] Achat B2C de bout en bout en mode test Stripe
- [ ] Email de confirmation reçu (via Brevo SMTP)
- [ ] Stock décrémenté correctement
- [ ] Demande de compte B2B → email admin → validation manuelle → login pro
- [ ] Connecté en pro : prix HT affichés, accès catalogue B2B

### 5.3 Embeds & flux quiz
- [ ] Page `/quiz` charge l'iframe quiz sans erreur console
- [ ] Soumettre le quiz → redirection vers `/epicurien` (ou autre profil) sur le WP
- [ ] HubSpot reçoit le contact (vérifier dans le portail HubSpot)
- [ ] Page `/recettes` charge l'iframe recettes sans erreur console
- [ ] Cliquer sur "Créer ma recette" → générateur IA fonctionne
- [ ] CTA "Acheter la sauce" depuis une recette → page produit WooCommerce

### 5.4 Régression — autres systèmes (cloisonnement)
- [ ] `snbbm-consulting.com` continue de fonctionner normalement
- [ ] `commercial-agent` cron `*/10` continue à mettre à jour `status.json`
  (`gh run list --workflow=robot.yml`)
- [ ] StudentFlow non impacté (si déployé)

---

## Étape 6 — Migration des données existantes

### 6.1 Si ancien site Netlify avait du contenu produit
Export manuel depuis l'ancien (s'il y avait une boutique) → import CSV
WooCommerce. Sinon, saisie manuelle des produits depuis catalogue physique.

### 6.2 Redirections SEO
Plugin **Redirection** (gratuit) : créer redirections 301 pour toute URL
de l'ancien site qui change.

### 6.3 Sitemap & SEO
- Yoast SEO : générer le sitemap → soumettre à Google Search Console
- Vérifier que `robots.txt` n'interdit rien d'important
- Vérifier balises `og:` et `twitter:` sur les pages produits

---

## Étape 7 — Rollback (si problème majeur)

Si la bascule échoue catastrophiquement :

1. **Revenir sur les DNS** : remettre l'apex `l-fds.com` vers Netlify
   (TTL court à 300s pendant la fenêtre de bascule pour permettre rollback rapide)
2. Garder WP en standby le temps de corriger
3. Le quiz et les recettes ne sont pas affectés (sous-domaines indépendants)

---

## Coûts annuels récurrents

| Poste | Coût | Notes |
|-------|------|-------|
| O2switch Unique | ~84 €/an | Hébergement WP |
| Domaine `l-fds.com` | ~12 €/an | Renouvellement registrar |
| Stripe | 1.4% + 0.25 € / transaction | Pas de frais fixes |
| PayPal | 2.9% + 0.35 € / transaction | Pas de frais fixes |
| Brevo SMTP | 0 € (1k emails/mois gratuit) | Sinon ~7 €/mois |
| Netlify quiz + recettes | 0 € | Tier gratuit suffit |
| Fly.io quiz backend | ~5 €/mois | Existant, inchangé |
| **TOTAL fixe** | **~150-200 €/an** | + commission paiements |

---

## Checklist finale avant go-live

- [ ] WP en preprod totalement fonctionnel
- [ ] Stripe + PayPal en mode test → un achat complet OK
- [ ] Embeds quiz et recettes testés en preprod (avec URL de test)
- [ ] Pages `/epicurien` etc. créées et publiées
- [ ] Backup Netlify actuel téléchargé (au cas où rollback)
- [ ] DNS prêts à modifier (TTL réduit à 300s 24h avant)
- [ ] Fenêtre de maintenance annoncée si trafic significatif
- [ ] Brevo SMTP testé (envoi d'un email test depuis WP)
- [ ] Wordfence configuré + 2FA admin actif
- [ ] Yoast configuré + sitemap soumis à Search Console

---

## Ce qui est explicitement HORS scope de ce runbook

- **SNB Consulting** : reste sur Netlify, alimenté par `commercial-agent`,
  aucune modification.
- **Quiz LFDS frontend** : reste tel quel sur Netlify (`docs/quiz/`).
- **Quiz LFDS backend** : reste sur Fly.io (`fly.toml`, `Dockerfile`).
- **Site recettes** : reste sur Netlify (`recettes/`), Sprint 3+5 livrés.
- **Commercial-agent Python** : aucune dépendance avec WP.
- **StudentFlow** : aucune dépendance avec WP.

Le seul changement opérationnel concerne `l-fds.com` (apex) qui passe de
Netlify à WordPress sur O2switch. Tous les autres systèmes restent
strictement indépendants — c'est la directive de cloisonnement SNB/LFDS
prise au sérieux.
