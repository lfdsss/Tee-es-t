"""Autonomous routine prompts for the commercial agent.

Kept as a dependency-free pure-Python module so tests and external tools can
import it without pulling `anthropic` or any SDK. The `autonomous.py` entry
point re-exports `ROUTINES` from here for backwards compatibility.
"""

from __future__ import annotations

BRAND_BIBLE = """
== BRAND BIBLE — La Francaise Des Sauces ==
Produit : sauce beurre aux herbes bio (nom commercial a adapter selon le site l-fds.com)
Ingredients : beurre francais, echalotes, estragon, basilic
Format : pots 200g (24,50 EUR/kg)
Fabrication : artisanale, Occitanie, France
Positionnement : sauce de finition premium — "sublimer sans masquer"
Ton : elegant, subtil, gastronomique, jamais agressif
Vocabulaire : harmonie, secret, exception, finition, terroir, subtilite, raffinement, sublimer, reveler
INTERDIT : ne jamais mentionner "entrecote" ou "sauce d'entrecote"
Fondateur : Baptiste Thevenot (bp.thevenot@gmail.com)
Site : l-fds.com
"""

ROUTINES: dict[str, str] = {
    "email_prospection": f"""Effectue la routine d'envoi d'emails de prospection (10 emails/jour).

{BRAND_BIBLE}

PROCESS :
1. Utilise hubspot_search_contacts pour trouver les contacts avec hs_lead_status = NEW qui n'ont pas encore ete contactes (max 10).
2. Pour chaque contact, identifie le type de prospect :
   - GROSSISTE (Pomona, Davigel, Avigros) : ton pro, chiffres, volumes, CTA = dossier de referencement
   - RESEAU BIO (Naturalia, Satoriz, Biodis) : valeurs partagees, bio, CTA = echantillons
   - GASTRONOMIE (Dalloyau, restaurants) : prestige, artisanal, CTA = degustation
   - TRAITEUR (Receptions Paris) : gain de temps, qualite constante, CTA = echantillonnage
   - ARTISAN (Metzger, Delon) : artisan a artisan, terroir, CTA = echange de produits
3. Pour chaque contact, cree un brouillon Gmail personnalise avec gmail_create_draft :
   - Objet < 50 caracteres, personnalise
   - Corps < 150 mots, adapte au persona
   - Signature : Baptiste Thevenot / La Francaise Des Sauces / l-fds.com
4. Cree une note dans HubSpot avec le contenu de l'email envoye
5. Cree une tache de relance a J+5 dans HubSpot
6. Passe le statut du contact de NEW a OPEN dans HubSpot
7. Resume : combien d'emails crees, pour qui, prochaines relances""",

    "morning": """Effectue la routine du matin :

1. EMAILS : Utilise gmail_search_messages pour chercher les emails non-lus (is:unread) recus dans les dernieres 24h.
   - Ignore les newsletters, spam, notifications automatiques (Uber, Bolt, Apple, Indeed, Nickel, Adobe, etc.)
   - Pour chaque email d'un vrai prospect ou client : lis le thread complet avec gmail_read_thread, puis cree un brouillon de reponse adapte avec gmail_create_draft.

2. CRM : Utilise hubspot_search_contacts pour lister les contacts avec hs_lead_status = OPEN ou IN_PROGRESS.
   - Pour chaque contact dont la derniere interaction date de plus de 3 jours, prepare un brouillon de relance.

3. TACHES : Utilise hubspot_search_contacts pour verifier s'il y a des taches en retard.

4. DEVIS & PROPOSITIONS : Pour chaque prospect qui a exprime un besoin concret ou demande un tarif :
   - Utilise livrables_create_devis pour generer un devis avec les lignes de prestation adaptees.
   - Si le projet est complexe, utilise livrables_create_proposition pour une proposition detaillee.
   - Mentionne le livrable genere dans le brouillon de reponse au client.

5. RESUME : A la fin, donne un resume structure :
   - Nombre d'emails traites
   - Nombre de brouillons crees
   - Nombre de devis/propositions generes
   - Contacts a relancer
   - Actions prioritaires

IMPORTANT : Tu dois TOUJOURS creer des brouillons (gmail_create_draft), JAMAIS envoyer directement. Baptiste validera ensuite.""",
    "followup": """Effectue la routine de relance :

1. Cherche dans HubSpot tous les contacts avec hs_lead_status = OPEN.
2. Pour chacun, verifie dans Gmail s'il y a eu une reponse recente (gmail_search_messages from:email_du_contact).
3. Si pas de reponse depuis plus de 3 jours : cree un brouillon de relance personnalise.
4. Si pas de reponse depuis plus de 7 jours : cree un brouillon de derniere relance avec une offre speciale ou un devis adapte (livrables_create_devis).
5. Si pas de reponse depuis plus de 14 jours : mets le statut a ATTEMPTED_TO_REACH dans HubSpot.
6. Verifie les livrables existants (livrables_list) et mentionne-les dans les relances si pertinent.
7. Resume les actions effectuees, incluant les devis generes.""",
    "weekly_audit": """Effectue l'audit hebdomadaire du CRM :

1. Liste tous les contacts actifs (hs_lead_status != UNQUALIFIED).
2. Identifie :
   - Contacts sans activite depuis plus de 7 jours
   - Deals sans montant defini
   - Contacts sans email
   - Doublons potentiels
3. Pour chaque probleme, propose une action corrective.
4. Genere un rapport complet avec KPIs :
   - Nombre total de contacts actifs
   - Nombre de deals en cours et valeur totale
   - Taux de reponse estime
   - Actions prioritaires pour la semaine""",
}
