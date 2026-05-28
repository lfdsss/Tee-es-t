"""Server-side HTML page templates for SEO-crawlable routes.

These pages are served to bots (Googlebot, Bingbot) and as deep-link targets.
The React SPA handles actual user interaction — these ensure crawlers see
rich, indexable content instead of a blank `<div id="root">`.

Design principles:
  - Self-contained: zero external CSS/JS dependencies (survives CDN outages)
  - Fast: inline critical CSS, no render-blocking resources
  - Schema.org: JobPosting JSON-LD embedded directly in <head>
  - Canonical: always point to the canonical URL to avoid duplicate content
  - Open Graph: social sharing preview cards
"""

from __future__ import annotations

from ..models import ContractType, Offer
from .schema_org import build_job_posting_schema, schema_to_script_tag
from .slug import offer_slug

_BASE_CSS = """
*{box-sizing:border-box;margin:0;padding:0}
body{font-family:system-ui,-apple-system,sans-serif;background:#0b0d10;color:#e6e9ef;line-height:1.6}
a{color:#6ee7f7;text-decoration:none}a:hover{text-decoration:underline}
.wrap{max-width:900px;margin:0 auto;padding:1.5rem}
header{border-bottom:1px solid #1e2530;padding-bottom:1rem;margin-bottom:1.5rem}
.logo{font-size:1.4rem;font-weight:700;color:#fff}
.badge{display:inline-block;padding:.2rem .6rem;border-radius:6px;font-size:.75rem;font-weight:600;margin:.25rem}
.badge-internship{background:#3b3a56;color:#a78bfa}
.badge-part_time{background:#1a3550;color:#6ee7f7}
.badge-cdd{background:#1e3a2a;color:#6ee7b7}
.badge-cdi{background:#2a1e3a;color:#d4a8ff}
.badge-apprenticeship{background:#3a2a1e;color:#fbbf24}
.badge-freelance{background:#3a1e2a;color:#f87171}
.badge-other{background:#222;color:#9aa4b2}
.card{background:#12161c;border:1px solid #1e2530;border-radius:12px;padding:1.5rem;margin-bottom:1rem}
.offer-title{font-size:1.6rem;font-weight:700;margin-bottom:.5rem}
.offer-meta{color:#9aa4b2;font-size:.9rem;margin-bottom:1rem}
.section-title{font-size:1.1rem;font-weight:600;margin-bottom:.75rem;color:#aab4c2}
.skills{display:flex;flex-wrap:wrap;gap:.35rem;margin-bottom:1rem}
.skill{background:#1a2535;color:#6ee7f7;padding:.2rem .55rem;border-radius:5px;font-size:.8rem}
.desc{color:#b0bec5;white-space:pre-line;margin-bottom:1rem}
.cta{display:inline-block;background:#2563eb;color:#fff;padding:.7rem 1.5rem;border-radius:8px;font-weight:600;margin-top:.5rem}
.cta:hover{background:#1d4ed8;text-decoration:none}
.grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(280px,1fr));gap:1rem}
.city-card{background:#12161c;border:1px solid #1e2530;border-radius:10px;padding:1rem}
.city-card h3{font-size:1rem;font-weight:600;margin-bottom:.3rem}
.city-card p{color:#9aa4b2;font-size:.85rem}
footer{border-top:1px solid #1e2530;margin-top:2rem;padding-top:1rem;color:#9aa4b2;font-size:.85rem;text-align:center}
"""


