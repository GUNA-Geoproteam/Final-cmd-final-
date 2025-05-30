import os
import logging
from auth import get_access_token
from email_graph_api import send_email_with_graph_api

from dotenv import load_dotenv






import os
import logging
from auth import get_access_token
from email_graph_api import send_email_with_graph_api

def send_log_to_admin(log_file_path):
    """
    Sends the process log file to the ADMIN_EMAIL after processing is completed.
    """
    admin_email = os.getenv("ADMIN_EMAIL")
    sender_email = os.getenv("SENDER_EMAIL")

    if not admin_email:
        logging.error("ADMIN_EMAIL is not set in the .env file. Skipping log email.")
        return

    # Ensure the log file exists and get its absolute path
    if not os.path.isfile(log_file_path):
        logging.error(f"Log file not found: {log_file_path}")
        return

    log_file_path = os.path.abspath(log_file_path)

    # Fetch access token
    access_token = get_access_token()
    if not access_token:
        logging.error("Failed to fetch access token. Log email not sent.")
        return

    subject = "Process Log - Report Extraction"
    body = "Hello,\n\nPlease find attached the latest process log for report extraction.\n\nBest regards,\nNextus Team"

    try:
        # Send email with attachment
        send_email_with_graph_api(
            access_token,
            sender_email,
            [admin_email],
            subject,
            body,
            attachment_paths=[log_file_path]
        )
        logging.info(f"Process log emailed successfully to {admin_email}.")
    except PermissionError:
        logging.error(f"Permission denied: Unable to access {log_file_path}. Check file permissions.")
    except Exception as e:
        logging.error(f"Failed to send process log email: {e}")
