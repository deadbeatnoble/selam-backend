import logging
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from app.config import settings

logger = logging.getLogger(__name__)


def send_appointment_email(*, to_email: str, subject: str, body: str) -> bool:
    if not settings.smtp_host or not to_email:
        logger.info("Email skipped (SMTP not configured). Would send to %s:\n%s", to_email, body[:500])
        return False

    msg = MIMEMultipart()
    msg["From"] = settings.smtp_from
    msg["To"] = to_email
    msg["Subject"] = subject
    msg.attach(MIMEText(body, "plain", "utf-8"))

    try:
        with smtplib.SMTP(settings.smtp_host, settings.smtp_port, timeout=15) as server:
            if settings.smtp_use_tls:
                server.starttls()
            if settings.smtp_user and settings.smtp_password:
                server.login(settings.smtp_user, settings.smtp_password)
            server.sendmail(settings.smtp_from, [to_email], msg.as_string())
        logger.info("Appointment email sent to %s", to_email)
        return True
    except Exception as exc:
        logger.error("Failed to send email to %s: %s", to_email, exc)
        return False
