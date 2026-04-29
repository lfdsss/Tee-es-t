"""SMTP email notifier.

Uses the stdlib `smtplib` + `email.message` so we avoid pulling a heavy
SDK. Works with any SMTP provider: Gmail, Fastmail, OVH, SendGrid SMTP
relay, Brevo (ex-Sendinblue), Mailgun, Infomaniak, etc.

The SMTP call is synchronous, so we run it inside `asyncio.to_thread` to
keep the NotifierAgent loop non-blocking.

Two messages live here:
  * `send()` — student notification with Accept / Pass buttons wired to
    signed-token one-click URLs. That's the Uber moment: one tap, employer
    gets a warm lead.
  * `send_employer_relay()` — fires when the student hits Accept. Delivers
    the student's contact info to the employer so they can close the loop.
"""

from __future__ import annotations

import asyncio
import logging
import smtplib
import ssl
from email.message import EmailMessage

from ..config import get_settings
from ..models import Match, Offer, Student
from .base import NotificationChannel

log = logging.getLogger(__name__)


class EmailNotifier(NotificationChannel):
    name = "email"

    def __init__(
        self,
        *,
        host: str,
        port: int,
        username: str,
        password: str,
        from_addr: str,
        use_tls: bool = True,
    ) -> None:
        self.host = host
        self.port = port
        self.username = username
        self.password = password
        self.from_addr = from_addr
        self.use_tls = use_tls

    # ---- student-facing notification -------------------------------------

    async def send(self, *, match: Match, student: Student, offer: Offer) -> None:
        msg = self._build_student_message(match=match, student=student, offer=offer)
        await asyncio.to_thread(self._send_sync, msg)
        log.info(
            "EmailNotifier: sent match %s to %s (%s)",
            match.id,
            student.email,
            offer.title,
        )

    def _build_student_message(
        self, *, match: Match, student: Student, offer: Offer
    ) -> EmailMessage:
        pct = round(match.score * 100)
        reasons_txt = "\n".join(f"  • {r}" for r in match.reasons) or "  (aucun détail)"
        base = get_settings().public_base_url.rstrip("/")
        accept_url = f"{base}/m/{match.token}/accept"
        decline_url = f"{base}/m/{match.token}/decline"
        distance_line = (
            f"  Distance   : {round(match.distance_km)} km\n"
            if match.distance_km is not None
            else ""
        )

        subject = f"[StudentFlow] Match {pct}% — {offer.title or 'offre'}"
        plain_body = (
            f"Salut {student.full_name or 'toi'},\n\n"
            f"Nouveau match StudentFlow :\n\n"
            f"  Titre      : {offer.title or '-'}\n"
            f"  Entreprise : {offer.company or '-'}\n"
            f"  Ville      : {offer.city or '-'}\n"
            f"{distance_line}"
            f"  Score      : {pct}%\n\n"
            f"Pourquoi on pense que ça colle :\n{reasons_txt}\n\n"
            f"👉 Accepter (l'entreprise sera prévenue) : {accept_url}\n"
            f"👋 Passer  : {decline_url}\n\n"
            f"— StudentFlow\n"
            f"Pour ne plus recevoir ces alertes, réponds STOP.\n"
        )
        html_body = _html_student_body(
            pct=pct,
            student=student,
            offer=offer,
            reasons=match.reasons,
            distance_km=match.distance_km,
            accept_url=accept_url,
            decline_url=decline_url,
        )

        msg = EmailMessage()
        msg["Subject"] = subject
        msg["From"] = self.from_addr
        msg["To"] = student.email
        msg.set_content(plain_body)
        msg.add_alternative(html_body, subtype="html")
        return msg

    # ---- employer relay (fires on accept) --------------------------------

    async def send_employer_relay(self, *, match: Match, student: Student, offer: Offer) -> None:
        if not offer.contact_email:
            return
        msg = self._build_employer_message(match=match, student=student, offer=offer)
        await asyncio.to_thread(self._send_sync, msg)
        log.info(
            "EmailNotifier: relayed match %s to employer %s",
            match.id,
            offer.contact_email,
        )

    def _build_employer_message(
        self, *, match: Match, student: Student, offer: Offer
    ) -> EmailMessage:
        pct = round(match.score * 100)
        subject = f"[StudentFlow] Un candidat a accepté: {offer.title}"
        body = (
            f"Bonjour,\n\n"
            f"Un étudiant vient d'accepter votre mission '{offer.title}' "
            f"via StudentFlow. Voici son profil :\n\n"
            f"  Nom     : {student.full_name or '(non renseigné)'}\n"
            f"  Email   : {student.email}\n"
            f"  Ville   : {student.city or '(non renseignée)'}\n"
            f"  Skills  : {', '.join(student.skills) or '(non renseignées)'}\n"
            f"  Match   : {pct}%\n\n"
            f"Vous pouvez le contacter directement par email pour organiser un "
            f"échange.\n\n"
            f"— StudentFlow\n"
        )
        msg = EmailMessage()
        msg["Subject"] = subject
        msg["From"] = self.from_addr
        msg["To"] = offer.contact_email
        msg.set_content(body)
        return msg

    # ---- SMTP plumbing ---------------------------------------------------

    def _send_sync(self, msg: EmailMessage) -> None:
        context = ssl.create_default_context()
        if self.use_tls:
            with smtplib.SMTP(self.host, self.port, timeout=15) as server:
                server.starttls(context=context)
                if self.username and self.password:
                    server.login(self.username, self.password)
                server.send_message(msg)
        else:
            with smtplib.SMTP_SSL(self.host, self.port, context=context, timeout=15) as server:
                if self.username and self.password:
                    server.login(self.username, self.password)
                server.send_message(msg)