def _html_shell(
    *,
    title: str,
    description: str,
    canonical: str,
    og_image: str = "",
    schema_tag: str = "",
    body: str,
    platform_url: str = "https://studentflow.fr",
) -> str:
    og_block = f"""
  <meta property="og:title" content="{title}">
  <meta property="og:description" content="{description}">
  <meta property="og:url" content="{canonical}">
  <meta property="og:type" content="website">
  {"<meta property='og:image' content='" + og_image + "'>" if og_image else ""}
  <meta name="twitter:card" content="summary">
  <meta name="twitter:title" content="{title}">
  <meta name="twitter:description" content="{description}">
"""
    return f"""<!doctype html>
<html lang="fr">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width,initial-scale=1">
  <title>{title}</title>
  <meta name="description" content="{description}">
  <link rel="canonical" href="{canonical}">
  {og_block}
  {schema_tag}
  <style>{_BASE_CSS}</style>
</head>
<body>
<div class="wrap">
  <header>
    <a href="{platform_url}" class="logo">StudentFlow</a>
  </header>
  {body}
  <footer>
    <p>StudentFlow &mdash; La plateforme de jobs étudiants en France.
    <a href="{platform_url}/emplois">Voir toutes les offres</a> &middot;
    <a href="{platform_url}/pour-les-entreprises">Publier une offre</a></p>
  </footer>
</div>
</body>
</html>"""


def render_offer_page(
    offer: Offer,
    *,
    slug: str | None = None,
    platform_url: str = "https://studentflow.fr",
    api_url: str = "https://api.studentflow.fr",
) -> str:
    """Full HTML page for a single job offer — the most important SEO page type."""
    slug = slug or offer_slug(offer)
    page_url = f"{platform_url}/offres/{slug}"
    canonical = page_url

    title_seo = f"{offer.title} — {offer.company or 'Entreprise'} — {offer.city.title() or 'France'} | StudentFlow"
    desc_seo = (
        f"{offer.title} chez {offer.company or 'une entreprise'} à {offer.city.title() or 'France'}. "
        f"Postulez en 1 clic sur StudentFlow, la plateforme jobs étudiants."
    )[:160]

    schema = build_job_posting_schema(
        offer, page_url=page_url, platform_url=platform_url
    )
    schema_tag = schema_to_script_tag(schema)

    contract_label = offer.contract.value
    badge = f'<span class="badge badge-{contract_label}">{contract_label.replace("_", " ").title()}</span>'

    remote_badge = '<span class="badge badge-part_time">Télétravail</span>' if offer.remote else ""

    skills_html = ""
    if offer.skills:
        skills_html = (
            '<div class="skills">'
            + "".join(f'<span class="skill">{s}</span>' for s in offer.skills[:15])
            + "</div>"
        )

    desc_text = offer.description[:2000] if offer.description else "Description non disponible."

    hours_info = f" · {offer.hours_per_week}h/sem" if offer.hours_per_week else ""

    apply_btn = ""
    if offer.url:
        apply_btn = f'<a href="{offer.url}" class="cta" target="_blank" rel="noopener">Postuler maintenant →</a>'
    else:
        apply_btn = f'<a href="{platform_url}/signup" class="cta">Créer mon profil et postuler</a>'

    body = f"""
  <article class="card" itemscope itemtype="https://schema.org/JobPosting">
    <div class="offer-title" itemprop="title">{offer.title}</div>
    <div class="offer-meta">
      {badge} {remote_badge}
      &nbsp;{offer.company or "Entreprise"}&nbsp;&middot;&nbsp;
      {offer.city.title() or "France"}{hours_info}
    </div>

    {skills_html}

    <h2 class="section-title">Description du poste</h2>
    <div class="desc">{desc_text}</div>

    {apply_btn}
  </article>

  <section style="margin-top:2rem">
    <h2 class="section-title">Offres similaires</h2>
    <p style="color:#9aa4b2">
      <a href="{platform_url}/emplois/{_city_slug(offer.city)}">
        Voir toutes les offres à {offer.city.title() or 'France'}
      </a>
    </p>
  </section>
"""

    return _html_shell(
        title=title_seo,
        description=desc_seo,
        canonical=canonical,
        schema_tag=schema_tag,
        body=body,
        platform_url=platform_url,
    )


