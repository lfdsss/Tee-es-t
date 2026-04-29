"""SNB Mission Hunter — Notifications (Telegram + Email digest)."""

import logging
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime, timezone
from typing import List, Optional
import aiohttp

from config import Config

logger = logging.getLogger("snb.notifier")


async def notify_telegram(mission: dict, proposal_text: str, config: Config):
    if not config.telegram_bot_token or not config.telegram_chat_id:
        return

    score = mission.get("score", 0)
    emoji = "\U0001f525" if score >= 90 else "\U0001f3af" if score >= 80 else "\U0001f4cb"

    message = (
        f"{emoji} *MISSION* — Score: {score}/100\n\n"
        f"\U0001f4cb *{mission.get('title', '?')}*\n"
        f"\U0001f3e2 {mission.get('company', 'N/A')}\n"
        f"\U0001f4b0 {mission.get('budget_raw', 'Non precise')}\n"
        f"\U0001f517 Source: {mission.get('source', '?')}\n\n"
        f"\U0001f4dd *PROPOSITION PRETE :*\n"
        f"```\n{proposal_text[:1500]}\n```\n\n"
        f"\U0001f517 [Postuler]({mission.get('source_url', '')})\n"
        f"\U0001f4ca [Dashboard](https://snb-consulting-platform.netlify.app)"
    )

    try:
        async with aiohttp.ClientSession() as session:
            resp = await session.post(
                f"https://api.telegram.org/bot{config.telegram_bot_token}/sendMessage",
                json={
                    "chat_id": config.telegram_chat_id,
                    "text": message,
                    "parse_mode": "Markdown",
                    "disable_web_page_preview": True,
                },
            )
            if resp.status != 200:
                body = await resp.text()
                logger.error(f"Telegram error {resp.status}: {body}")
    except Exception as e:
        logger.error(f"Telegram exception: {e}")


def send_email_digest(missions: List[dict], config: Config):
    if not config.smtp_user or not config.smtp_password:
        return
    if not missions:
        return

    good_missions = [m for m in missions if m.get("score", 0) >= config.score_threshold]
    if not good_missions:
        return

    html = f"""<div style="font-family:Inter,sans-serif;max-width:600px;margin:0 auto;">
<h2 style="color:#111;">SNB Mission Hunter — Digest</h2>
<p style="color:#666;">Missions avec score >= {config.score_threshold}</p>"""

    for m in good_missions[:15]:
        score = m.get("score", 0)
        color = "#22c55e" if score >= 90 else "#3b82f6" if score >= 70 else "#f59e0b"
        html += f"""<div style="border:1px solid #eee;padding:16px;margin:8px 0;border-radius:8px;">
<span style="background:{color};color:#fff;padding:2px 8px;border-radius:4px;font-size:12px;font-weight:700;">{score}</span>
<strong style="margin-left:8px;">{m.get('title', '?')}</strong><br>
<span style="color:#666;font-size:13px;">{m.get('company', 'N/A')} — {m.get('budget_raw', '?')} — {m.get('source', '?')}</span><br>
<a href="{m.get('source_url', '#')}" style="color:#3b82f6;font-size:13px;">Voir la mission</a></div>"""

    html += """<p style="color:#999;font-size:12px;margin-top:16px;">
<a href="https://snb-consulting-platform.netlify.app">Dashboard</a></p></div>"""

    msg = MIMEMultipart("alternative")
    msg["Subject"] = f"SNB: {len(good_missions)} mission{'s' if len(good_missions) > 1 else ''} (score >= {config.score_threshold})"
    msg["From"] = config.smtp_user
    msg["To"] = config.email_to
    msg.attach(MIMEText(html, "html"))

    try:
        with smtplib.SMTP(config.smtp_host, config.smtp_port) as server:
            server.starttls()
            server.login(config.smtp_user, config.smtp_password)
            server.send_message(msg)
        logger.info(f"Email digest envoye: {len(good_missions)} missions")
    except Exception as e:
        logger.error(f"Email error: {e}")