def _html_student_body(
    *,
    pct: int,
    student: Student,
    offer: Offer,
    reasons: list[str],
    distance_km: float | None,
    accept_url: str,
    decline_url: str,
) -> str:
    """Minimal inline-styled HTML — gmail/outlook safe, no external CSS."""
    reasons_html = "".join(f"<li>{_escape(r)}</li>" for r in reasons)
    dist_html = (
        f'<tr><td style="color:#9aa4b2">Distance</td><td><strong>{round(distance_km)} km</strong></td></tr>'
        if distance_km is not None
        else ""
    )
    return f"""<!doctype html><html><body style="font-family:Arial,Helvetica,sans-serif;background:#0b0d10;color:#e6e9ef;margin:0;padding:24px">
<div style="max-width:560px;margin:0 auto;background:#12161c;border:1px solid #242a33;border-radius:14px;padding:24px">
  <div style="display:inline-block;background:#7c5cff;color:#fff;padding:4px 12px;border-radius:999px;font-size:12px;font-weight:700">MATCH {pct}%</div>
  <h1 style="margin:12px 0 6px 0;font-size:22px">{_escape(offer.title or "Nouvelle mission")}</h1>
  <p style="margin:0 0 16px 0;color:#9aa4b2">{_escape(offer.company or "")} — {_escape(offer.city or "à distance")}</p>
  <table style="width:100%;border-collapse:collapse;font-size:14px;margin-bottom:16px">
    {dist_html}
  </table>
  <p style="color:#9aa4b2;font-size:13px;margin:0 0 6px 0">Pourquoi ça colle :</p>
  <ul style="margin:0 0 20px 18px;padding:0;color:#e6e9ef;font-size:13px;line-height:1.6">{reasons_html}</ul>
  <div style="text-align:center;margin:24px 0 8px 0">
    <a href="{accept_url}" style="display:inline-block;background:#31c48d;color:#0b0d10;text-decoration:none;padding:14px 28px;border-radius:10px;font-weight:700;font-size:15px;margin-right:8px">✓ J'accepte</a>
    <a href="{decline_url}" style="display:inline-block;background:#1a1f27;color:#9aa4b2;text-decoration:none;padding:14px 28px;border-radius:10px;font-weight:600;font-size:15px;border:1px solid #242a33">Passer</a>
  </div>
  <p style="color:#6b7280;font-size:12px;text-align:center;margin-top:24px">
    Un clic suffit. En acceptant, l'entreprise reçoit tes coordonnées par email et te contacte directement.
  </p>
</div></body></html>"""


def _escape(s: str) -> str:
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;").replace('"', "&quot;")
