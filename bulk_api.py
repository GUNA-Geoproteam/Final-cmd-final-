# bulk_api.py

import os
import sys
import time
import base64
import zipfile
import io
import logging
import requests
import pandas as pd
import xml.etree.ElementTree as ET
import re
from datetime import datetime

from email_graph_api import send_email_with_graph_api
import os
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
OUTPUT_DIR = os.getenv('OUTPUT_DIR', os.path.join(BASE_DIR, "output_reports"))

REPORT_API_URL = "https://webapi.collaboratemd.com/v1/reports"

def build_bulk_post_url(customer_ids, report_id, filter_id):
    """
    Returns the URL that the bulk-POST will hit, 
    e.g. https://…/reports/10064076/filter/10137003/run?customer=1001&customer=1002
    """
    params = "&".join(f"customer={cid}" for cid in customer_ids)
    return f"{REPORT_API_URL}/{report_id}/filter/{filter_id}/run?{params}"


# ——— Configuration —————————————————————————————————————
# Path to your customer Excel; override via CUSTOMER_EXCEL env-var
EXCEL_FILE      = os.getenv('CUSTOMER_EXCEL', 'data/customer-logo-master.xlsx')
# Directory where each report’s XLSX will be saved
OUTPUT_DIR      = os.getenv('OUTPUT_DIR', 'output_reports')
# Excel columns
CUSTOMER_COLUMN = os.getenv('CUSTOMER_COLUMN', 'customer_id')
ACTIVE_COLUMN   = os.getenv('ACTIVE_COLUMN', 'isActive')
# API
REPORT_API_URL  = os.getenv('REPORT_API_URL', 'https://webapi.collaboratemd.com/v1/reports')
API_USERNAME    = os.getenv('API_USERNAME')
API_PASSWORD    = os.getenv('API_PASSWORD')
XML_HEADERS     = { 'Content-Type': 'application/xml', 'Accept': 'application/xml' }

# Ensure output directory exists
os.makedirs(OUTPUT_DIR, exist_ok=True)

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')






def get_graph_access_token():
    """
    Retrieve the Microsoft Graph access token.
    Replace this with your actual implementation.
    """
    # Example: You might be using MSAL or another mechanism here.
    raise NotImplementedError("Implement get_graph_access_token() to retrieve your MS Graph access token.")

def upload_to_sharepoint(file_path, target_folder):
    """
    Uploads a file to a SharePoint folder using Microsoft Graph.

    Args:
        file_path (str): Local path to the file to upload.
        target_folder (str): SharePoint folder path (e.g. '/sites/YourSite/Shared Documents/YourFolder')
    
    Returns:
        bool: True if the upload succeeds, False otherwise.
    """
    try:
        access_token = get_graph_access_token()
        sharepoint_base_url = os.getenv('SHAREPOINT_BASE_URL')
        if not sharepoint_base_url:
            logging.error("SHAREPOINT_BASE_URL environment variable is not set.")
            return False

        file_name = os.path.basename(file_path)
        # Construct the upload URL; this uses the Microsoft Graph endpoint for OneDrive/SharePoint.
        upload_url = f"{sharepoint_base_url}/drive/root:{target_folder}/{file_name}:/content"
        logging.info(f"Uploading file to SharePoint URL: {upload_url}")

        with open(file_path, 'rb') as f:
            file_contents = f.read()

        headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/octet-stream"
        }
        response = requests.put(upload_url, headers=headers, data=file_contents)
        if response.status_code in (200, 201):
            logging.info("File uploaded successfully to SharePoint.")
            return True
        else:
            logging.error(f"SharePoint upload failed: {response.status_code} {response.text}")
            return False

    except Exception as e:
        logging.error(f"Exception during SharePoint upload: {e}")
        return False






def make_api_request(url, method='POST', auth=None, headers=XML_HEADERS):
    try:
        resp = requests.post(url, auth=auth, headers=headers) if method == 'POST' \
               else requests.get(url, auth=auth, headers=headers)
        resp.raise_for_status()
        return resp
    except requests.RequestException as e:
        logging.error(f"API request failed: {e}")
        return None


import re

