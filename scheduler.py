# import sys
# import schedule
# import pandas as pd
# import os
# from datetime import datetime
# import time
# import logging
# from data_processor import process_customers_with_progress
# from utils import MockSocketIO


# def run_scheduled_jobs_for_today():
#     """
#     Reads Scheduled_Reports.xlsx to find which jobs are 'due' today (daily, weekly, monthly, etc.),
#     merges each with Canned_Reports.xlsx to get filter_column, then processes each row SEQUENTIALLY.

#     Crucially, we call process_customers_with_progress one row at a time, passing row['file_path']
#     so that each row's output goes to its custom folder.
#     """
#     logging.info(f"==== Starting daily batch at {datetime.now()} ====")

#     schedule_file = "data/Scheduled_Reports.xlsx"
#     canned_file = "data/Canned_Reports.xlsx"

#     if not os.path.exists(schedule_file):
#         logging.error(f"Scheduled reports file not found: {schedule_file}")
#         return

#     schedule_data = pd.read_excel(schedule_file)
#     today = datetime.now()
#     current_day_name = today.strftime("%A").lower()  # e.g. "monday"
#     current_date_num = today.day  # e.g. 1..31

#     due_rows = []
#     for _, row in schedule_data.iterrows():
#         frequency = str(row["frequency"]).strip().lower()
#         row_day = str(row["day"]).strip().lower() if not pd.isna(row["day"]) else None
#         custom_days = str(row["custom_days"]).strip() if not pd.isna(row["custom_days"]) else None
#         date_filter = str(row["date_filter"]).strip().lower() if "date_filter" in row and not pd.isna(row["date_filter"]) else None  # ✅ Add this


#         is_due = False

#         if frequency == "daily":
#             is_due = True
#         elif frequency == "weekly" and (row_day == current_day_name):
#             is_due = True
#         elif frequency == "fortnightly" and (row_day == current_day_name):
#             # If you want an actual "every two weeks" check, you'd do extra logic here
#             is_due = True
#         elif frequency == "monthly":
#             if custom_days:
#                 days_list = [int(d) for d in custom_days.split(",")]
#                 if current_date_num in days_list:
#                     is_due = True
#             else:
#                 if current_date_num == 1:
#                     is_due = True
#         elif frequency == "custom" and custom_days:
#             days_list = [int(d) for d in custom_days.split(",")]
#             if current_date_num in days_list:
#                 is_due = True

#         if is_due:
#             due_rows.append(row)

#     if not due_rows:
#         logging.info("No rows are due today. Exiting.")
#         print("No scheduled jobs for today. Done.")
#         return

#     # Read Canned_Reports
#     canned_data = pd.read_excel(canned_file)

#     # Process each "due row" individually, passing that row's file_path
#     for row in due_rows:
#         # 1) Merge with Canned_Reports to find filter_column
#         customer_id = row["customer_id"]
#         report_identifier = row["report_identifier"]
#         filter_identifier = row["filter_identifier"]
#         match = canned_data[
#             (canned_data["customer_id"] == customer_id) &
#             (canned_data["report_identifier"] == report_identifier) &
#             (canned_data["filter_identifier"] == filter_identifier)
#             ]

#         if not match.empty:
#             filter_column = match.iloc[0]["filter_column"]
#         else:
#             filter_column = None

#         # 2) Create a one-row DataFrame containing exactly the columns that
#         #    process_customers_with_progress expects:
#         single_row_data = {
#             "customer_id": row["customer_id"],
#             "customer_name": row["customer_name"],
#             "report_name": row["report_name"],
#             "report_identifier": row["report_identifier"],
#             "filter_identifier": row["filter_identifier"],
#             "recipient_email": row.get("recipients_email", None),
#             "filter_column": filter_column
#             # add columns if your code expects more
#         }
#         df_single = pd.DataFrame([single_row_data])

#         # 3) Save it as a temporary Excel so process_customers_with_progress can read it
#         temp_xlsx = "data/Customer_Report_Filter_TEMP.xlsx"  # Overwrite if we want
#         df_single.to_excel(temp_xlsx, index=False)

