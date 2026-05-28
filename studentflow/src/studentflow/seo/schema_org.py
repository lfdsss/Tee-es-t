"""JobPosting schema.org JSON-LD generator.

Google Jobs aggregates structured job data from pages that include a
<script type="application/ld+json"> block conforming to the JobPosting schema.
This is the single highest-ROI SEO action for a job platform: zero cost,
automatic inclusion in Google Jobs which captures 30-40% of job search queries.

References:
  https://developers.google.com/search/docs/appearance/structured-data/job-posting
  https://schema.org/JobPosting

Tested against Google's Rich Results Test.
"""

from __future__ import annotations

import json
from datetime import datetime, timedelta

from ..models import ContractType, Offer

# Schema.org employmentType mapping.
# Google requires values from the spec: FULL_TIME, PART_TIME, CONTRACTOR,
# TEMPORARY, INTERN, VOLUNTEER, PER_DIEM, OTHER.
_EMPLOYMENT_TYPE_MAP: dict[ContractType, str] = {
    ContractType.INTERNSHIP: "INTERN",
    ContractType.APPRENTICESHIP: "FULL_TIME",  # apprenticeship is treated as full-time contract
    ContractType.CDD: "TEMPORARY",
    ContractType.CDI: "FULL_TIME",
    ContractType.PART_TIME: "PART_TIME",
    ContractType.FREELANCE: "CONTRACTOR",
    ContractType.OTHER: "OTHER",
}


def build_job_posting_schema(
    offer: Offer,
    *,
    page_url: str,
    platform_name: str = "StudentFlow",
    platform_url: str = "https://studentflow.fr",
) -> dict:
    """Return a dict suitable for JSON-LD embedding.

    Includes all Google-required fields. Missing optional fields are omitted
    rather than set to None, which would fail Google's validation.
    """
    scraped_dt = offer.scraped_at if offer.scraped_at else datetime.utcnow()
    date_posted = scraped_dt.strftime("%Y-%m-%d")

    # Default validity: 30 days from posting if no end date on offer.
    if offer.ends_on:
        valid_through = offer.ends_on.strftime("%Y-%m-%dT23:59:59")
    else:
        valid_through = (scraped_dt + timedelta(days=30)).strftime("%Y-%m-%dT23:59:59")

    schema: dict = {
        "@context": "https://schema.org",
        "@type": "JobPosting",
        "title": offer.title,
        "datePosted": date_posted,
        "validThrough": valid_through,
        "employmentType": _EMPLOYMENT_TYPE_MAP.get(offer.contract, "OTHER"),
        "hiringOrganization": {
            "@type": "Organization",
            "name": offer.company or platform_name,
            "sameAs": offer.url or platform_url,
        },
        "description": offer.description or offer.title,
        "url": page_url,
    }

    # Location (required unless remote).
    if offer.remote:
        schema["jobLocationType"] = "TELECOMMUTE"
        # Google still requires applicantLocationRequirements for remote jobs.
        schema["applicantLocationRequirements"] = {
            "@type": "Country",
            "name": "France",
        }
    else:
        job_location: dict = {
            "@type": "Place",
            "address": {
                "@type": "PostalAddress",
                "addressCountry": "FR",
            },
        }
        if offer.city:
            job_location["address"]["addressLocality"] = offer.city.title()
        if offer.latitude and offer.longitude:
            job_location["geo"] = {
                "@type": "GeoCoordinates",
                "latitude": offer.latitude,
                "longitude": offer.longitude,
            }
        schema["jobLocation"] = job_location

    # Skills → keywords (helps Google categorize the listing).
    if offer.skills:
        schema["skills"] = ", ".join(offer.skills[:10])

    # Hours hint.
    if offer.hours_per_week:
        schema["workHours"] = f"{offer.hours_per_week}h par semaine"

    # Availability window.
    if offer.starts_on:
        schema["jobStartDate"] = offer.starts_on.strftime("%Y-%m-%d")

    return schema


def schema_to_script_tag(schema: dict) -> str:
    """Serialize a schema dict to an inline <script type="application/ld+json"> block."""
    payload = json.dumps(schema, ensure_ascii=False, indent=2)
    return f'<script type="application/ld+json">\n{payload}\n</script>'
