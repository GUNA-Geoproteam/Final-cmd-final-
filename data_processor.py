# data_processor.py
import os
import io
import zipfile
import base64
import logging
import pandas as pd
from datetime import datetime
from bulk_api import process_active_customers as bulk_run

from excel_formatter import (format_excel_file, add_report_details_to_xlsx,
                             update_consolidated_file, consolidate_monthly_report)
# from pdf_converter import convert_xlsx_to_pdf_with_split_header
from excel_formatter import sanitize_filename
from auth import get_access_token
from email_graph_api import send_email_with_graph_api
from alignment_dictionary import alignment_dict




# alignment_dict = {
#     "Activity Summary by Month Report": {1: {"align": "L", "width": 25}, 2: {"align": "C", "width": 25}, 3: {"align": "C", "width": 30}, 4: {"align": "C", "width": 50}, 5: {"align": "C", "width": 50}},
#     "CLAIMS BILLED REPORT": {1: {"align": "L", "width": 23}, 2: {"align": "C", "width": 40}, 3: {"align": "C", "width": 32}, 4: {"align": "C", "width": 30}, 5: {"align": "C", "width": 32}, 6: {"align": "C", "width": 40}, 7: {"align": "C", "width": 30}, 8: {"align": "C", "width": 30}, 9: {"align": "L", "width": 41}, 10: {"align": "L", "width": 95}, 11: {"align": "R", "width": 82}},    
#     "NEXTUS MONTHLY DETAIL PAYMENT REPORT": {1: {"align": "L", "width": 60}, 2: {"align": "C", "width": 27}, 3: {"align": "C", "width": 28}, 4: {"align": "L", "width": 50}, 5: {"align": "L", "width": 25}, 6: {"align": "C", "width": 30}, 7: {"align": "C", "width": 20}, 8: {"align": "C", "width": 29}, 9: {"align": "C", "width": 27}, 10: {"align": "C", "width": 30}, 11: {"align": "C", "width": 30}, 12: {"align": "L", "width": 75}, 13: {"align": "R", "width": 25}, 14: {"align": "C", "width": 19}},
#     "NEXTUS PAYMENT SUMMARY MONTHLY REPORT": {1: {"align": "L", "width": 127}, 2: {"align": "C", "width": 42}, 3: {"align": "C", "width": 45}, 4: {"align": "C", "width": 42}, 5: {"align": "L", "width": 127}, 6: {"align": "C", "width": 37}, 7: {"align": "R", "width": 38}},
#     "NEXTUS PAYMENT SUMMARY WEEKLY REPORT": {1: {"align": "L", "width": 127}, 2: {"align": "C", "width": 42}, 3: {"align": "C", "width": 45}, 4: {"align": "C", "width": 37}, 5: {"align": "L", "width": 135}, 6: {"align": "C", "width": 37}, 7: {"align": "R", "width": 38}},
#     "AR AGING SUMMARY": {1: {"align": "L", "width": 135}, 2: {"align": "C", "width": 63}, 3: {"align": "C", "width": 49}, 4: {"align": "C", "width": 42}, 5: {"align": "C", "width": 42}, 6: {"align": "C", "width": 70}, 7: {"align": "C", "width": 43}, 8: {"align": "C", "width": 45}, 9: {"align": "C", "width": 38}, 10: {"align": "C", "width": 35}, 11: {"align": "C", "width": 35}},
#     "NEXTUS PATIENT BALANCE REPORT": {1: {"align": "L", "width": 17}, 2: {"align": "C", "width": 65}, 3: {"align": "C", "width": 35}, 4: {"align": "L", "width": 27}, 5: {"align": "L", "width": 35}, 6: {"align": "C", "width": 35}, 7: {"align": "C", "width": 35}, 8: {"align": "C", "width": 35}, 9: {"align": "C", "width": 45}, 10: {"align": "C", "width": 35}, 11: {"align": "C", "width": 35}, 12: {"align": "L", "width": 38}, 13: {"align": "R", "width": 35}
# }}



import os
import base64
import zipfile
import io
import pandas as pd
import logging
from datetime import datetime
from openpyxl import load_workbook
from ar_new import process_claim_file  # Import function for "A/R Aging Summary"
from auth import get_access_token
from email_graph_api import send_email_with_graph_api

