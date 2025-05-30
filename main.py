# main.py
import os
import logging
import pandas as pd
from dotenv import load_dotenv

from utils import get_default_output_folder, MockSocketIO
from data_processor import process_customers_with_progress, update_canned_reports

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Load environment variables
load_dotenv()

def main():
    INPUT_EXCEL = "data/Customer_Report_Filter.xlsx"
    OUTPUT_FOLDER = get_default_output_folder()
    try:
        uploaded_data = pd.read_excel(INPUT_EXCEL)
        print("Success-1")
        input_data = uploaded_data.to_dict(orient="records")
        print("Success-2")
        update_canned_reports(input_data, file_name=os.path.basename(INPUT_EXCEL))
        logging.info(f"Output folder is set to: {OUTPUT_FOLDER}")
        mock_socketio = MockSocketIO()
        process_customers_with_progress(INPUT_EXCEL, OUTPUT_FOLDER, mock_socketio, log_file = "process_log.txt")
    except Exception as e:
        logging.exception(f"An error occurred during processing: {e}")

if __name__ == "__main__":
    main()
