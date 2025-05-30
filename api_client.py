# api_client.py
import time
import xml.etree.ElementTree as ET
import requests
import logging
import os

# Load environment variables (or consider doing this in a central config module)
USERNAME = os.environ.get("API_USERNAME")
PASSWORD = os.environ.get("API_PASSWORD")
HEADERS = {
    "Content-Type": "application/xml",
    "Accept": "application/xml",
}
MAX_RETRIES = 30  # Maximum number of polling attempts
WAIT_TIME = 30    # Wait time (in seconds) between polling attempts

def make_api_request(url, method="POST", auth=None, headers=None):
    """
    Makes an API request (GET or POST) and handles exceptions.
    """
    try:
        if method == "POST":
            response = requests.post(url, auth=auth, headers=headers)
        else:
            response = requests.get(url, auth=auth, headers=headers)
        response.raise_for_status()
        return response
    except requests.exceptions.RequestException as e:
        logging.error(f"API request failed: {e}")
        return None



def get_identifier(customer_id, report_identifier, filter_identifier):
    """
    Retrieves the report identifier for a specific customer and filter.
    Handles failure messages directly from the POST call.
    """
    url = f"https://webapi.collaboratemd.com/v1/customer/{customer_id}/reports/{report_identifier}/filter/{filter_identifier}/run"

    response = make_api_request(url, auth=(USERNAME, PASSWORD), headers=HEADERS)

    if response:
        try:
            root = ET.fromstring(response.text)
            namespace = {"ns1": "http://www.collaboratemd.com/api/v1/"}
            identifier_elem = root.find(".//ns1:Identifier", namespaces=namespace)

            # Extract any failure messages
            status_message_elem = root.find(".//ns1:StatusMessage", namespaces=namespace)
            status_message = status_message_elem.text.strip() if status_message_elem is not None else ""

            # Define failure messages that should be classified as "Success"
            success_failure_messages = [
                "Facility is inactive",
                "Interface is not turned on",
                "No records found",
                "Report not available for this customer"
                "The report completed successfully, but no records were found matching the criteria used."
            ]

            if any(msg.lower() in status_message.lower() for msg in success_failure_messages):
                logging.info(
                    f"Report request for customer {customer_id} is marked as SUCCESS due to: '{status_message}'")
                # print(f"Status Message : {status_message}")
                return "Success"  # Returning Success instead of an identifier

            return identifier_elem.text if identifier_elem is not None else None

        except ET.ParseError as e:
            logging.error(f"XML parsing error: {e}")

    return None  # Failure to get identifier



def poll_for_report(customer_id, identifier):
    """
    Polls the API for the status of a report until completion or failure.
    Now classifies specific failures as success based on predefined conditions.
    """
    url = f"https://webapi.collaboratemd.com/v1/customer/{customer_id}/reports/results/{identifier}"
    print(f"Customer ID {customer_id} and Final Report Identifier : {identifier}")
    namespace = {"ns1": "http://www.collaboratemd.com/api/v1/"}

    # Define failure messages that should be treated as success
    success_failure_messages = [
        "Facility is inactive",
        "Interface is not turned on",
        "No records found",
        "Report not available for this customer",
        "The report completed successfully, but no records were found matching the criteria used."
    ]

    for attempt in range(MAX_RETRIES):
        response = make_api_request(url, auth=(USERNAME, PASSWORD), headers=HEADERS)
        if response:
            try:
                root = ET.fromstring(response.text)
            except ET.ParseError as e:
                logging.error(f"XML parsing error during polling: {e}")
                break

            status_elem = root.find(".//ns1:Status", namespaces=namespace)
            if status_elem is None:
                logging.error("Status element not found in the response.")
                break

            status = status_elem.text
            status_message_elem = root.find(".//ns1:StatusMessage", namespaces=namespace)
            status_message = status_message_elem.text.strip() if status_message_elem is not None else ""

            # Check if status message matches a known failure condition that should be treated as success
            if any(message.lower() in status_message.lower() for message in success_failure_messages):
                logging.info(f"Report for customer_id: {customer_id} is classified as SUCCESS due to: '{status_message}'")
                # print(f"Status Message : {status_message}")
                return "Success"

            # Handle normal success case
            if status in ["REPORT COMPLETE", "SUCCESS"]:
                data_element = root.find(".//Data")
                return data_element.text if data_element is not None else None

            # Handle normal failure case
            elif status == "REPORT RUNNING":
                time.sleep(WAIT_TIME)
            else:
                logging.error(f"Unexpected status: {status}")
                break

    logging.error(f"Max retries reached or report failed for customer_id: {customer_id}.")
    return None
