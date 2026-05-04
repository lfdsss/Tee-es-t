"""Unit tests for the France Travail salary parser.

The OAuth + HTTP path is integration-tested against the real API only when
credentials are configured (skipped in CI). What we lock down here is the
structural-text parsing of `salaire.libelle`, since the API ships free-text
strings rather than structured min/max/period fields. The parser is the
fragile piece.
"""

from __future__ import annotations

from studentflow.models import SalaryPeriod
from studentflow.scrapers.france_travail import _parse_salary


def test_parse_salary_hourly_range() -> None:
    lo, hi, period = _parse_salary("Horaire de 11,52 € à 14,00 €")
    assert period == SalaryPeriod.HOURLY
    assert lo == 11.52
    assert hi == 14.00


def test_parse_salary_monthly_range_with_thousands_separator() -> None:
    lo, hi, period = _parse_salary("Mensuel de 1 800,00 Euros à 2 200,00 Euros sur 12 mois")
    assert period == SalaryPeriod.MONTHLY
    assert lo == 1800.0
    assert hi == 2200.0


def test_parse_salary_annual_folds_to_monthly() -> None:
    """30 000€/year → 2 500€/month, period normalised to MONTHLY."""
    lo, hi, period = _parse_salary("Annuel de 30000,00 Euros sur 12 mois")
    assert period == SalaryPeriod.MONTHLY
    assert lo == 2500.0
    assert hi is None


def test_parse_salary_annual_range_folds_both_bounds() -> None:
    lo, hi, period = _parse_salary("Annuel de 24000,00 Euros à 36000,00 Euros")
    assert period == SalaryPeriod.MONTHLY
    assert lo == 2000.0
    assert hi == 3000.0


def test_parse_salary_single_amount() -> None:
    lo, hi, period = _parse_salary("Mensuel de 2000 Euros")
    assert period == SalaryPeriod.MONTHLY
    assert lo == 2000.0
    assert hi is None


def test_parse_salary_unparseable_returns_none() -> None:
    assert _parse_salary("À débattre selon profil") == (None, None, None)
    assert _parse_salary("") == (None, None, None)


def test_parse_salary_handles_euro_symbol_or_word() -> None:
    """Both '€' and 'Euros' must work."""
    _, _, period_eur = _parse_salary("Horaire de 12,00 €")
    _, _, period_word = _parse_salary("Horaire de 12,00 Euros")
    assert period_eur == period_word == SalaryPeriod.HOURLY
