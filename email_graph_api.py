import requests
import os
import base64


import requests
import os
import base64



def send_email_with_graph_api(access_token, sender_email, recipient_emails, subject, body, attachment_paths=None):
    """
    Sends an email with multiple attachments using Microsoft Graph API.

    Args:
        access_token (str): OAuth 2.0 access token.
        sender_email (str): Sender's email address.
        recipient_emails (list): List of recipient email addresses.
        subject (str): Email subject.
        body (str): Email body.
        attachment_paths (list): List of file paths to attach.

    Returns:
        None
    """
    url = f"https://graph.microsoft.com/v1.0/users/{sender_email}/sendMail"
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json"
    }

    # Prepare recipient list
    to_recipients = [{"emailAddress": {"address": email}} for email in recipient_emails]

    # Base email structure
    email_data = {
        "message": {
            "subject": subject,
            "body": {"contentType": "Text", "content": body},
            "toRecipients": to_recipients
        },
        "saveToSentItems": "true"
    }

    # Process attachments if provided
    attachments = []
    if attachment_paths:
        for attachment_path in attachment_paths:
            if os.path.exists(attachment_path):
                with open(attachment_path, "rb") as attachment_file:
                    file_content = attachment_file.read()
                    file_name = os.path.basename(attachment_path)

                attachment = {
                    "@odata.type": "#microsoft.graph.fileAttachment",
                    "name": file_name,
                    "contentBytes": base64.b64encode(file_content).decode("utf-8")
                }
                attachments.append(attachment)
            else:
                print(f"Warning: Attachment not found: {attachment_path}")

    # If there are attachments, add them to email data
    if attachments:
        email_data["message"]["attachments"] = attachments

    # Send the email
    try:
        response = requests.post(url, json=email_data, headers=headers)
        if response.status_code == 202:
            print("Email sent successfully.")
        else:
            print(f"Failed to send email. HTTP Status: {response.status_code}")
            print(f"Response: {response.text}")
    except requests.exceptions.RequestException as e:
        print(f"Error sending email: {e}")


