import requests
import os
import logger as logger

log = logger.logger

webhook_url = os.environ.get("SLACK_WEBHOOK_URL", None)


def send_slack_notification(message: str) -> bool:
    if not webhook_url:
        log.error("SLACK_WEBHOOK_URL is not set.")
        return False
    if not message:
        log.error("Message is empty.")
        return False
    log.debug(f"Sending Slack notification: {message}")

    # Send the notification
    payload = {"text": message}
    try:
        response = requests.post(webhook_url, json=payload)
        response.raise_for_status()
        log.info(f"Slack notification sent: {message}")
    except requests.RequestException as error:
        log.error(f"Failed to send Slack notification: {error}")
        return False
    return True


send_slack_notification("Hello from Shazamify!")