#connections
from nextus_monthly_handling import transform_nextus_monthly_report
from api_client import get_identifier,poll_for_report
from excel_formatter import process_monthly_consolidation,ar_add_report_details_to_xlsx,add_report_details_to_xlsx
from send_log_to_admin import send_log_to_admin
from customer_utils import get_customer_logo, is_customer_active, get_facility_acronym
# from sharepoint_upload import upload_to_sharepoint






# WITH NEW NAMING CONVENTION AND AR AGING SUMMARY
import os
import base64
import zipfile
import io
import pandas as pd
import logging
from datetime import datetime





#KOTHA
def decode_and_process_data(binary_data, base_output_folder, customer_id, customer_name, report_name, filter_column,
                            recipient_email, alignment_dict, date_filter, file_path):
    if not binary_data:
        logging.info(f"No data to decode for customer {customer_name} (ID: {customer_id})")
        return "No data"

    sanitized_customer_name = sanitize_filename(customer_name)
    decoded_data = base64.b64decode(binary_data)
    success_flag = False
    # output_pdf = None

    try:
        with zipfile.ZipFile(io.BytesIO(decoded_data)) as z:
            file_list = z.namelist()
            if not file_list:
                logging.info(f"No files found in the archive for customer {customer_name} (ID: {customer_id})")
                return "No data"

            facility_acronym = get_facility_acronym(customer_id)
            print(f"Facility acronym for {customer_id} and {customer_name} is {facility_acronym}")

            if not facility_acronym:
                facility_acronym = "Unknown"
                logging.warning(f"Facility Acronym not found for Customer ID {customer_id}, using default 'Unknown'.")

            current_month_year = datetime.now().strftime("%b %Y")
            current_year = datetime.now().strftime("%Y")
            current_month = datetime.now().strftime("%b")

            customer_folder = os.path.join(
                base_output_folder,
                current_year,
                current_month,
                report_name,
                f"{report_name} - {date_filter}" if date_filter else "",
                sanitized_customer_name
            )

            os.makedirs(customer_folder, exist_ok=True)

            # Define Processed Reports Folder for raw Excel (AR Aging Summary only)
            processed_output_folder = os.path.join(base_output_folder, "processed_reports")
            os.makedirs(processed_output_folder, exist_ok=True)

            for file_name in file_list:
                if file_name.endswith(".csv"):
                    sanitized_file_name = sanitize_filename(file_name)
                    # extracted_csv_path = os.path.join(customer_folder, file_name)
                    # os.makedirs(os.path.dirname(extracted_csv_path), exist_ok=True)
                    # z.extract(file_name, customer_folder)

                    # z.extract(file_name,processed_output_folder if report_name == "AR Aging Summary" else customer_folder)
                    z.extract(file_name,processed_output_folder if report_name == "AR AGING SUMMARY" else customer_folder)
                    # extracted_csv_path = os.path.join(processed_output_folder if report_name == "AR Aging Summary" else customer_folder, file_name)
                    extracted_csv_path = os.path.join(processed_output_folder if report_name == "AR AGING SUMMARY" else customer_folder, file_name)
                    print(f"Extracted CSV Path: {extracted_csv_path}")

                    try:
                        df_csv = pd.read_csv(extracted_csv_path)
                    except Exception as e:
                        logging.error(f"Error reading CSV file {extracted_csv_path}: {e}")
                        continue

                    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                    new_file_name = f"{current_month_year} ({facility_acronym}) {report_name}_{timestamp}.xlsx"
                    raw_excel_path = os.path.join(customer_folder, new_file_name)

                    df_csv.to_excel(raw_excel_path, index=False)
                    os.remove(extracted_csv_path)

                    if report_name== "AR AGING SUMMARY":
                        print("No formatting required for the AR data source file")
                    else:
                        format_excel_file(raw_excel_path)

                    logging.info(f"Raw Excel (Data Source) saved at: {raw_excel_path}")

                    # AR Aging Summary - Swap Folder Logic
                    if report_name == "AR AGING SUMMARY":

                        # transformed_excel_path = os.path.join(customer_folder,
                        #                                       f"A_R Aging Summary - {sanitized_customer_name}.xlsx")

                        transformed_excel_path = raw_excel_path

                        print(f"⚙️ Processing A/R Aging Summary: {raw_excel_path} → {transformed_excel_path}")
                        print(f"Data Source Excel Path : {raw_excel_path}")
                        print(f"Transformed Excel Path : {transformed_excel_path}")
                        process_claim_file(raw_excel_path, transformed_excel_path)

                        if os.path.exists(transformed_excel_path):
                            print(f"✅ Transformed Excel saved at: {transformed_excel_path}")
                            final_report_path = transformed_excel_path
                            report_period = ar_add_report_details_to_xlsx(final_report_path, report_name, customer_name,
                                                                          filter_column, customer_id, date_filter)

                            # 📤 Upload Transformed Excel to SharePoint
                            # logging.info(f"📤 Uploading Transformed Excel to SharePoint...")
                            # upload_to_sharepoint(final_report_path, file_path, report_name, date_filter,
                            #                      customer_name)



                        else:
                            print(f"❌ ERROR: Transformed Excel NOT found at {transformed_excel_path}")
                            final_report_path = raw_excel_path  # Fallback if transformation fails

                            # # 📤 Upload Normal Excel to SharePoint (No if condition needed)
                            # logging.info(f"📤 Uploading Normal Excel to SharePoint...")
                            # upload_to_sharepoint(final_report_path, file_path, report_name, date_filter, customer_name)

                    else:
                        # Normal Workflow for Other Reports
                        final_report_path = raw_excel_path
                        report_period = add_report_details_to_xlsx(final_report_path, report_name, customer_name,
                                                                   filter_column, customer_id, date_filter)

                        # 📤 Upload Normal Excel to SharePoint (No if condition needed)
                        # logging.info(f"📤 Uploading Normal Excel to SharePoint...")
                        # upload_to_sharepoint(final_report_path, file_path, report_name, date_filter, customer_name)



                    try:
                        df_check = pd.read_excel(final_report_path, header=None)
                    except Exception as e:
                        logging.error(f"Error reading processed XLSX {final_report_path}: {e}")
                        continue

                    num_columns = len(df_check.columns)
                    update_consolidated_file(customer_folder, final_report_path, sanitized_customer_name)
                    process_monthly_consolidation(base_output_folder, report_name, current_year, current_month)

                    # 📤 Upload Consolidated Excel to SharePoint after processing
                    consolidated_report_path = os.path.join(base_output_folder, current_year, current_month,
                                                            report_name,
                                                            f"{report_name}_{current_month}_consolidated.xlsx")
                    # if os.path.exists(consolidated_report_path):
                    #     logging.info(f"📤 Uploading Consolidated Excel to SharePoint...")
                    #     upload_to_sharepoint(consolidated_report_path, file_path, report_name, date_filter,
                    #                          customer_name)
                    # else:
                    #     logging.warning(f"⚠️ Consolidated Excel not found at {consolidated_report_path}. Skipping upload.")







                    if num_columns > 14:
                        logging.error(f"Too many columns ({num_columns}), skipping PDF generation for {customer_name}.")
                    # else:
                    #     output_pdf = os.path.join(customer_folder,
                    #                               f"{current_month_year} ({facility_acronym}) {report_name}_{timestamp}.pdf")
                        today = datetime.now()
                        start_date = today - pd.to_timedelta(today.weekday(), unit='d')
                        base_font_size = 12
                        min_font_size = 6
                        font_size = max(min_font_size,
                                        base_font_size - (num_columns - 8)) if num_columns > 8 else base_font_size

                        logging.info(f"Setting font size to {font_size} for {num_columns} columns.")

                        if report_name == "NEXTUS MONTHLY DETAIL PAYMENT REPORT":
                            transformed_df = transform_nextus_monthly_report(final_report_path)
                            if transformed_df is not None and not transformed_df.empty:
                                transformed_df.to_excel(final_report_path, index=False)
                                format_excel_file(final_report_path)
                                report_period = add_report_details_to_xlsx(final_report_path, report_name,
                                                                           customer_name, filter_column, customer_id,
                                                                           date_filter)

                        # convert_xlsx_to_pdf_with_split_header(final_report_path, output_pdf, customer_id, font_size,
                        #                                       alignment_dict, filter_column, start_date, today,
                        #                                       report_period)

                        # if report_name == "AR AGING SUMMARY":
                        #     convert_xlsx_to_pdf_for_ar_aging(final_report_path, output_pdf, customer_id, font_size,
                        #                                          alignment_dict, report_period)

                        #     logging.info(f"Processed PDF saved for {sanitized_customer_name} at {output_pdf}")
                        #     success_flag = True

                        # else:
                        #     convert_xlsx_to_pdf_for_general_reports(final_report_path, output_pdf, customer_id, font_size,
                        #                                             alignment_dict, report_period)

                        #     logging.info(f"Processed PDF saved for {sanitized_customer_name} at {output_pdf}")
                        #     success_flag = True



                        # # 📤 Upload PDF to SharePoint after generation
                        # if os.path.exists(output_pdf):
                        #     logging.info(f"📤 Uploading PDF to SharePoint...")
                        #     upload_to_sharepoint(output_pdf, file_path, report_name, date_filter, customer_name)

        if recipient_email and success_flag:
            recipient_emails = [email.strip() for email in str(recipient_email).split(',') if
                                email.strip() and email.strip().lower() != "nan"]
            if recipient_emails:
                logging.info(f"Sending email to: {', '.join(recipient_emails)}")
                access_token = get_access_token()
                if access_token:
                    subject = f"Your Report: {report_name}"
                    body = f"Dear {customer_name},\n\nPlease find attached your report: {report_name}.\n\nBest regards,\nNextus Team"

                    attachment_files = [final_report_path]
                    # if output_pdf and os.path.exists(output_pdf):
                    #     attachment_files.append(output_pdf)

                    send_email_with_graph_api(
                        access_token,
                        os.getenv("SENDER_EMAIL"),
                        recipient_emails,
                        subject,
                        body,
                        attachment_paths=attachment_files
                    )
                else:
                    logging.error("Failed to fetch access token. Email not sent.")
            else:
                logging.info(f"Skipping email for customer {customer_name} as no valid recipient email is provided.")

        return "Success" if success_flag else "No data"

    except zipfile.BadZipFile as e:
        logging.error(f"Bad zip file: {e}")
        return "Error"