def render_city_page(
    city: str,
    offer_previews: list[dict],
    *,
    skill_filter: str | None = None,
    platform_url: str = "https://studentflow.fr",
) -> str:
    """Programmatic landing page for a city (+ optional skill filter).

    These pages are the long-tail SEO goldmine: "jobs étudiant serveur Paris",
    "baby-sitting Lyon étudiant", etc. Google ranks them based on relevance and
    freshness — and we generate them dynamically from real offer data.
    """
    from .slug import city_slug

    city_display = city.title()
    city_s = city_slug(city)

    if skill_filter:
        title_seo = f"Jobs étudiant {skill_filter.title()} à {city_display} | StudentFlow"
        desc_seo = f"Trouvez des jobs étudiant {skill_filter} à {city_display}. Matching instantané, postulez en 1 clic sur StudentFlow."[:160]
        canonical = f"{platform_url}/emplois/{city_s}/{skill_filter}"
        heading = f"Jobs étudiant <em>{skill_filter.title()}</em> à {city_display}"
    else:
        title_seo = f"Jobs étudiant à {city_display} — Offres à pourvoir | StudentFlow"
        desc_seo = f"Toutes les offres d'emploi étudiant à {city_display}. Stage, alternance, job temps partiel. Matching instantané sur StudentFlow."[:160]
        canonical = f"{platform_url}/emplois/{city_s}"
        heading = f"Jobs étudiant à {city_display}"

    offer_cards = ""
    for op in offer_previews[:30]:
        slug = op.get("slug", "")
        t = op.get("title", "Offre")
        co = op.get("company", "")
        ct = op.get("contract", "other")
        offer_cards += f"""
    <a href="{platform_url}/offres/{slug}" class="city-card" style="display:block;color:inherit">
      <h3>{t}</h3>
      <p>{co} &middot; <span class="badge badge-{ct}" style="font-size:.7rem">{ct}</span></p>
    </a>"""

    no_offers = '<p style="color:#9aa4b2">Aucune offre pour le moment. <a href="/signup">Inscrivez-vous</a> pour être alerté.</p>' if not offer_previews else ""

    body = f"""
  <h1 style="font-size:1.8rem;font-weight:700;margin-bottom:.5rem">{heading}</h1>
  <p style="color:#9aa4b2;margin-bottom:1.5rem">{len(offer_previews)} offre{"s" if len(offer_previews) != 1 else ""} disponible{"s" if len(offer_previews) != 1 else ""}</p>

  <div class="grid">
    {offer_cards}
    {no_offers}
  </div>

  <section style="margin-top:2rem">
    <h2 class="section-title">Autres villes</h2>
    <p><a href="{platform_url}/emplois">Voir toutes les villes →</a></p>
  </section>
"""

    return _html_shell(
        title=title_seo,
        description=desc_seo,
        canonical=canonical,
        body=body,
        platform_url=platform_url,
    )


def render_city_index(
    cities: list[dict],
    *,
    platform_url: str = "https://studentflow.fr",
) -> str:
    """Index page listing all cities with active offers.

    This is the hub page for our programmatic SEO cluster.
    Internal linking: home → /emplois → /emplois/{city} → /offres/{slug}
    """
    city_cards = "".join(
        f"""<div class="city-card">
      <h3><a href="{platform_url}/emplois/{c['slug']}">{c['name']}</a></h3>
      <p>{c['count']} offre{"s" if c['count'] != 1 else ""}</p>
    </div>"""
        for c in cities[:50]
    )

    body = f"""
  <h1 style="font-size:1.8rem;font-weight:700;margin-bottom:.5rem">Jobs étudiants par ville</h1>
  <p style="color:#9aa4b2;margin-bottom:1.5rem">
    Trouvez des offres d'emploi étudiant dans votre ville — stage, alternance, job temps partiel.
  </p>
  <div class="grid">
    {city_cards}
  </div>
"""

    return _html_shell(
        title="Jobs étudiants par ville en France | StudentFlow",
        description="Trouvez des offres d'emploi étudiant dans toutes les villes de France. Stage, alternance, job temps partiel sur StudentFlow.",
        canonical=f"{platform_url}/emplois",
        body=body,
        platform_url=platform_url,
    )


def _city_slug(city: str) -> str:
    from .slug import city_slug
    return city_slug(city)
