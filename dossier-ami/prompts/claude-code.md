# Prompt — Claude Code / Claude CoWork

À copier-coller dans Claude Code (CLI) ou Claude CoWork pour qu'il
**personnalise** le kit (remplir les variables) et **assemble** les
courriers prêts à imprimer / envoyer.

---

## 1. Prompt — Personnalisation

```
Tu es l'assistant administratif d'une personne physique qui doit gérer
un dossier multi-organismes (Cetelem, banque, opérateur télécom, CNIL,
assurance, Banque de France).

Le kit de courriers se trouve dans `dossier-ami/courriers/`. Tous les
templates contiennent des variables au format {NOM_DE_VARIABLE}.

Ta mission :

1. Lire toutes les variables présentes dans les fichiers .md du dossier
   `dossier-ami/courriers/`.
2. Me poser UNE seule fois, en bloc, la liste des variables à renseigner,
   regroupées par catégorie (identité / contrats / faits / demandes).
3. Une fois mes réponses reçues, remplir les variables dans tous les
   fichiers concernés. Si une variable n'est pas pertinente pour un
   organisme, la laisser vide ou supprimer la ligne (à indiquer
   explicitement avant chaque suppression).
4. Conserver le ton neutre, factuel, recevable. Ne JAMAIS ajouter
   d'accusations non documentées (pas de "violation RGPD", "fraude
   caractérisée", "mise en demeure" si non justifié).
5. Mettre à jour `dossier-ami/SUIVI.md` et `dossier-ami/SUIVI.csv` avec
   les bons noms d'organisme, objets, et statut "À envoyer".
6. Me lister à la fin : (a) les fichiers modifiés, (b) les variables
   restées vides volontairement, (c) les pièces à joindre par envoi.

Règles dures :

- Ne pas inventer de faits.
- Ne pas inventer de numéros de contrat / dossier / sinistre.
- Ne pas commiter de données personnelles tant que je n'ai pas validé.
- Si une demande légale (article cité, médiateur, autorité) ne s'applique
  pas au cas concret, la retirer plutôt que la laisser inadaptée.
```

## 2. Prompt — Génération PDF

```
Pour chaque courrier dans `dossier-ami/courriers/<organisme>/`, génère
le PDF correspondant via pandoc :

1. Convertir `email.md` → `email.pdf` (titre = objet, mise en page
   sobre, marge 25 mm).
2. Convertir `lrar.md` → `lrar.pdf` avec un en-tête et un pied de page
   adaptés au courrier postal (police Garamond ou Times, 11 pt,
   interligne 1.15).
3. Créer un index `dossier-ami/INDEX.pdf` qui liste tous les PDF générés
   avec leur date et leur destinataire.

Commande de référence :
  pandoc -o email.pdf email.md \
    --pdf-engine=xelatex \
    -V geometry:margin=25mm \
    -V mainfont="Garamond" \
    -V fontsize=11pt
```

## 3. Prompt — Vérification

```
Avant tout envoi, vérifie pour chaque courrier de
`dossier-ami/courriers/<organisme>/` :

1. Toutes les variables {…} ont été remplacées (zéro variable restante).
2. La date du courrier == aujourd'hui.
3. Les pièces listées dans la section "Pièces jointes" existent
   physiquement dans `dossier-ami/pieces/`.
4. L'adresse du destinataire (LRAR) est cohérente avec l'adresse
   publique de l'organisme (vérifie via une recherche web rapide pour
   confirmer).
5. Le ton reste neutre et factuel — flag toute formulation agressive
   ou juridiquement risquée pour relecture humaine.

Retourne un rapport :
- ✓ courriers prêts à envoyer
- ⚠ courriers avec problèmes (et lesquels)
- ✗ courriers à reprendre
```

## 4. Variables consolidées (à remplir une fois pour tout le kit)

### Identité du déclarant
- `{NOM}` =
- `{PRÉNOM}` =
- `{DATE_NAISSANCE}` =
- `{LIEU_NAISSANCE}` =
- `{ADRESSE_LIGNE_1}` =
- `{CODE_POSTAL}` =
- `{VILLE}` =
- `{EMAIL}` =
- `{EMAIL_PERSO}` (= EMAIL en général)
- `{TÉLÉPHONE}` =

### Cetelem
- `{NUMÉRO_DOSSIER}` =
- `{NUMÉRO_CONTRAT}` =
- `{DATE_SOUSCRIPTION}` =

### Banque
- `{NOM_BANQUE}` =
- `{NUMÉRO_COMPTE}` =
- `{AGENCE_VILLE}` =
- `{EMAIL_SERVICE_RECLAMATIONS_BANQUE}` =
- `{ADRESSE_SERVICE_RECLAMATIONS}` =

### Opérateur
- `{NOM_OPÉRATEUR}` =
- `{NUMÉRO_LIGNE}` =
- `{NUMÉRO_CONTRAT}` (peut différer de Cetelem)
- `{EMAIL_SERVICE_CLIENTS_OPERATEUR}` =
- `{NUMÉRO_TICKET}` =
- `{DATE_APPEL}` =
- `{PRÉNOM_CONSEILLER}` =

### CNIL
- `{NOM_ORGANISME}` (organisme mis en cause) =
- `{ADRESSE_ORGANISME}` =
- `{EMAIL_DPO_SI_CONNU}` =
- `{DATE_PREMIÈRE_DEMANDE}` =

### Assurance
- `{NOM_ASSUREUR}` =
- `{NUMÉRO_CONTRAT}` (assurance) =
- `{NOM_FORMULE}` =
- `{NUMÉRO_SINISTRE}` =
- `{EMAIL_GESTION_SINISTRES_OU_RECLAMATIONS}` =
- `{ADRESSE_SERVICE}` =

### Banque de France
- `{DÉPARTEMENT_OU_VILLE}` =
- `{ADRESSE_SUCCURSALE}` =
- `{EMAIL_DELEGATION_DEPARTEMENTALE_BDF}` =

### Faits & demandes (transversal)
- `{DESCRIPTION_FACTUELLE_DES_FAITS}` =
- `{DEMANDE_PRÉCISE_1}` =
- `{DEMANDE_PRÉCISE_2}` =
- `{DEMANDE_PRÉCISE_3}` =
- `{DATE_DU_JOUR}` = (auto-rempli)