# NEW working code
def process_customers_with_progress(input_excel, output_folder, socketio, log_file):
    """
    Processes rows in input_excel.  If a row has report_type="bulk" it
    runs the bulk engine, otherwise it runs your single-customer flow.
    """
    df = pd.read_excel(input_excel, dtype=str)
    total = len(df)
    succ = fail = 0

    # remember original bulk_api.OUTPUT_DIR so we can restore it
    _orig_bulk_dir = bulk_api.OUTPUT_DIR

    with open(log_file, "w") as log:
        log.write("Processing started.\n")

        for idx, row in df.iterrows():
            rtype     = str(row.get("report_type", "single")).strip().lower()
            report_id = row["report_identifier"]
            filter_id = row["filter_identifier"]
            rpt_name  = row["report_name"]
            date_filt = row.get("date_filter", "").strip()
            cust_ids  = [c.strip() for c in str(row["customer_id"]).split(",")]

            # ── BULK branch ───────────────────────────────────────────────────────
            if rtype == "bulk":
                log.write(f"Row {idx+1}: BULK → customers={cust_ids}\n")
                # force bulk_api to write into our `output_folder`
                bulk_api.OUTPUT_DIR = output_folder
                try:
                    result = bulk_run(
                        cust_ids,
                        report_id,
                        filter_id,
                        report_name=rpt_name,
                        date_filter=date_filt
                    )
                    succ += 1
                    status = f"Bulk OK ({len(result.get('saved_xlsx',[]))} files)"
                except Exception as e:
                    fail += 1
                    status = f"Bulk ERROR: {e!r}"
                finally:
                    # restore original
                    bulk_api.OUTPUT_DIR = _orig_bulk_dir

                prog = int((idx+1)/total * 100)
                socketio.emit('progress_update', {'progress': prog})
                entry = (f"Row {idx+1}/{total} BULK → {report_id}/{filter_id} "
                         f"Status={status} Progress={prog}%\n")
                log.write(entry)
                logging.info(entry.strip())
                continue

            # ── SINGLE‐customer branch ────────────────────────────────────────────
            cust_id   = row["customer_id"]
            cust_name = row["customer_name"]
            recipient = row.get("recipient_email", None)
            filter_col= row.get("filter_column", None)

            # skip inactive
            if not is_customer_active(cust_id):
                succ += 1
                status = "Skipped (inactive)"
                prog = int((idx+1)/total * 100)
                socketio.emit('progress_update', {'progress': prog})
                entry = (f"Row {idx+1}/{total} SINGLE → Cust={cust_id} "
                         f"Status={status} {prog}%\n")
                log.write(entry)
                logging.info(entry.strip())
                continue

            # fetch run ID
            ident = get_identifier(cust_id, report_id, filter_id)
            if not ident:
                fail += 1
                status = "No identifier"
            else:
                raw = poll_for_report(ident)
                if not raw:
                    fail += 1
                    status = "No data"
                else:
                    try:
                        status = decode_and_process_data(
                            raw, output_folder,
                            cust_id, cust_name,
                            rpt_name, filter_col,
                            recipient, alignment_dict,
                            date_filt, row.get("file_path")
                        )
                        if status in ("Success", "No data"):
                            succ += 1
                        else:
                            fail += 1
                    except Exception as e:
                        fail += 1
                        status = f"Error: {e!r}"

            prog = int((idx+1)/total * 100)
            socketio.emit('progress_update', {'progress': prog})
            entry = (f"Row {idx+1}/{total} SINGLE → Cust={cust_id} "
                     f"Rpt={report_id}/{filter_id} Status={status} {prog}%\n")
            log.write(entry)
            logging.info(entry.strip())

        # final summary
        socketio.emit('progress_update', {'progress': 100})
        summary = {"total_runs": total, "success_count": succ, "failure_count": fail}
        log.write("\nSUMMARY:\n")
        log.write(f"  Total:   {total}\n")
        log.write(f"  Success: {succ}\n")
        log.write(f"  Failure: {fail}\n")
        log.flush()

    send_log_to_admin(log_file)
    return summary










