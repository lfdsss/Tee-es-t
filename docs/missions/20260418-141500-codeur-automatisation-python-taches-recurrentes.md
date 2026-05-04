---
id: "20260418-141500-codeur-automatisation-python-taches-recurrentes"
date_utc: "2026-04-18T14:15:00+00:00"
platform: "codeur"
title: "Automatisation Python de taches commerciales recurrentes"
budget_hint: "1500 EUR"
urgency: "Livraison sous 3 semaines"
---

## Mission (extrait)

```
PME de 15 personnes cherche a automatiser des taches commerciales repetitives :
extraction quotidienne de donnees depuis Gmail (devis recus par email),
consolidation dans un Google Sheet de suivi, generation d'un rapport Excel
hebdomadaire envoye par email a la direction. Volume : 20 a 40 emails
devis par jour. Stack souhaitee : Python. Budget 1500 EUR. Livraison attendue
sous 3 semaines.
```

## Reponse generee

Bonjour,

Mission claire et completement faisable dans votre budget et votre delai.
C'est le genre d'automatisation que je livre regulierement avec Python plus
APIs Google, en moins de 5 jours effectifs.

COMPREHENSION DU BESOIN

Trois briques a articuler :
- Connecteur Gmail qui identifie et parse les emails devis quotidiennement.
- Synchronisation dans Google Sheet avec deduplication.
- Generateur de rapport Excel hebdomadaire envoye automatiquement.

APPROCHE PROPOSEE

- Setup Gmail API avec compte de service ou OAuth dedie (selon votre
  gouvernance email).
- Parser intelligent des pieces jointes PDF et du corps du mail pour
  extraire montant, client, date, objet. Regex plus fallback Claude si la
  mise en forme est heterogene.
- Script Python executable en cron toutes les heures (GitHub Actions ou
  serveur leger OVH / Railway).
- Ecriture idempotente dans Google Sheet avec cle de dedup (hash de
  l'email).
- Rapport hebdomadaire : agregation par commercial, par client, par
  montant, envoye automatiquement le lundi a 8h.

DEVIS

Phase 1 - Cadrage et acces - 0.5 jour - 300 EUR.
Validation du perimetre, creation des acces Google, echantillonnage de 10
emails reels pour calibrer le parser.

Phase 2 - Connecteur Gmail et parser - 1.5 jour - 750 EUR.
Extraction, parsing robuste, tests avec vos donnees reelles.

Phase 3 - Google Sheet et rapport hebdo - 1 jour - 350 EUR.
Synchronisation, deduplication, rapport Excel automatise.

Phase 4 - Recette et documentation - 0.5 jour - 100 EUR.
Tests croises avec votre equipe, runbook de maintenance.

Total : 3.5 jours, 1 500 EUR HT, aligne sur votre budget.

DISPONIBILITE

Demarrage possible la semaine prochaine. Livraison finale en 15 jours
calendaires apres la Phase 1. Je ne facture qu'apres validation de chaque
phase.

Pour demarrer proprement : il me faudrait 10 emails devis anonymises pour
calibrer le parser. Je vous liste les acces Google a creer de votre cote
des que vous me donnez le feu vert.

A votre disposition pour toute question,

Baptiste Thevenot
SNB Consulting
bp.thevenot@gmail.com
