import requests
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()


def get_access_token():
    """
    Fetches an access token for Microsoft Graph API using credentials from environment variables.

    Returns:
        str: Access token if successful, None otherwise.
    """
    # Fetch details from environment variables
    tenant_id = os.environ.get("TENANT_ID")
    client_id = os.environ.get("CLIENT_ID")
    client_secret = os.environ.get("CLIENT_SECRET")

    if not tenant_id or not client_id or not client_secret:
        print("Error: Missing TENANT_ID, CLIENT_ID, or CLIENT_SECRET in environment variables.")
        return None

    # Graph API Token URL
    url = f"https://login.microsoftonline.com/{tenant_id}/oauth2/v2.0/token"
    data = {
        "grant_type": "client_credentials",
        "client_id": client_id,
        "client_secret": client_secret,
        "scope": "https://graph.microsoft.com/.default"
    }

    # Make the request
    response = requests.post(url, data=data)
    if response.status_code == 200:
        return response.json().get("access_token")
    else:
        print(f"Failed to get access token: {response.status_code}, {response.text}")
        return None