def get_identifier(customer_ids, report_id, filter_id):
    filtered = customer_ids.copy()
    bad_ids = []
    recipients = [os.getenv('ADMIN_EMAIL'), os.getenv('LEAD_EMAIL')]

    while True:
        # build the URL from the current filtered list
        url    = build_bulk_post_url(filtered, report_id, filter_id)
        logging.info(f"📤 Bulk POST URL → {url}")

        resp = make_api_request(url, auth=(API_USERNAME, API_PASSWORD))
        if resp is None:
            return None

        text = resp.text.lower()
        # check for any of our “bad customer” signals
        if ("interface is not turned on" in text
         or "no longer active"       in text
         or "invalid criteria"       in text):
            logging.warning("⚠️ Faulty customer detected; isolating…")
            # parse the offending id out of the StatusMessage
            m = re.search(r"customer number\s*(\d+)", resp.text, re.IGNORECASE)
            if m:
                bad = m.group(1)
                if bad in filtered:
                    bad_ids.append(bad)
                    filtered.remove(bad)
                    logging.info(f"🔪 Excluding faulty customer {bad}; retrying…")
                    continue
            # fallback per-customer check
            for cid in customer_ids:
                single_url = build_bulk_post_url([cid], report_id, filter_id)
                single_resp = make_api_request(single_url, auth=(API_USERNAME, API_PASSWORD))
                if single_resp and (
                   'interface is not turned on' in single_resp.text.lower()
                 or 'no longer active'       in single_resp.text.lower()
                 or 'invalid criteria'       in single_resp.text.lower()):
                    bad_ids.append(cid)
                    filtered.remove(cid)
                    logging.info(f"🔪 Excluding faulty customer {cid}; retrying…")
                    break
            else:
                logging.error("❌ Could not isolate faulty customer; aborting.")
                return None
            continue

        # otherwise we got a real Identifier back
        try:
            root = ET.fromstring(resp.text)
            ns   = {'ns1': 'http://www.collaboratemd.com/api/v1/'}
            ident = root.find('.//ns1:Identifier', namespaces=ns)
            run_id = ident.text if ident is not None else None
            logging.info(f"✅ Got run identifier: {run_id} (skipped {bad_ids})")
            return run_id
        except ET.ParseError as e:
            logging.error(f"XML parse error: {e}")
            return None


def poll_for_report(identifier, max_retries=30, wait=30):
    """
    Polls /results/{identifier} until status is COMPLETE or SUCCESS,
    returns the base64‐encoded data string, or None on timeout/error.
    """
    ns = {'ns1': 'http://www.collaboratemd.com/api/v1/'}
    for attempt in range(max_retries):
        url  = f"{REPORT_API_URL}/results/{identifier}"
        resp = make_api_request(url, auth=(API_USERNAME, API_PASSWORD), headers=XML_HEADERS)
        if resp is None:
            return None

        try:
            root   = ET.fromstring(resp.text)
            status = root.find('.//ns1:Status', namespaces=ns).text
            msg    = root.find('.//ns1:StatusMessage', namespaces=ns)
            txt    = msg.text.lower() if msg is not None and msg.text else ''
        except Exception:
            break

        if 'no records were found' in txt:
            logging.info("No records found for identifier")
            return None
        if status in ('REPORT COMPLETE', 'SUCCESS'):
            data = root.find('.//Data')
            return data.text if data is not None else None

        logging.info(f"Report {identifier} status={status}, retrying in {wait}s")
        time.sleep(wait)

    logging.error("Polling timed out or failed.")
    return None


# ────────── ADD THIS BLOCK ──────────

import base64
import zipfile
import io
import pandas as pd

import base64
import zipfile
import io
import pandas as pd
from datetime import datetime
import os
import logging

def process_active_customers(customer_ids, report_identifier, filter_identifier, report_name=None, date_filter=None, destination_folder=None):
    """
    1) Bulk‐run the report for `customer_ids` → run_id
    2) Poll until complete → Base64 ZIP
    3) Write ZIP, extract CSV, dedupe & save XLSX
    Returns dict with paths or raises on error.
    
    If destination_folder is provided, it will be used as the base folder for saving outputs;
    otherwise the default OUTPUT_DIR is used.
    """
    # 1) Kick off the bulk run
    run_id = get_identifier(customer_ids, report_identifier, filter_identifier)
    if not run_id:
        raise RuntimeError("Could not get run identifier")
    
    # 2) Poll for the completed report (Base64‐encoded ZIP)
    raw_b64 = poll_for_report(run_id)
    if not raw_b64:
        raise RuntimeError("Report did not produce any data")
    
    # 3) Decode and prepare folder structure
    zip_bytes = base64.b64decode(raw_b64)
    
    # Use provided destination_folder if available; otherwise use OUTPUT_DIR from environment/default.
    base_output_folder = destination_folder if destination_folder else OUTPUT_DIR

    today = datetime.now()
    year_folder = str(today.year)                      # e.g., '2025'
    month_folder = today.strftime("%b")                 # e.g., 'Apr'
    
    # Log the inputs to check
    logging.info(f"Processing report for: {report_name} with date filter: {date_filter}")
    
    # Construct the report folder name using report_name and date_filter if provided.
    if report_name and date_filter:
        report_folder = f"{report_name} {date_filter}"
    else:
        report_folder = f"{report_identifier}_{filter_identifier}"
    logging.info(f"Report folder: {report_folder}")

    # Final Output Path using the base_output_folder:
    final_output_folder = os.path.join(base_output_folder, year_folder, month_folder, report_folder)
    os.makedirs(final_output_folder, exist_ok=True)
    
    # Log the final path
    logging.info(f"Final folder path: {final_output_folder}")
    
    # 4) Save ZIP into the final folder with today's date
    today_date_str = today.strftime("%m-%d-%Y")  # e.g., '04-25-2025'
    zip_filename = f"{report_name} {today_date_str}.zip"  # Using report name and date
    zip_path = os.path.join(final_output_folder, zip_filename)
    
    with open(zip_path, "wb") as zf:
        zf.write(zip_bytes)
    logging.info(f"Wrote ZIP to {zip_path}")
    
    # 5) Extract CSV(s), dedupe, and save XLSX
    saved_files = []
    with zipfile.ZipFile(io.BytesIO(zip_bytes)) as z:
        first_csv_processed = False  # Process only the first CSV inside ZIP
        for member in z.namelist():
            if member.lower().endswith(".csv") and not first_csv_processed:
                with z.open(member) as csvfile:
                    df = pd.read_csv(csvfile)
                before = len(df)
                df.drop_duplicates(inplace=True)
                after = len(df)
                logging.info(f"Dropped {before-after} duplicate rows in {member}")
    
                # Build clean XLSX name using report_name and date_filter (or fallback if not provided)
                if report_name and date_filter:
                    xlsx_filename = f"{report_name} {date_filter}.xlsx"
                else:
                    xlsx_filename = f"{report_identifier}_{filter_identifier}.xlsx"
    
                # Remove any forbidden characters from file name
                import re
                xlsx_filename = re.sub(r'[<>:"/\\|?*]', '_', xlsx_filename)
    
                xlsx_path = os.path.join(final_output_folder, xlsx_filename)
                df.to_excel(xlsx_path, index=False)
                logging.info(f"Saved XLSX to {xlsx_path}")
                saved_files.append(xlsx_path)
    
                first_csv_processed = True  # Only process the first CSV
    
    return {
        "run_id": run_id,
        "zip_path": zip_path,
        "saved_xlsx": saved_files
    }
