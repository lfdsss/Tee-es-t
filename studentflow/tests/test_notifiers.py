"""Tests for the notification channels (webhook + null + email build)."""

from __future__ import annotations

import httpx
import pytest
import respx

from studentflow.config import Settings
from studentflow.models import Match
from studentflow.notifiers import build_notifier
from studentflow.notifiers.base import NullNotifier
from studentflow.notifiers.email_smtp import EmailNotifier
from studentflow.notifiers.webhook import WebhookNotifier

from .fixtures import make_offer, make_student


def _match_for(offer_id, student_id) -> Match:  # type: ignore[no-untyped-def]
    return Match(
        offer_id=offer_id,
        student_id=student_id,
        score=0.82,
        reasons=["skills overlap", "same city"],
    )


@pytest.mark.asyncio
async def test_null_notifier_is_noop() -> None:
    offer = make_offer()
    student = make_student()
    match = _match_for(offer.id, student.id)
    await NullNotifier().send(match=match, student=student, offer=offer)  # no raise


@pytest.mark.asyncio
async def test_webhook_notifier_posts_json_payload() -> None:
    offer = make_offer()
    student = make_student()
    match = _match_for(offer.id, student.id)

    url = "https://hooks.example.com/studentflow"
    with respx.mock(assert_all_called=True) as mock:
        route = mock.post(url).mock(return_value=httpx.Response(200, json={"ok": True}))
        await WebhookNotifier(url).send(match=match, student=student, offer=offer)

        assert route.called
        request = route.calls.last.request
        import json

        body = json.loads(request.content)
        assert body["match_id"] == str(match.id)
        assert body["student_email"] == student.email
        assert body["offer_title"] == offer.title
        assert body["score"] == 0.82
        assert body["reasons"] == ["skills overlap", "same city"]


@pytest.mark.asyncio
async def test_webhook_notifier_raises_on_http_error() -> None:
    offer = make_offer()
    student = make_student()
    match = _match_for(offer.id, student.id)

    url = "https://hooks.example.com/studentflow"
    with respx.mock() as mock:
        mock.post(url).mock(return_value=httpx.Response(500))
        with pytest.raises(httpx.HTTPStatusError):
            await WebhookNotifier(url).send(match=match, student=student, offer=offer)


@pytest.fixture
def clean_env(monkeypatch: pytest.MonkeyPatch) -> None:
    """Strip every StudentFlow env var + disable .env loading.

    Required so the build_notifier tests are not polluted by an actual
    developer `.env` file or CI-level secrets.
    """
    for key in (
        "SMTP_HOST",
        "SMTP_PORT",
        "SMTP_USERNAME",
        "SMTP_PASSWORD",
        "SMTP_FROM",
        "SMTP_USE_TLS",
        "NOTIFICATION_WEBHOOK_URL",
    ):
        monkeypatch.delenv(key, raising=False)
    # Force pydantic-settings to ignore any .env file at cwd.
    monkeypatch.setitem(Settings.model_config, "env_file", None)


def test_build_notifier_prefers_email_when_smtp_set(clean_env: None) -> None:
    settings = Settings(
        smtp_host="smtp.example.com",
        smtp_from="alerts@example.com",
        notification_webhook_url="https://hooks.example.com/x",
    )
    channel = build_notifier(settings)
    assert isinstance(channel, EmailNotifier)


def test_build_notifier_falls_back_to_webhook(clean_env: None) -> None:
    settings = Settings(notification_webhook_url="https://hooks.example.com/x")
    channel = build_notifier(settings)
    assert isinstance(channel, WebhookNotifier)


def test_build_notifier_defaults_to_null(clean_env: None) -> None:
    settings = Settings()
    channel = build_notifier(settings)
    assert isinstance(channel, NullNotifier)


def test_email_notifier_builds_message_with_student_name_and_score() -> None:
    offer = make_offer()
    student = make_student()
    match = _match_for(offer.id, student.id)

    notifier = EmailNotifier(
        host="smtp.example.com",
        port=587,
        username="user",
        password="pw",
        from_addr="alerts@example.com",
    )
    msg = notifier._build_student_message(match=match, student=student, offer=offer)
    assert msg["From"] == "alerts@example.com"
    assert msg["To"] == student.email
    assert "82%" in msg["Subject"]
    plain = msg.get_body(preferencelist=("plain",))
    assert plain is not None
    body = plain.get_content()
    assert student.full_name in body
    assert offer.title in body
    assert "skills overlap" in body
    # Accept/decline URLs now embedded in the body.
    assert "/accept" in body
    assert "/decline" in body


def test_email_notifier_builds_html_alternative_with_accept_button() -> None:
    offer = make_offer()
    student = make_student()
    match = _match_for(offer.id, student.id)
    notifier = EmailNotifier(
        host="smtp.example.com",
        port=587,
        username="user",
        password="pw",
        from_addr="alerts@example.com",
    )
    msg = notifier._build_student_message(match=match, student=student, offer=offer)
    html = msg.get_body(preferencelist=("html",))
    assert html is not None
    content = html.get_content()
    assert "J'accepte" in content
    assert match.token in content


def test_email_notifier_builds_employer_relay_message() -> None:
    offer = make_offer(contact_email="hr@acme.fr")
    student = make_student()
    match = _match_for(offer.id, student.id)
    notifier = EmailNotifier(
        host="smtp.example.com",
        port=587,
        username="",
        password="",
        from_addr="alerts@example.com",
    )
    msg = notifier._build_employer_message(match=match, student=student, offer=offer)
    assert msg["To"] == "hr@acme.fr"
    body = msg.get_content()
    assert student.email in body
    assert offer.title in body
