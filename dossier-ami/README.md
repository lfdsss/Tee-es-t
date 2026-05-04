# Dossier — Kit de courriers et de suivi

Kit prêt à l'emploi pour gérer un dossier multi-organismes (Cetelem, banque,
opérateur télécom, CNIL, assurance, Banque de France). Tous les courriers
existent en deux versions : **email** et **LRAR** (lettre recommandée avec
accusé de réception).

Le ton est volontairement **neutre, factuel, recevable** — pas de "mise en
demeure" généralisée ni d'accusation RGPD non documentée. Plus crédible, plus
solide en cas de suite contentieuse.

## Structure

```
dossier-ami/
├── README.md                  ← ce fichier
├── CHECKLIST.md               ← pièces à rassembler avant d'envoyer
├── SUIVI.md                   ← tableau de suivi (à tenir à jour)
├── SUIVI.csv                  ← même tableau, format tableur
├── courriers/                 ← templates avec variables {NOM}, {DATE}…
│   ├── cetelem/               ← email.md + lrar.md
│   ├── banque/                ← email.md + lrar.md
│   ├── operateur/             ← email.md + lrar.md
│   ├── cnil/                  ← formulaire.md (pas de LRAR en priorité)
│   ├── assurance/             ← email.md + lrar.md
│   └── banque-de-france/      ← email.md + lrar.md
├── specimens/                 ← courriers ENTIÈREMENT rédigés (scénario
│   │                            usurpation d'identité), à adapter en
│   │                            remplaçant 5-6 informations
│   ├── SPECIMENS.md           ← cover note : comment s'en servir
│   ├── cetelem/               ← email.md + lrar.md
│   ├── banque/                ← email.md + lrar.md
│   ├── operateur/             ← email.md + lrar.md
│   ├── cnil/                  ← formulaire.md
│   ├── assurance/             ← email.md + lrar.md
│   └── banque-de-france/      ← email.md + lrar.md
├── pieces/                    ← pièces jointes du dossier
│   ├── identite/
│   ├── contrats/
│   ├── releves/
│   ├── correspondances/
│   └── preuves/
├── archives/
│   └── recus-envois/          ← scans des AR, preuves de dépôt, captures
├── prompts/
│   └── claude-code.md         ← prompt complet pour Claude Code / CoWork
└── scripts/
    └── init-dossier.sh        ← regénère une arborescence vierge ailleurs
```

## Templates vs spécimens

- **`courriers/`** : templates neutres avec variables `{NOM}`, `{DATE}`, etc.
  Bon si on veut un courrier court et générique, ou si la situation ne
  correspond à aucun scénario type.
- **`specimens/`** : **6 courriers entièrement rédigés** dans le scénario
  *usurpation d'identité → contestation crédit Cetelem + impacts bancaires
  + FICP*. Tout est écrit en prose ; il suffit de remplacer
  `Jean MARTIN`, l'adresse, et les marqueurs `[À ADAPTER]` (numéros de
  contrat, dates, montants). Recommandé pour ce scénario.

## Stratégie d'envoi par organisme

| Organisme        | Canal prioritaire           | LRAR systématique ?       |
| ---------------- | --------------------------- | ------------------------- |
| Cetelem          | Email **+** LRAR            | Oui                       |
| Banque           | Messagerie sécurisée + email | Seulement si non-réponse / anomalie |
| Opérateur télécom | Appel + email              | Seulement si non-réponse / anomalie |
| CNIL             | Formulaire en ligne         | Non — pas en priorité     |
| Assurance        | Email **+** LRAR            | Oui                       |
| Banque de France | Email **+** LRAR            | Oui                       |

## Mode d'emploi (15 min)

1. **Remplir les variables** dans chaque fichier `.md` :
   - `{NOM}`, `{PRÉNOM}`, `{ADRESSE}`, `{EMAIL}`, `{TÉLÉPHONE}`
   - `{NUMÉRO_CONTRAT}`, `{NUMÉRO_CLIENT}`, `{NUMÉRO_DOSSIER}`
   - `{DATE_FAITS}`, `{DESCRIPTION_BREVE_DES_FAITS}`
   - `{DEMANDE_PRÉCISE}` (ce que tu attends concrètement)
2. **Imprimer / convertir** chaque LRAR en PDF (ouvre le `.md` dans Word ou
   Google Docs, mets en page, exporte en PDF).
3. **Envoyer** dans l'ordre : email d'abord, puis LRAR le même jour.
4. **Logger** chaque envoi dans `SUIVI.md` (date, canal, n° de suivi, réponse
   attendue à J+15).
5. **Archiver** les preuves de dépôt dans `archives/recus-envois/`.

## Délais types à surveiller

| Action                         | Délai légal / d'usage |
| ------------------------------ | --------------------- |
| Réponse banque (réclamation)   | 15 jours ouvrés (puis 35 jours)|
| Réponse Cetelem (litige conso) | 2 mois (médiateur saisissable après) |
| Réponse opérateur télécom      | 1 mois (médiateur après) |
| Instruction CNIL               | 3 mois (premier retour) |
| Réponse assurance              | 10 jours ouvrés (avis de réception du sinistre) |
| Banque de France (FICP/FCC)    | Mise à jour sous 1 mois après preuve de régularisation |

## Génération d'un nouveau dossier vierge

Pour ré-utiliser le kit pour quelqu'un d'autre :

```bash
./scripts/init-dossier.sh ~/mes-dossiers/dossier-untel
```

Le script copie la structure, vide les pièces, et garde tous les templates.

## Important

- Ne pas commiter de données personnelles (`.gitignore` exclut `pieces/` et
  `archives/`).
- Ne **rien** signer / envoyer sans relire.
- En cas de doute juridique : **médiateur** d'abord (gratuit), avocat ensuite.
