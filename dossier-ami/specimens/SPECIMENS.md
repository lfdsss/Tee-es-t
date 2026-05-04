# Spécimens — courriers entièrement rédigés

Ces fichiers sont des **courriers complets**, pas des templates à variables.
La situation décrite est une situation-type fréquente :

> **Scénario** : usurpation d'identité. Une personne tierce s'est servie des
> données personnelles du déclarant pour souscrire un crédit chez Cetelem,
> en faire prélever les échéances sur son compte bancaire, et provoquer
> ensuite un défaut de paiement et un fichage FICP. Des contestations
> connexes touchent l'opérateur télécom (SIM swap suspecté), l'assurance
> (prélèvement non reconnu) et la CNIL (utilisation abusive des données
> personnelles).

## Comment ton ami doit s'en servir (5 minutes par courrier)

1. Lire le courrier en entier — comprendre ce qu'il dit avant de l'envoyer.
2. Faire `Rechercher / Remplacer` dans son éditeur :
   - `Jean MARTIN` → son vrai prénom + nom
   - `12 rue des Lilas, 75011 Paris` → sa vraie adresse
   - `jean.martin@example.fr` → son vrai email
   - `06 12 34 56 78` → son vrai téléphone
   - Toute mention `[À ADAPTER]` → préciser selon son cas
3. Vérifier les **dates** : les remplacer par les vraies dates des faits.
4. Vérifier les **numéros** de contrat / dossier / sinistre.
5. Vérifier les **montants** s'il y en a.
6. Imprimer (LRAR) ou envoyer (email).
7. Logger l'envoi dans `../SUIVI.md`.

## Si la situation de ton ami est différente

Ces spécimens partent d'une situation d'usurpation d'identité. Si le cas
réel est différent (ex. : litige sur un service mal facturé, sinistre
contesté, simple demande FICP de routine), il faut **réécrire la section
"Faits" et "Demandes"** de chaque courrier. Le squelette légal (articles
cités, médiateurs, autorités, délais) reste valable.

## Différences avec `../courriers/`

- `../courriers/` : templates avec variables `{NOM}`, `{DATE}` — neutre,
  réutilisable pour n'importe quel cas.
- `specimens/` : courriers prêts, prose complète — copier-coller,
  remplacer 5-6 informations, envoyer.

Les deux coexistent : utiliser ce qui est le plus rapide selon le cas.
