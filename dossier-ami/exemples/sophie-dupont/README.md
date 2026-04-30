# Exemple de déploiement — Sophie DUPONT

> ⚠️ **Cas FICTIF** créé uniquement pour démontrer le pipeline du kit.
> Sophie Dupont, l'adresse `8 rue Paul Bert, 69003 Lyon`, le contrat
> Cetelem `CRD-2025-08847291`, le compte Crédit Agricole, la ligne
> Orange et le contrat MAIF n'existent pas. Aucune correspondance avec
> une personne réelle.

## Scénario

Le 9 avril 2026, Sophie reçoit un courrier de **Cetelem** mentionnant un
crédit (réf. `CRD-2025-08847291`) qu'elle n'a jamais souscrit. En
vérifiant ses relevés du **Crédit Agricole Centre-Est**, elle découvre
des prélèvements SEPA mensuels au profit de Cetelem depuis le 5 février
2026 (cumul **1 247,52 €**). Le 12 avril, sa ligne **Orange** a été
coupée 6 heures sans préavis (suspicion de **SIM swap**). Elle saisit
en parallèle la **CNIL** (utilisation non consentie de ses données) et
la **Banque de France** (vérification d'un éventuel fichage FICP).

## Pipeline de déploiement (3 commandes, 30 secondes)

```bash
# 1. Décrire le cas dans un profil JSON (déjà fait : profil.json)
# 2. Lancer la personnalisation
python3 dossier-ami/scripts/personalize.py \
        dossier-ami/exemples/sophie-dupont/profil.json

# 3. Récupérer les courriers prêts à imprimer
ls dossier-ami/exemples/sophie-dupont/pdf/
```

## Ce qui est généré (11 courriers, ~1 MB)

| Organisme        | Email                          | LRAR                           |
| ---------------- | ------------------------------ | ------------------------------ |
| Cetelem          | `pdf/cetelem-email.pdf`        | `pdf/cetelem-lrar.pdf`         |
| Banque (CA)      | `pdf/banque-email.pdf`         | `pdf/banque-lrar.pdf`          |
| Opérateur (Orange)| `pdf/operateur-email.pdf`     | `pdf/operateur-lrar.pdf`       |
| CNIL             | `pdf/cnil-formulaire.pdf`      | (pas de LRAR)                  |
| Assurance (MAIF) | `pdf/assurance-email.pdf`      | `pdf/assurance-lrar.pdf`       |
| Banque de France | `pdf/banque-de-france-email.pdf`| `pdf/banque-de-france-lrar.pdf`|

Les sources Markdown personnalisées sont dans `courriers/<organisme>/`
si tu veux les rééditer avant de regénérer le PDF.

## Comment ça marche en interne

`personalize.py` fait 3 passes sur chaque spécimen :

1. **Identité** — substitution simple (`Jean MARTIN` → `Sophie DUPONT`,
   adresse, email, téléphone).
2. **Marqueurs `[À ADAPTER : <clef>]`** — résolution via `lookup_marker()`
   qui matche la clef sur le profil. Désambiguïsation contextuelle
   (date du courrier reçu vs. date du LRAR vs. date d'envoi) à partir
   des 80 caractères précédant le marqueur **et** du type de document
   (déduit du H1).
3. **Blocs alternatifs `[option A / option B / option C]`** —
   résolution via `choix_editoriaux` du profil, sinon 1ʳᵉ option.

## Pour ton ami — 1 commande

```bash
# 1. Bootstrap : crée le dossier et copie le template
./dossier-ami/scripts/new-dossier.sh <son-prenom>

# 2. Édite le profil avec ses vraies infos
$EDITOR dossier-ami/exemples/<son-prenom>/profil.json

# 3. Génère les courriers + PDFs
./dossier-ami/scripts/new-dossier.sh <son-prenom> --build

# (optionnel) Vérifier l'état
./dossier-ami/scripts/new-dossier.sh <son-prenom> --status

# (optionnel) Ouvrir le dossier PDF
./dossier-ami/scripts/new-dossier.sh <son-prenom> --open
```

Tu obtiens **son dossier complet en PDF**, prêt à imprimer et envoyer.

> Variante "à la main" (sans wrapper) :
> ```bash
> cp dossier-ami/exemples/sophie-dupont/profil.json \
>    dossier-ami/exemples/<son-prenom>/profil.json
> $EDITOR dossier-ami/exemples/<son-prenom>/profil.json
> python3 dossier-ami/scripts/personalize.py \
>         dossier-ami/exemples/<son-prenom>/profil.json
> ```

⚠️ **Confidentialité** : les vrais profils contiennent des données
personnelles. Le `.gitignore` exclut `dossier-ami/exemples/*/` sauf
`sophie-dupont/` (l'exemple public). Pour ton ami, fais le travail en
local sans pousser.

## Limites connues

- **Adresses postales** des médiateurs / organismes : à reverifier sur
  les sites officiels (peuvent évoluer).
- **Choix éditoriaux** : le script choisit la 1ʳᵉ option par défaut.
  Pour forcer un autre choix, ajoute la clef dans
  `profil.json > choix_editoriaux`.
- **Articles légaux** : le squelette légal vaut pour le scénario
  *usurpation d'identité*. Pour un autre scénario (litige conso,
  sinistre, simple demande FICP), il faut **réécrire les sections
  Faits/Demandes** dans les spécimens — les articles cités peuvent ne
  plus être pertinents.
