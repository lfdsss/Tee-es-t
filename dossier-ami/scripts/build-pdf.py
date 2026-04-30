#!/usr/bin/env python3
"""
Génère les PDF du kit dossier-ami à partir des sources Markdown.

Sortie :
  dossier-ami/pdf/
    ├── 00-INDEX.pdf                  (sommaire + checklist + suivi)
    ├── DOSSIER-COMPLET.pdf           (toutes les pièces dans un seul PDF)
    ├── specimens/
    │   ├── cetelem-email.pdf, cetelem-lrar.pdf
    │   ├── banque-email.pdf, banque-lrar.pdf
    │   ├── operateur-email.pdf, operateur-lrar.pdf
    │   ├── cnil-formulaire.pdf
    │   ├── assurance-email.pdf, assurance-lrar.pdf
    │   └── banque-de-france-email.pdf, banque-de-france-lrar.pdf
    └── templates/
        └── (mêmes fichiers, version templates avec variables)
"""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Iterable

from markdown_pdf import MarkdownPdf, Section


ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT
OUT = ROOT / "pdf"

# CSS sobre, lisible, format A4 imprimable
CSS = """
@page { size: A4; margin: 25mm 22mm 25mm 22mm; }
body { font-family: 'Garamond', Georgia, serif; font-size: 11pt; line-height: 1.45; color: #111; }
h1 { font-size: 18pt; margin: 0 0 12pt 0; padding-bottom: 4pt; border-bottom: 1px solid #333; }
h2 { font-size: 13pt; margin: 14pt 0 6pt 0; color: #222; }
h3 { font-size: 11pt; margin: 10pt 0 4pt 0; color: #333; }
p, li { margin: 4pt 0; }
table { border-collapse: collapse; width: 100%; margin: 6pt 0; font-size: 10pt; }
th, td { border: 1px solid #888; padding: 4pt 6pt; text-align: left; vertical-align: top; }
th { background: #eee; }
code { font-family: 'Courier New', monospace; font-size: 10pt; background: #f4f4f4; padding: 1pt 3pt; }
pre { background: #f4f4f4; padding: 8pt; border-left: 3px solid #888; font-size: 9.5pt; white-space: pre-wrap; }
blockquote { border-left: 3px solid #aaa; padding: 2pt 10pt; color: #444; margin: 6pt 0; }
hr { border: none; border-top: 1px solid #888; margin: 10pt 0; }
strong { color: #000; }
"""


def md_to_pdf(md_files: list[Path], out_pdf: Path, title: str) -> None:
    """Convertit une liste de fichiers Markdown en un seul PDF (concaténation)."""
    out_pdf.parent.mkdir(parents=True, exist_ok=True)
    pdf = MarkdownPdf(toc_level=2, optimize=True)
    pdf.meta["title"] = title
    pdf.meta["author"] = "dossier-ami"

    for md in md_files:
        text = md.read_text(encoding="utf-8")
        pdf.add_section(Section(text), user_css=CSS)

    pdf.save(str(out_pdf))
    rel = out_pdf.relative_to(ROOT)
    size_kb = out_pdf.stat().st_size // 1024
    print(f"  ✓ {rel}  ({size_kb} KB)")


def collect(*paths: str) -> list[Path]:
    """Résout des chemins relatifs à dossier-ami/, ignore ceux qui n'existent pas."""
    out = []
    for p in paths:
        full = SRC / p
        if full.exists():
            out.append(full)
        else:
            print(f"  ⚠  {p} introuvable, ignoré", file=sys.stderr)
    return out


def main() -> None:
    OUT.mkdir(exist_ok=True)
    print(f"→ Source : {SRC}")
    print(f"→ Sortie : {OUT}\n")

    # ── 1. Sommaire / pilotage ──────────────────────────────────────────────
    print("── Pilotage ──")
    md_to_pdf(
        collect("README.md", "CHECKLIST.md", "SUIVI.md"),
        OUT / "00-INDEX.pdf",
        title="Dossier — Index, checklist et suivi",
    )

    # ── 2. Spécimens (un PDF par courrier) ──────────────────────────────────
    print("\n── Spécimens (courriers entièrement rédigés) ──")
    specs_dir = OUT / "specimens"

    organisms = [
        ("cetelem", ["email.md", "lrar.md"]),
        ("banque", ["email.md", "lrar.md"]),
        ("operateur", ["email.md", "lrar.md"]),
        ("cnil", ["formulaire.md"]),
        ("assurance", ["email.md", "lrar.md"]),
        ("banque-de-france", ["email.md", "lrar.md"]),
    ]

    for org, files in organisms:
        for f in files:
            src = SRC / "specimens" / org / f
            if not src.exists():
                continue
            stem = f.replace(".md", "")
            md_to_pdf(
                [src],
                specs_dir / f"{org}-{stem}.pdf",
                title=f"Spécimen — {org} ({stem})",
            )

    # ── 3. Templates (un PDF par courrier) ──────────────────────────────────
    print("\n── Templates (avec variables {NOM}, {DATE}…) ──")
    tpl_dir = OUT / "templates"

    for org, files in organisms:
        for f in files:
            src = SRC / "courriers" / org / f
            if not src.exists():
                continue
            stem = f.replace(".md", "")
            md_to_pdf(
                [src],
                tpl_dir / f"{org}-{stem}.pdf",
                title=f"Template — {org} ({stem})",
            )

    # ── 4. Dossier complet (tout dans un seul PDF) ──────────────────────────
    print("\n── Dossier complet (tout-en-un) ──")
    all_md: list[Path] = []
    all_md += collect("README.md", "CHECKLIST.md", "SUIVI.md")
    all_md += collect("specimens/SPECIMENS.md")

    # Spécimens d'abord (prêts à utiliser), puis templates
    for org, files in organisms:
        for f in files:
            p = SRC / "specimens" / org / f
            if p.exists():
                all_md.append(p)

    for org, files in organisms:
        for f in files:
            p = SRC / "courriers" / org / f
            if p.exists():
                all_md.append(p)

    all_md += collect("prompts/claude-code.md")

    md_to_pdf(
        all_md,
        OUT / "DOSSIER-COMPLET.pdf",
        title="Dossier complet — kit administratif",
    )

    # ── 5. Récap ────────────────────────────────────────────────────────────
    print("\n" + "=" * 60)
    print("  ✓ Génération terminée")
    print("=" * 60)
    pdfs = sorted(OUT.rglob("*.pdf"))
    total_kb = sum(p.stat().st_size for p in pdfs) // 1024
    print(f"\n  {len(pdfs)} PDF générés ({total_kb} KB total)")
    print(f"  Dossier : {OUT.relative_to(ROOT.parent)}")


if __name__ == "__main__":
    main()
