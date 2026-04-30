#!/usr/bin/env python3
"""
Personnalise les spécimens du kit dossier-ami à partir d'un profil JSON.

Usage :
    ./personalize.py <chemin/profil.json>

Le profil contient :
  - identité (nom, prénom, adresse, contact, naissance)
  - références (organismes, contrats, dates, montants)
  - faits (dates clés, actions déjà entreprises)

Le script :
  1. Lit les spécimens dans `dossier-ami/specimens/<organisme>/*.md`
  2. Remplace `Jean MARTIN`, `12 rue des Lilas, 75011 Paris`,
     `jean.martin@example.fr`, `06 12 34 56 78` par les vraies valeurs
  3. Remplace chaque marqueur `[À ADAPTER : <clef>]` par la valeur du
     profil correspondante (ou laisse `[À COMPLÉTER]` si absente)
  4. Écrit les .md personnalisés dans `<dossier_du_profil>/courriers/`
  5. Génère les PDF dans `<dossier_du_profil>/pdf/`

Exemple :
    ./personalize.py dossier-ami/exemples/sophie-dupont/profil.json
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

from markdown_pdf import MarkdownPdf, Section


SCRIPT = Path(__file__).resolve()
ROOT = SCRIPT.parents[1]  # dossier-ami/
SPECIMENS = ROOT / "specimens"

# Spécimen → (nom, fichiers)
ORGANISMS = [
    ("cetelem",          ["email.md", "lrar.md"]),
    ("banque",           ["email.md", "lrar.md"]),
    ("operateur",        ["email.md", "lrar.md"]),
    ("cnil",             ["formulaire.md"]),
    ("assurance",        ["email.md", "lrar.md"]),
    ("banque-de-france", ["email.md", "lrar.md"]),
]

# Identifiants codés en dur dans les spécimens
SPECIMEN_IDENTITY = {
    "Jean MARTIN":             "{full_name}",
    "12 rue des Lilas":        "{address_line_1}",
    "75011 Paris":              "{postal_code} {city}",
    "jean.martin@example.fr":  "{email}",
    "06 12 34 56 78":          "{phone}",
}

PDF_CSS = """
@page { size: A4; margin: 25mm 22mm; }
body { font-family: 'Garamond', Georgia, serif; font-size: 11pt; line-height: 1.45; }
h1 { font-size: 18pt; margin: 0 0 12pt 0; padding-bottom: 4pt; border-bottom: 1px solid #333; }
h2 { font-size: 13pt; margin: 14pt 0 6pt 0; }
h3 { font-size: 11pt; margin: 10pt 0 4pt 0; }
p, li { margin: 4pt 0; }
strong { color: #000; }
blockquote { border-left: 3px solid #aaa; padding: 2pt 10pt; color: #444; }
code { font-family: 'Courier New', monospace; background: #f4f4f4; padding: 1pt 3pt; }
hr { border: none; border-top: 1px solid #888; margin: 10pt 0; }
"""

# Capture [À ADAPTER : <texte>] avec gestion des crochets imbriqués (ex.
# « [À ADAPTER : ou « le [date] » ] »), et la variante courte [À ADAPTER]
# (sans deux-points), qu'on traite à part.
ADAPTER_FULL_RE = re.compile(r"\[À ADAPTER\s*:\s*((?:[^\[\]]|\[[^\]]*\])+)\]")
ADAPTER_BARE_RE = re.compile(r"\[À ADAPTER\](?!\s*:)")


def personalize_text(text: str, profile: dict) -> tuple[str, list[str]]:
    """Substitue identité + marqueurs [À ADAPTER : clef]. Retourne (texte, clefs_manquantes)."""
    ident = profile["identite"]
    facts = profile.get("faits", {})
    refs = profile.get("references", {})

    # 1. Identité (string-replace simple)
    full_name = f"{ident['prenom']} {ident['nom'].upper()}"
    addr = ident["adresse"]
    replacements = {
        "Jean MARTIN":            full_name,
        "12 rue des Lilas":       addr["ligne_1"],
        "75011 Paris":            f"{addr['code_postal']} {addr['ville']}",
        "À Paris":                f"À {addr['ville']}",  # lieu de signature LRAR
        "jean.martin@example.fr": ident["email"],
        "06 12 34 56 78":         ident["telephone"],
    }
    for old, new in replacements.items():
        text = text.replace(old, new)

    # 2. Marqueurs [À ADAPTER : ...] et [À ADAPTER] (sans clef)
    missing: list[str] = []
    last_topic: dict[str, str | None] = {"value": None}

    # Détection du type de document via l'en-tête H1 (les 200 premiers chars)
    head = text[:200].lower()
    if "opérateur" in head or "operateur" in head or "sim swap" in head:
        doc_type = "operateur"
    elif "assurance" in head or "assureur" in head:
        doc_type = "assurance"
    elif "banque de france" in head:
        doc_type = "bdf"
    elif "banque" in head:
        doc_type = "banque"
    elif "cnil" in head:
        doc_type = "cnil"
    else:
        doc_type = "cetelem"

    def replace_full(m: re.Match) -> str:
        raw = m.group(1).strip()
        # Aplatir : retirer retours-ligne et préfixes Markdown blockquote
        key = re.sub(r"\s*\n\s*>?\s*", " ", raw).strip()
        # Mémoriser le sujet pour résoudre un [À ADAPTER] nu suivant
        last_topic["value"] = key
        # Contexte avant le marqueur (80 caractères) pour désambiguïser
        ctx = text[max(0, m.start() - 80):m.start()]
        value = lookup_marker(key, facts, refs, ident, context=ctx, doc_type=doc_type)
        if value is None:
            missing.append(key)
            return f"[À COMPLÉTER : {key}]"
        return str(value)

    # Vue large du document complet pour détecter le contexte global
    # (ex. "Email — Opérateur télécom" en H1 → tout le doc parle de l'opérateur)
    doc_lower = text.lower()
    is_operateur_doc = "opérateur télécom" in doc_lower or "operateur télécom" in doc_lower or "sim swap" in doc_lower
    is_assurance_doc = "— assurance" in doc_lower or "assurance (" in doc_lower or "assureur" in doc_lower
    is_banque_doc = ("— banque (" in doc_lower or "banque (opposition" in doc_lower or "banque (récl" in doc_lower) and not is_assurance_doc
    is_bdf_doc = "banque de france" in doc_lower

    def replace_bare(m: re.Match) -> str:
        # [À ADAPTER] sans clef : désambiguïsation par contexte précédent + global
        ctx = text[max(0, m.start() - 60):m.start()].lower()
        value = None

        # 1. Indices locaux forts (60 char avant)
        if "compte n°" in ctx or "compte numéro" in ctx:
            value = refs.get("banque_compte")
        elif "ligne " in ctx and ("n°" in ctx or "numéro" in ctx) or "ligne n°" in ctx:
            value = refs.get("operateur_ligne")

        # 2. Contrat n° → désambiguïsation par contexte global du document
        elif "contrat n°" in ctx or "contrat numéro" in ctx:
            if is_operateur_doc:
                value = refs.get("operateur_contrat")
            elif is_assurance_doc:
                value = refs.get("assurance_contrat")
            elif is_bdf_doc:
                value = refs.get("cetelem_contrat")  # FICP : on cite le contrat Cetelem
            else:
                value = refs.get("cetelem_contrat")

        # 3. Fallback : dernier marqueur résolu
        else:
            topic = last_topic["value"]
            if topic and "contrat" in topic.lower():
                value = refs.get("cetelem_contrat")
            if value is None:
                value = refs.get("cetelem_contrat")

        if value is None:
            missing.append("(marqueur nu)")
            return "[À COMPLÉTER]"
        return str(value)

    text = ADAPTER_FULL_RE.sub(replace_full, text)
    text = ADAPTER_BARE_RE.sub(replace_bare, text)

    # 3. Blocs alternatifs « [option A / option B / option C] » NON préfixés
    # par À ADAPTER. On garde la 1ʳᵉ option, ou celle indiquée dans
    # `choix_editoriaux` du profil. Multi-ligne et imbriqué `[durée]` toléré.
    # On ignore : URLs, paths, et la mention d'un seul élément (pas de ` / `).
    choix = profile.get("choix_editoriaux", {})
    # Regex : crochets externes, contenu = caractères sans crochets OU
    # un crochet interne simple « [xxx] ». Multiligne ; on retire ensuite
    # les préfixes blockquote « > » lors de la résolution.
    choice_re = re.compile(
        r"\[((?:[^\[\]]|\[[^\[\]]*\])+?)\]",
        re.DOTALL,
    )

    def replace_choice(m: re.Match) -> str:
        raw = m.group(1)
        # Aplatir les retours-ligne et préfixes blockquote pour le matching
        flat = re.sub(r"\s*\n\s*>?\s*", " ", raw).strip()
        # Pas un bloc à choix → on laisse tel quel
        if " / " not in flat:
            return m.group(0)
        # URLs, paths, refs → on laisse
        if flat.startswith(("http", "/", "#", "!")) or "://" in flat:
            return m.group(0)
        # Marqueur À ADAPTER déjà traité plus haut → ne pas re-toucher
        if flat.lower().startswith("à adapter") or flat.startswith("À COMPLÉTER"):
            return m.group(0)
        # Mapping explicite via le profil
        for k_user, v_user in choix.items():
            if k_user.lower() in flat.lower():
                return v_user
        # Sinon : 1ʳᵉ option
        return flat.split(" / ")[0].strip()

    text = choice_re.sub(replace_choice, text)
    return text, missing


def lookup_marker(
    key: str,
    facts: dict,
    refs: dict,
    ident: dict,
    context: str = "",
    doc_type: str = "cetelem",
) -> str | None:
    """Mappe le texte d'un marqueur [À ADAPTER : xxx] vers une valeur du profil.

    `context` = ~80 caractères précédant le marqueur, pour désambiguïser
    les marqueurs génériques comme `[À ADAPTER : date]`.
    `doc_type` = "operateur" | "banque" | "assurance" | "bdf" | "cnil" | "cetelem"
    déduit du H1 du document, pour résoudre les marqueurs comme
    `[À ADAPTER : numéro de contrat]` selon le destinataire.
    """
    k = key.lower()
    ctx = context.lower()

    # ── Désambiguïsation contextuelle des dates ──────────────────────────
    # On se déclenche quand le marqueur est `date` simple (sans précision).
    if k == "date":
        # « courrier Cetelem reçu le » → date du courrier reçu
        if "courrier" in ctx and "reçu" in ctx:
            return facts.get("cetelem_date_courrier")
        if "lrar adressé à cetelem" in ctx or "lrar du" in ctx and "cetelem" in ctx:
            return facts.get("cetelem_date_lrar")
        if "lrar du" in ctx:
            return facts.get("cetelem_date_lrar")
        if "appel du" in ctx:
            return facts.get("operateur_date_appel")
        if "email du" in ctx:
            return facts.get("operateur_date_email") or facts.get("banque_date_premier_contact")
        if "message du" in ctx:
            return facts.get("banque_date_premier_contact")
        if "depuis le" in ctx:
            return facts.get("banque_date_premier_prelevement")
        if "prélèvement du" in ctx:
            return facts.get("banque_date_premier_prelevement")
        if "j'ai reçu de cetelem" in ctx or "reçu de cetelem" in ctx:
            return facts.get("cetelem_date_courrier")
        if "le " in ctx and ("j'ai exercé" in ctx or "j'ai contesté" in ctx or "demande" in ctx):
            return facts.get("cetelem_date_lrar")
        # Fallback : LRAR Cetelem (date la plus souvent référencée)
        return facts.get("cetelem_date_lrar") or facts.get("date_du_jour")

    # Choix éditoriaux (deux phrasings entre slashs) → on garde la 1ʳᵉ option
    # Exemples : "Non / Oui le ... / Partielle", "ou « le [date] »",
    #           "assuré(e) auprès / découvre"
    if " / " in key:
        choice = profile_choice(key, facts.get("choix_editoriaux", {}))
        if choice is not None:
            return choice

    # Dates simples
    if "date du jour" in k:
        return facts.get("date_du_jour")
    if "date de naissance" in k:
        return ident.get("date_naissance")
    if "lieu de naissance" in k:
        return ident.get("lieu_naissance")

    # Numéro de contrat — désambiguïsation via doc_type
    if "numéro de contrat" in k or "numéro figurant" in k or "numéro" == k:
        if doc_type == "operateur":
            return refs.get("operateur_contrat")
        if doc_type == "assurance":
            return refs.get("assurance_contrat")
        return refs.get("cetelem_contrat")
    if ("courrier" in k and "reçu" in k) or ("date du courrier" in k):
        return facts.get("cetelem_date_courrier")
    if "lrar cetelem" in k or "lrar adressé à cetelem" in k:
        return facts.get("cetelem_date_lrar")

    # Banque
    if "numéro de compte" in k:
        return refs.get("banque_compte")
    if "ville de l'agence" in k or k == "agence" or "agence" in k:
        return refs.get("banque_agence")
    if "nom de la banque" in k:
        return refs.get("banque_nom")
    if "email du service réclamations de la banque" in k or "service réclamations de la banque" in k:
        return refs.get("banque_email")
    if "n° de message" in k or "numéro de message" in k or "référence" in k and "message" in k:
        return facts.get("banque_ref_message")
    if "date premier contact" in k:
        return facts.get("banque_date_premier_contact")
    if "numéro de mandat" in k or "rum" in k:
        return refs.get("banque_rum")
    if "date du premier prélèvement" in k or "premier prélèvement" in k:
        return facts.get("banque_date_premier_prelevement")
    if "montant" in k and "cumul" in k:
        return refs.get("banque_montant_cumule")
    if "montant" in k:
        return refs.get("montant_principal")

    # Opérateur
    if "nom de l'opérateur" in k:
        return refs.get("operateur_nom")
    if "numéro de ligne" in k or "ligne" == k:
        return refs.get("operateur_ligne")
    if "email service clients de l'opérateur" in k or "email service clients" in k:
        return refs.get("operateur_email") or refs.get("service_email")
    if "numéro de contrat" in k and "opérateur" in k:
        return refs.get("operateur_contrat")
    if "n° de ticket" in k or "numéro de ticket" in k:
        return refs.get("operateur_ticket")
    if "date" in k and "appel" in k:
        return facts.get("operateur_date_appel")
    if "date" in k and "email" in k:
        return facts.get("operateur_date_email")
    if "durée" in k:
        return facts.get("operateur_duree_coupure")
    if "faits concomitants" in k:
        return facts.get("operateur_faits_concomitants")

    # Assurance
    if "nom de l'assureur" in k:
        return refs.get("assurance_nom")
    if "contrat" in k and "assurance" in k:
        return refs.get("assurance_contrat")

    # Banque de France
    if "succursale" in k:
        return refs.get("bdf_succursale")
    if "email de la succursale" in k:
        return refs.get("bdf_email")

    # Adresses postales / emails de service génériques
    if "email service réclamations" in k:
        return refs.get("service_email")
    if "adresse postale" in k:
        return refs.get("service_adresse")

    # Date génériques
    if k == "date" or "date" in k:
        return facts.get("date_generique") or facts.get("date_du_jour")

    # Pièces jointes / autre
    if k == "autre" or "autre piece" in k or "autres pieces" in k:
        return facts.get("autres_pieces", "—")

    return None


def profile_choice(key: str, choix: dict) -> str | None:
    """Pour un marqueur du type 'A / B / C', retourne le choix utilisateur ou la 1ʳᵉ option."""
    options = [opt.strip() for opt in key.split(" / ")]
    # Match explicite par texte du marqueur dans le profil
    for k_user, v_user in choix.items():
        if k_user.lower() in key.lower():
            return v_user
    # Sinon : 1ʳᵉ option (par défaut)
    return options[0] if options else None


def render_pdf(md_text: str, out_pdf: Path, title: str) -> None:
    out_pdf.parent.mkdir(parents=True, exist_ok=True)
    pdf = MarkdownPdf(toc_level=0, optimize=True)
    pdf.meta["title"] = title
    pdf.add_section(Section(md_text), user_css=PDF_CSS)
    pdf.save(str(out_pdf))


def main() -> None:
    if len(sys.argv) != 2:
        print(__doc__)
        sys.exit(1)

    profile_path = Path(sys.argv[1]).resolve()
    if not profile_path.exists():
        print(f"❌ Profil introuvable : {profile_path}", file=sys.stderr)
        sys.exit(1)

    profile = json.loads(profile_path.read_text(encoding="utf-8"))
    out_dir = profile_path.parent
    md_dir = out_dir / "courriers"
    pdf_dir = out_dir / "pdf"

    full_name = f"{profile['identite']['prenom']} {profile['identite']['nom'].upper()}"
    print(f"→ Profil : {full_name}")
    print(f"→ Sortie : {out_dir.relative_to(ROOT.parent)}\n")

    all_missing: dict[str, list[str]] = {}

    for org, files in ORGANISMS:
        for f in files:
            src = SPECIMENS / org / f
            if not src.exists():
                continue
            text = src.read_text(encoding="utf-8")
            personalized, missing = personalize_text(text, profile)

            stem = f.replace(".md", "")
            md_out = md_dir / org / f
            md_out.parent.mkdir(parents=True, exist_ok=True)
            md_out.write_text(personalized, encoding="utf-8")

            pdf_out = pdf_dir / f"{org}-{stem}.pdf"
            render_pdf(personalized, pdf_out, title=f"{org} ({stem}) — {full_name}")

            tag = " ⚠ " if missing else " ✓ "
            print(f" {tag} {org}/{f}  → {pdf_out.name}"
                  + (f"  (manquants: {len(missing)})" if missing else ""))
            if missing:
                all_missing[f"{org}/{f}"] = missing

    # Récap manquants
    if all_missing:
        print("\n── Marqueurs sans valeur dans le profil ──")
        for src, keys in all_missing.items():
            print(f"  {src}")
            for k in sorted(set(keys)):
                print(f"    • {k}")
        print("\n  → ces champs apparaissent comme [À COMPLÉTER : ...] dans les PDF.")
    else:
        print("\n  ✓ Aucune valeur manquante — dossier prêt à imprimer.")


if __name__ == "__main__":
    main()