import os
import pandas as pd
import logging

def update_canned_reports(input_data, file_name=None):
    """
    Updates the Canned_Reports.xlsx file with new input data, avoiding duplicates.
    Ensures columns remain in the correct order and includes date_filter and report_type.
    """
    reports_file = 'data/Canned_Reports.xlsx'
    required_columns = [
        'customer_id',
        'report_identifier',
        'filter_identifier',
        'customer_name',
        'report_name',
        'filter_column',
        'unique_report_name',
        'date_filter',     # ✅ ensure date_filter is stored
        'report_type'      # ✅ now track single vs bulk
    ]

    # Load existing or create new
    if os.path.exists(reports_file):
        existing_data = pd.read_excel(reports_file, dtype=str)
        logging.info(f"Loaded existing data from {reports_file}")
    else:
        existing_data = pd.DataFrame(columns=required_columns)
        logging.info(f"{reports_file} does not exist. Creating a new file.")

    # Ensure all required columns exist
    for col in required_columns:
        if col not in existing_data.columns:
            existing_data[col] = ""

    # Build set of unique_report_name to prevent duplicates
    existing_unique = set(existing_data['unique_report_name'].fillna(""))

    new_rows = []
    for record in input_data:
        # build the same unique key as before
        unique_name = (
            f"{record['report_name']} "
            f"{record.get('date_filter','').strip()} - "
            f"{record['customer_name']}"
        )
        if unique_name not in existing_unique:
            new_rows.append({
                'customer_id':       record['customer_id'],
                'report_identifier': record['report_identifier'],
                'filter_identifier': record['filter_identifier'],
                'customer_name':     record['customer_name'],
                'report_name':       record['report_name'],
                'filter_column':     record['filter_column'],
                'unique_report_name': unique_name,
                'date_filter':       record.get('date_filter', ''),
                'report_type':       record.get('report_type', 'single').strip().lower()
            })
            existing_unique.add(unique_name)

    logging.info(f"New records to add: {len(new_rows)}")

    if new_rows:
        new_df = pd.DataFrame(new_rows)
        updated = pd.concat([existing_data, new_df], ignore_index=True)
        # enforce column order
        updated = updated[required_columns]
        updated.to_excel(reports_file, index=False)
        logging.info(f"Appended {len(new_rows)} new records to {reports_file}.")
    else:
        logging.info("No new records to add; all were duplicates.")


def load_payment_data(file_path):
    """
    Load payment data from Excel and perform initial processing.
    """
    df = pd.read_excel(file_path)
    required_columns = [
        'Facility Name', 'Payment Entered', 'Payment Received',
        'Credit Source(w Payer)', 'Payment Total Paid (Sum)'
    ]
    if not all(col in df.columns for col in required_columns):
        raise ValueError("Missing required columns in the Excel file.")
    df['Payment Entered'] = pd.to_datetime(df['Payment Entered'], errors='coerce')
    df['Payment Received'] = pd.to_datetime(df['Payment Received'], errors='coerce')
    df['Payment Total Paid (Sum)'] = (
        df['Payment Total Paid (Sum)'].astype(str)
        .str.replace('[\$,]', '', regex=True)
        .pipe(pd.to_numeric, errors='coerce')
    )
    df['Year-Month'] = df['Payment Received'].dt.to_period('M').astype(str)
    return df