# ────────────────────────────────────

def process_report(report_id, filter_id, customer_ids=None, output_folder=None, report_name=None, date_filter=None):
    """
    Orchestrates bulk report processing:
     1) Polls and decodes the Base64 ZIP.
     2) Creates a dated subfolder.
     3) Saves the ZIP and extracts its CSV into an XLSX using the same naming scheme.
    """
    # Assume 'raw' (the Base64 ZIP string) and run_id are available.
    # For demo purposes, they could be retrieved by earlier steps.
    raw = ...  # Retrieved Base64 ZIP string
    run_id = ...  # Retrieved run identifier
    
    decoded = base64.b64decode(raw)
    
    # Use provided output_folder or fallback
    if output_folder is None:
        output_folder = os.path.join(os.path.dirname(os.path.abspath(__file__)), "output")
    
    # Create a dated subfolder using today's date (if date_filter is not provided)
    today_str = date_filter if date_filter else datetime.now().strftime("%m-%d-%Y")
    dated_output_dir = os.path.join(output_folder, today_str)
    os.makedirs(dated_output_dir, exist_ok=True)
    logging.info(f"Created dated output directory: {dated_output_dir}")
    print("Created dated output directory:", dated_output_dir)
    
    # Build filenames using report_name and today's date; fallback to report_id_filter_id if needed.
    if report_name:
        zip_filename = f"{report_name} {today_str}.zip"
        xlsx_filename = f"{report_name} {today_str}.xlsx"
    else:
        zip_filename = f"{report_id}_{filter_id}_{today_str}.zip"
        xlsx_filename = f"{report_id}_{filter_id}_{today_str}.xlsx"
    
    # Remove any forbidden characters from filename
    zip_filename = re.sub(r'[<>:"/\\|?*]', '_', zip_filename)
    xlsx_filename = re.sub(r'[<>:"/\\|?*]', '_', xlsx_filename)
    
    zip_path = os.path.join(dated_output_dir, zip_filename)
    with open(zip_path, "wb") as zf:
        zf.write(decoded)
    logging.info(f"Wrote ZIP to {zip_path}")
    print("Wrote ZIP to", zip_path)
    
    # Extract CSV(s) and save as XLSX using same naming scheme.
    saved_files = []
    try:
        with zipfile.ZipFile(io.BytesIO(decoded)) as z:
            csv_found = False
            for fname in z.namelist():
                if fname.lower().endswith('.csv'):
                    csv_found = True
                    with z.open(fname) as f:
                        df_csv = pd.read_csv(f)
                    before = len(df_csv)
                    df_csv.drop_duplicates(inplace=True)
                    after = len(df_csv)
                    logging.info(f"Dropped {before - after} duplicate rows in {fname}")
                    
                    xlsx_path = os.path.join(dated_output_dir, xlsx_filename)
                    df_csv.to_excel(xlsx_path, index=False)
                    saved_files.append(xlsx_path)
                    logging.info(f"Saved XLSX to {xlsx_path}")
                    print("Saved XLSX to:", xlsx_path)
            if not csv_found:
                logging.warning("No CSV files found in the ZIP.")
                print("WARNING: No CSV files found in the ZIP.")
    except zipfile.BadZipFile as e:
        logging.error(f"ZIP processing error: {e}")
        print("ZIP processing error:", e)
        return False
    
    return {
        "run_id": run_id,
        "zip_path": zip_path,
        "saved_xlsx": saved_files
    }

if __name__ == '__main__':
    if len(sys.argv) != 3:
        print("Usage: python bulk_api.py <report_id> <filter_id>")
        sys.exit(1)
    rid, fid = sys.argv[1], sys.argv[2]
    success = process_report(rid, fid)
    sys.exit(0 if success else 1)