#         # 4) Call process_customers_with_progress
#         #    PASS THIS ROW'S file_path as the second argument
#         row_output_folder = row["file_path"]
#         if not os.path.exists(row_output_folder):
#             try:
#                 os.makedirs(row_output_folder, exist_ok=True)
#             except Exception as e:
#                 logging.error(f"Failed to create output folder {row_output_folder}: {e}")
#                 continue

#         logging.info(f"Processing {customer_id} => Output folder: {row_output_folder}")

#         try:
#             summary = process_customers_with_progress(
#                 temp_xlsx,
#                 row_output_folder,
#                 MockSocketIO()
#             )
#             logging.info(f"Row done. Summary: {summary}")
#             print(f"Processed row for {customer_id}, summary={summary}")
#         except Exception as e:
#             logging.error(f"Error processing row for {customer_id}: {e}")
#             print(f"Error: {e}")

#     logging.info("All due rows processed.Exiting now.")
#     print("All due rows processed. Exiting now.")
#     sys.exit(0)



# def schedule_daily_midnight_job():
#     logging.basicConfig(
#         filename="scheduler.log",
#         level=logging.INFO,
#         format="%(asctime)s %(message)s"
#     )

#     # Ensure the scheduled reports file has the date_filter column
#     schedule_file = "data/Scheduled_Reports.xlsx"

#     if os.path.exists(schedule_file):
#         df = pd.read_excel(schedule_file)
        
#         if 'date_filter' not in df.columns:
#             df['date_filter'] = None  # Add the new column if missing
#             df.to_excel(schedule_file, index=False)

#     schedule.every().day.at("11:30").do(run_scheduled_jobs_for_today)
#     print("Scheduled run_scheduled_jobs_for_today at 11:30 every day.")



# def run_scheduler():
#     schedule_daily_midnight_job()
#     while True:
#         schedule.run_pending()
#         time.sleep(1)


# if __name__ == "__main__":
#     run_scheduler()



import sys
import schedule
import pandas as pd
import os
from datetime import datetime
import time
import logging
from datetime import datetime
from bulk_api import build_bulk_post_url, process_active_customers as bulk_run
from data_processor import process_customers_with_progress
from sharepoint_upload import upload_to_sharepoint

from utils import MockSocketIO

# ← NEW: import your “bulk” helper
from bulk_api import process_active_customers as bulk_run


def print_env_file(filepath=".env"):
    if os.path.exists(filepath):
        with open(filepath, "r") as env_file:
            content = env_file.read()
            print("=== .env File Content Start ===")
            print(content)
            print("=== .env File Content End ===")
    else:
        print(f".env file not found at {filepath}")



