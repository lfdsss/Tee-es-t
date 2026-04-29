"""SNB Mission Hunter — Email sender via SMTP (Gmail).
P0: Tested SMTP connection with proper error handling.
"""

import smtplib
import logging
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from config import Config

logger = logging.getLogger("snb.email_sender")


def test_smtp_connection(config: Config) -> bool:
    """Test SMTP connection at startup."""
    if not config.smtp_password or config.smtp_password in ("xxxx", ""):
        logger.warning("SMTP_PASSWORD non configure — emails desactives")
        return False
    try:
        with smtplib.SMTP(config.smtp_host, config.smtp_port, timeout=10) as server:
            server.ehlo()
            server.starttls()
            server.ehlo()
            server.login(config.smtp_user, config.smtp_password)
        logger.info("SMTP connection test OK")
        return True
    except Exception as e:
        logger.error(f"SMTP connection test FAILED: {e}")
        return False


def send_proposal_email(config: Config, to_email: str, subject: str,
                        body_html: str, reply_to: str = None) -> bool:
    if not config.smtp_password or config.smtp_password in ("xxxx", ""):
        logger.warning("SMTP_PASSWORD non configure — email non envoye")
        return False

    msg = MIMEMultipart("alternative")
    msg["From"] = f"Baptiste Thevenot <{config.smtp_user}>"
    msg["To"] = to_email
    msg["Subject"] = subject
    if reply_to:
        msg["Reply-To"] = reply_to

    # Plain text fallback
    import re
    plain = re.sub(r'<[^>]+>', '', body_html)
    plain = plain.replace('&nbsp;', ' ').replace('&amp;', '&')

    msg.attach(MIMEText(plain, "plain"))
    msg.attach(MIMEText(body_html, "html"))

    try:
        with smtplib.SMTP(config.smtp_host, config.smtp_port, timeout=15) as server:
            server.ehlo()
            server.starttls()
            server.ehlo()
            server.login(config.smtp_user, config.smtp_password)
            server.sendmail(config.smtp_user, to_email, msg.as_string())
        logger.info(f"Email envoye a {to_email}: {subject}")
        return True
    except Exception as e:
        logger.error(f"Erreur envoi email a {to_email}: {e}")
        return False
