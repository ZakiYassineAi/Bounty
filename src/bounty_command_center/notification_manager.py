import requests
import smtplib
from email.mime.text import MIMEText
from .config import settings
from .logging_setup import get_logger

log = get_logger(__name__)

class NotificationManager:
    """Manages sending notifications for high-severity findings."""

    def __init__(self):
        self.slack_webhook_url = settings.notifications.slack_webhook_url
        self.smtp_server = settings.notifications.smtp_server
        self.smtp_port = settings.notifications.smtp_port
        self.smtp_user = settings.notifications.smtp_user
        self.smtp_password = settings.notifications.smtp_password
        self.email_to = settings.notifications.email_to

    def send_slack_notification(self, target_name: str, finding_summary: str):
        """Sends a notification to a Slack webhook."""
        if not self.slack_webhook_url:
            log.warning("Slack webhook URL not configured. Skipping notification.")
            return

        message = {
            "text": f"New high-severity finding detected!\n*Target:* {target_name}\n*Finding:* {finding_summary}"
        }
        try:
            response = requests.post(self.slack_webhook_url, json=message)
            response.raise_for_status()
            log.info("Slack notification sent successfully.")
        except requests.exceptions.RequestException as e:
            log.error("Failed to send Slack notification.", error=str(e))

    def send_email_notification(self, target_name: str, finding_summary: str):
        """Sends an email notification."""
        if not self.email_to:
            log.warning("Email recipient not configured. Skipping notification.")
            return

        subject = f"New High-Severity Finding Detected: {target_name}"
        body = f"A new high-severity finding has been detected for target: {target_name}.\n\nFinding: {finding_summary}"
        msg = MIMEText(body)
        msg["Subject"] = subject
        msg["From"] = self.smtp_user
        msg["To"] = self.email_to

        try:
            with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                if self.smtp_user and self.smtp_password:
                    server.login(self.smtp_user, self.smtp_password)
                server.sendmail(self.smtp_user, [self.email_to], msg.as_string())
                log.info("Email notification sent successfully.")
        except Exception as e:
            log.error("Failed to send email notification.", error=str(e))

    def send_high_severity_notification(self, target_name: str, finding_summary: str):
        """Sends notifications for a high-severity finding."""
        log.info("High-severity finding detected, sending notifications...")
        self.send_slack_notification(target_name, finding_summary)
        self.send_email_notification(target_name, finding_summary)