def run_scheduled_jobs_for_today():
    logging.info(f"==== Starting daily batch at {datetime.now()} ====")

    schedule_file = "data/Scheduled_Reports.xlsx"
    canned_file   = "data/Canned_Reports.xlsx"

    if not os.path.exists(schedule_file):
        logging.error(f"Scheduled reports file not found: {schedule_file}")
        return

    schedule_data = pd.read_excel(schedule_file)
    canned_data   = pd.read_excel(canned_file)   # ← load this once, up front

    today            = datetime.now()
    current_day_name = today.strftime("%A").lower()
    current_date_num = today.day

    # figure out which rows are due…
    due_rows = []
    for _, row in schedule_data.iterrows():
        freq        = str(row["frequency"]).strip().lower()
        row_day     = str(row["day"]).strip().lower()        if not pd.isna(row["day"])        else None
        custom_days = str(row["custom_days"]).strip()        if not pd.isna(row["custom_days"]) else None

        is_due = (
            freq == "daily" or
            (freq in ("weekly","fortnightly") and row_day == current_day_name) or
            (freq == "monthly" and (
                (custom_days and current_date_num in map(int, custom_days.split(","))) or
                (not custom_days and current_date_num == 1)
            )) or
            (freq == "custom" and custom_days and current_date_num in map(int, custom_days.split(",")))
        )

        if is_due:
            due_rows.append(row)

    if not due_rows:
        logging.info("No rows are due today. Exiting.")
        print("No scheduled jobs for today. Done.")
        return

    # ── now process each due row ─────────────────────────────────────
    for row in due_rows:
        report_type = str(row.get("report_type", "single")).strip().lower()  # Now expects "single" or "multiple"
        report_identifier = row["report_identifier"]
        filter_identifier = row["filter_identifier"]
        raw_ids = row["customer_id"]

        # If the report type is multiple, run the bulk/multiple branch.
        if report_type == "multiple":
            customer_ids = [cid.strip() for cid in str(raw_ids).split(",") if cid.strip()]
            print("Multiple Report Selected. Running multiple-customer (bulk) flow.")
            # Build URL, set date, etc. (as before)
            raw_date = row.get("date_filter")
            if isinstance(raw_date, datetime):
                date_str = raw_date.strftime("%Y-%m-%d")
            else:
                date_str = str(raw_date) if raw_date else datetime.now().strftime("%Y-%m-%d")
            try:
                result = bulk_run(
                    customer_ids,
                    report_identifier,
                    filter_identifier,
                    report_name=row["report_name"],
                    date_filter=date_str
                    # note: if you want to pass destination here, include destination_folder=row["file_path"]
                )
            except Exception as e:
                print(f"❌ Multiple report FAILED: {e}")
                logging.error(f"Multiple report error for {report_identifier}/{filter_identifier}: {e}")
                continue
            print(f"✅ Multiple report succeeded: {report_identifier}_{filter_identifier}")
            print("   ZIP →", result["zip_path"])
            print("   XLSX →", result["saved_xlsx"])
            # Optionally upload files, etc.
            for file_path in result.get("saved_xlsx", []):
                try:
                    upload_to_sharepoint(
                        file_path=file_path,
                        report_identifier=row["report_identifier"],
                        filter_identifier=row["filter_identifier"],
                        report_name=row["report_name"],
                        _date_filter=date_str,
                        report_type="multiple",  # Changed from bulk
                        customer_name=None
                    )
                except Exception as e:
                    logging.error(f"Failed to upload multiple report {file_path}: {e}")
            continue

        # Otherwise, if report_type is "single", run the single-customer flow.
        else:
            # (Existing single flow code, merging with canned_data, etc.)
            match = canned_data[
                (canned_data["customer_id"] == row["customer_id"]) &
                (canned_data["report_identifier"] == report_identifier) &
                (canned_data["filter_identifier"] == filter_identifier)
            ]
            if not match.empty:
                filter_column = match.iloc[0]["filter_column"]
                date_filter = match.iloc[0]["date_filter"]
            else:
                filter_column = None
                date_filter = None
            single_row_data = {
                "customer_id": row["customer_id"],
                "customer_name": row["customer_name"],
                "report_name": row["report_name"],
                "report_identifier": report_identifier,
                "filter_identifier": filter_identifier,
                "recipient_email": row.get("recipients_email"),
                "filter_column": filter_column,
                "date_filter": date_filter,
                "file_path": row["file_path"]
            }
            df_single = pd.DataFrame([single_row_data])
            temp_xlsx = "data/Customer_Report_Filter_TEMP.xlsx"
            df_single.to_excel(temp_xlsx, index=False)
            output_folder = row["file_path"]
            logging.info(f"Processing single report for {row['customer_id']} → {output_folder}")
            try:
                log_file = os.path.join(output_folder, "log.txt")
                summary = process_customers_with_progress(
                    temp_xlsx,
                    output_folder,
                    MockSocketIO(),
                    log_file
                )
                logging.info(f"Single report done. Summary: {summary}")
                print(f"Processed row for {row['customer_id']}, summary={summary}")
            except Exception as e:
                logging.error(f"Error in single report for {row['customer_id']}: {e}")
                print(f"Error: {e}")

    logging.info("All due rows processed. Exiting now.")
    print("All due rows processed. Exiting now.")
    sys.exit(0)


def schedule_daily_midnight_job():
    logging.basicConfig(
        filename="scheduler.log",
        level=logging.INFO,
        format="%(asctime)s %(message)s"
    )
    schedule.every().day.at("05:55").do(run_scheduled_jobs_for_today)
    print("Scheduled run_scheduled_jobs_for_today at 12:14 every day.")


def run_scheduler():
    schedule_daily_midnight_job()
    while True:
        schedule.run_pending()
        time.sleep(1)


if __name__ == "__main__":
    print_env_file()
    run_scheduler()
    

