"""
app.py
"""

import eventlet
# don’t patch os — let real os.fdopen handle files
eventlet.monkey_patch(os=False)
import json  # at the top if not already imported
from flask import make_response
import io, csv
from sqlalchemy import text
import logging
from flask import Flask, request, render_template, jsonify, send_from_directory, redirect, flash
from flask_socketio import SocketIO
import os
import pandas as pd
from werkzeug.utils import secure_filename
from data_processor import process_customers_with_progress, update_canned_reports, load_payment_data
from dash_app import init_dash_app
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import text
from dotenv import load_dotenv
from sqlalchemy.exc import OperationalError
from flask_mail import Mail, Message
from auth_helper import get_graph_access_token
from email_graph_api import send_email_with_graph_api
import os
from dotenv import load_dotenv
load_dotenv()            # ← must come before any os.getenv()
from functools import wraps
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import text
from flask import Flask, request, render_template, redirect, url_for, flash, make_response, jsonify, send_from_directory
import eventlet
from bulk_api import process_active_customers as bulk_run


app = Flask(__name__)
app.secret_key = os.getenv("FLASK_SECRET_KEY", "dev")
# still in app.py

# store tokens & user info on disk (not in client cookie)
app.config["SESSION_TYPE"] = "filesystem"

# your Azure AD app settings
CLIENT_ID     = os.getenv("AZURE_CLIENT_ID")
CLIENT_SECRET = os.getenv("AZURE_CLIENT_SECRET")
AUTHORITY     = os.getenv("AZURE_AUTHORITY")      # e.g. https://login.microsoftonline.com/your-tenant
REDIRECT_PATH = "/getAToken"                      # must match your Azure app registration
SCOPE         = ["User.Read"]                     # we just need user profile



# MSAL / Flask-Session setup
CLIENT_ID     = os.getenv("AZURE_CLIENT_ID")
CLIENT_SECRET = os.getenv("AZURE_CLIENT_SECRET")
TENANT_ID     = os.getenv("AZURE_TENANT_ID")
AUTHORITY     = f"https://login.microsoftonline.com/{TENANT_ID}"
REDIRECT_PATH = "/getAToken"   # must match your AAD app registration
REDIRECT_URI  = f"http://localhost:5000{REDIRECT_PATH}"
SCOPE         = ["User.Read"]

# store tokens & user info on disk



app = Flask(__name__)

# Load environment variables
# load_dotenv()
# print("Environment variables loaded:")
# print("DB_USER:", os.getenv("DB_USER"))
# print("DB_PASSWORD:", os.getenv("DB_PASSWORD"))
# print("DB_HOST:", os.getenv("DB_HOST"))
# print("DB_PORT:", os.getenv("DB_PORT"))
# print("DB_NAME:", os.getenv("DB_NAME"))

# Database configuration
load_dotenv()

server = os.getenv("DB_SERVER")
database = os.getenv("DB_DATABASE")
driver = os.getenv("ODBC_DRIVER")
auth = os.getenv("AUTH_TYPE")

connection_string = (
    f"mssql+pyodbc://@{server}/{database}"
    f"?driver={driver}&authentication={auth}"
)

app.config["SQLALCHEMY_DATABASE_URI"] = connection_string
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db = SQLAlchemy(app)

app.secret_key = 'your_secret_key_here'

# Flask application and SocketIO initialization
socketio = SocketIO(app, cors_allowed_origins="*")

# Initialize Dash app
dash_app = init_dash_app(app)

# Folder configurations
UPLOAD_FOLDER = 'uploads'  # Directory for uploaded files
OUTPUT_FOLDER = 'output'   # Directory for processed files
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['OUTPUT_FOLDER'] = OUTPUT_FOLDER

# Create necessary directories if not present
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(OUTPUT_FOLDER, exist_ok=True)

# Mount Dash app at /analytics
@app.route('/analytics')
def analytics_redirect():
    """
    Route to embed the Dash dashboard in an iframe.
    """
    return '''
    <h1>Analytics Dashboard</h1>
    <iframe src="/dashboard/" width="100%" height="1200px"></iframe>
    '''
@app.route('/')

def index():
    """
    Route for the homepage.
    Renders the index.html template.

    Returns:
        HTML: The homepage template.
    """
    return render_template('index.html')



# @app.route('/_debug/tables')
# def debug_tables():
#     # Which database?
#     db_name = db.session.execute(text("SELECT DB_NAME()")).scalar()

#     # List all base tables
#     result = db.session.execute(text("""
#       SELECT TABLE_SCHEMA, TABLE_NAME
#       FROM INFORMATION_SCHEMA.TABLES
#       WHERE TABLE_TYPE = 'BASE TABLE'
#     """)).fetchall()

#     tables = [f"{row.TABLE_SCHEMA}.{row.TABLE_NAME}" for row in result]
#     return jsonify({
#       "connected_database": db_name,
#       "tables": tables
#     })










# --- Debug: see where you’re connected ---
@app.route("/debug/current-db")
def debug_db():
    name = db.session.execute(text("SELECT DB_NAME()")).scalar()
    return f"🔍 Connected to: {name}"

# # --- LOCMASTER CRUD ---
# @app.route('/view-locmaster')
# def view_locmaster():
#     rows = db.session.execute(text("""
#         SELECT rev_code, cpt_code, loc, carrier, excluded_carrier
#         FROM dbo.locmaster
#     """)).fetchall()
#     return render_template('view_locmaster.html', rows=rows)

# @app.route('/locmaster/new', methods=['GET','POST'])
# def new_locmaster():
#     if request.method=='POST':
#         params = {k: request.form[k] for k in
#                   ('rev_code','cpt_code','loc','carrier','excluded_carrier')}
#         db.session.execute(text("""
#             INSERT INTO dbo.locmaster
#               (rev_code,cpt_code,loc,carrier,excluded_carrier)
#             VALUES
#               (:rev_code,:cpt_code,:loc,:carrier,:excluded_carrier)
#         """), params)
#         db.session.commit()
#         flash('LOC record added.', 'success')
#         return redirect(url_for('view_locmaster'))
#     return render_template('locmaster_form.html', row=None)
# @app.route('/edit-locmaster/<rev_code>/', defaults={'cpt_code': None}, methods=['GET', 'POST'])
# @app.route('/edit-locmaster/<rev_code>/<cpt_code>', methods=['GET', 'POST'])
# def edit_locmaster(rev_code, cpt_code):
#     if request.method == 'POST':
#         try:
#             # Get new values from the form
#             updated_rev_code = request.form['rev_code']
#             updated_cpt_code = request.form['cpt_code'] or None
#             loc = request.form['loc']
#             carrier = request.form['carrier']
#             excluded_carrier = request.form['excluded_carrier']

#             # Retrieve the original values from hidden fields
#             orig_rev_code = request.form['orig_rev_code']
#             orig_cpt_code = request.form['orig_cpt_code'] or None

#             if orig_cpt_code:
#                 update_query = """
#                     UPDATE dbo.locmaster
#                     SET rev_code = :new_rev_code,
#                         cpt_code = :new_cpt_code,
#                         loc = :loc,
#                         carrier = :carrier,
#                         excluded_carrier = :excluded_carrier
#                     WHERE rev_code = :orig_rev_code AND cpt_code = :orig_cpt_code
#                 """
#             else:
#                 update_query = """
#                     UPDATE dbo.locmaster
#                     SET rev_code = :new_rev_code,
#                         cpt_code = :new_cpt_code,
#                         loc = :loc,
#                         carrier = :carrier,
#                         excluded_carrier = :excluded_carrier
#                     WHERE rev_code = :orig_rev_code AND cpt_code IS NULL
#                 """

#             db.session.execute(
#                 text(update_query), {
#                     'new_rev_code': updated_rev_code,
#                     'new_cpt_code': updated_cpt_code,
#                     'loc': loc,
#                     'carrier': carrier,
#                     'excluded_carrier': excluded_carrier,
#                     'orig_rev_code': orig_rev_code,
#                     'orig_cpt_code': orig_cpt_code
#                 }
#             )
#             db.session.commit()
#             flash("LOC record updated successfully.", "success")
#             return redirect(url_for('view_locmaster'))
#         except Exception as e:
#             db.session.rollback()
#             flash(f"Error updating record: {e}", "error")
#             return redirect(url_for('view_locmaster'))
#     else:
#         # GET request: fetch the record and display form
#         row = db.session.execute(
#             text("SELECT rev_code, cpt_code, loc, carrier, excluded_carrier FROM dbo.locmaster WHERE rev_code = :rev_code AND (cpt_code = :cpt_code OR (cpt_code IS NULL AND :cpt_code IS NULL))"),
#             {'rev_code': rev_code, 'cpt_code': cpt_code}
#         ).fetchone()
#         if not row:
#             flash("Record not found.", "error")
#             return redirect(url_for('view_locmaster'))

#         # Optionally load groups or other required data here for the form
#         return render_template('locmaster_form.html', row=dict(row._mapping))

# @app.route('/locmaster/delete/<rev_code>/', defaults={'cpt_code': None}, methods=['POST'])
# @app.route('/locmaster/delete/<rev_code>/<cpt_code>',              methods=['POST'])
# def delete_locmaster(rev_code, cpt_code):
#     if cpt_code is None:
#         # delete the row where cpt_code IS NULL
#         db.session.execute(text("""
#             DELETE FROM dbo.locmaster
#              WHERE rev_code = :rev_code
#                AND cpt_code IS NULL
#         """), {'rev_code': rev_code})
#     else:
#         db.session.execute(text("""
#             DELETE FROM dbo.locmaster
#              WHERE rev_code = :rev_code
#                AND cpt_code  = :cpt_code
#         """), {'rev_code': rev_code, 'cpt_code': cpt_code})
#     db.session.commit()
#     flash('LOC record deleted.', 'success')
#     return redirect(url_for('view_locmaster'))

# @app.route('/locmaster/download')
# def download_locmaster():
#     rows = db.session.execute(text("""
#         SELECT rev_code,cpt_code,loc,carrier,excluded_carrier
#         FROM dbo.locmaster
#     """)).fetchall()
#     si = io.StringIO()
#     writer = csv.writer(si)
#     writer.writerow(['rev_code','cpt_code','loc','carrier','excluded_carrier'])
#     for r in rows:
#         writer.writerow([r.rev_code, r.cpt_code, r.loc, r.carrier, r.excluded_carrier])
#     resp = make_response(si.getvalue())
#     resp.headers.update({
#       "Content-Disposition":"attachment;filename=locmaster.csv",
#       "Content-Type":"text/csv"
#     })
#     return resp





















@app.route('/process', methods=['POST'])
def process_file():
    """Route to handle file upload and split bulk vs single jobs."""
    if 'file' not in request.files or 'destination_folder' not in request.form:
        return jsonify({"error": "File and destination folder are required."}), 400

    file         = request.files['file']
    destination  = request.form['destination_folder']
    os.makedirs(destination, exist_ok=True)

    if not file.filename.endswith('.xlsx'):
        return jsonify({"error": "Invalid file type. Only .xlsx supported."}), 400

    # save uploaded
    filename    = secure_filename(file.filename)
    upload_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    file.save(upload_path)

    try:
        df = pd.read_excel(upload_path)
        records = df.to_dict(orient='records')

        # 1) Update your canned reports as before
        update_canned_reports(records, file_name=filename)

        bulk_results   = []
        single_records = []

        # 2) split out bulk vs single
        for r in records:
            rpt_type = str(r.get('report_type','')).strip().lower()
            if rpt_type == 'bulk':
                customer_ids = [c.strip() for c in str(r['customer_id']).split(',') if c.strip()]
                # call the bulk runner and pass the destination folder from the UI
                res = bulk_run(
                    customer_ids,
                    r['report_identifier'],
                    r['filter_identifier'],
                    report_name=r.get('report_name'),
                    date_filter=r.get('date_filter'),
                    destination_folder=destination  # now using UI-provided folder
                )
                
                bulk_results.append({
                    'report_name': r.get('report_name'),
                    'customer_ids': customer_ids,
                    'result': res
                })
            else:
                single_records.append(r)

        # 3) for your single jobs, write a temp Excel and call your progress function once
        single_summary = None
        if single_records:
            tmp = os.path.join(app.config['UPLOAD_FOLDER'], 'temp_single_jobs.xlsx')
            pd.DataFrame(single_records).to_excel(tmp, index=False)

            log_file = os.path.join(destination, 'single_processing.log')
            single_summary = process_customers_with_progress(
                tmp,
                destination,
                socketio,
                log_file
            )
            os.remove(tmp)

        # clean up upload
        os.remove(upload_path)

        return jsonify({
            "bulk_jobs":   bulk_results,
            "single_summary": single_summary
        }), 200

    except Exception as e:
        logging.error("Processing failed", exc_info=True)
        if os.path.exists(upload_path):
            os.remove(upload_path)
        return jsonify({"error": str(e)}), 500


@app.route('/upload-payment-data', methods=['POST'])
def upload_payment_data():
    """
    Handle payment data upload and processing.
    """
    if 'file' not in request.files:
        return jsonify({"error": "No file uploaded."}), 400

    file = request.files['file']
    if file.filename.endswith('.xlsx'):
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], secure_filename(file.filename))
        file.save(file_path)

        try:
            df = load_payment_data(file_path)
            df.to_excel(os.path.join(app.config['OUTPUT_FOLDER'], 'processed_payments.xlsx'), index=False)
            return jsonify({"message": "File processed successfully."}), 200
        except Exception as e:
            return jsonify({"error": str(e)}), 500
    else:
        return jsonify({"error": "Invalid file type. Only .xlsx files are supported."}), 400

@socketio.on('connect')
def test_connect():
    """
    SocketIO event handler for new client connections.
    Sends an initial progress update of 0% to the connected client.

    Emits:
        progress_update (dict): Initial progress of 0%.
    """
    print("Client connected")
    socketio.emit('progress_update', {'progress': 0})

@app.route('/download-template')
def download_template():
    """
    Route to download the report filter template.
    Serves the template file from the 'templates' directory.

    Returns:
        File: The template file for download.
    """
    template_folder = os.path.join(os.getcwd(), 'templates')  # Directory containing the template
    template_filename = 'Customer_Report_Filter_Template.xlsx'
    return send_from_directory(template_folder, template_filename, as_attachment=True)

@app.route('/download-scheduled-reports')
def download_scheduled_reports():
    """
    Route to download the scheduled reports.


    Returns:
        File: The scheduled reports file for download.
    """
    template_folder = os.path.join(os.getcwd(), 'data')  # Directory containing the template
    template_filename = 'Scheduled_Reports.xlsx'
    return send_from_directory(template_folder, template_filename, as_attachment=True)

#code for the user guide

@app.route('/download-user-guide')
def download_user_guide():
    """
    Route to download the User Guide document.

    Returns:
        File: The User Guide document for download.
    """
    template_folder = os.path.join(os.getcwd(), 'data')  # Same directory as Scheduled Reports
    template_filename = 'User Guide.pdf'
    return send_from_directory(template_folder, template_filename, as_attachment=True)


@app.route('/get-reports', methods=['GET'])
def get_reports():
    """
    Route to fetch the unique report names from Canned_Reports.xlsx.
    """
    try:
        # Path to the Canned_Reports.xlsx file
        file_path = os.path.join("data", "Canned_Reports.xlsx")

        # Read the Excel file
        df = pd.read_excel(file_path)

        # Extract the unique_report_name column and drop NaN values
        report_names = df['unique_report_name'].dropna().tolist()

        # Return the list as JSON
        return jsonify({"reports": report_names}), 200
    except Exception as e:
        return jsonify({"error": f"Failed to load reports: {str(e)}"}), 500

@app.route('/schedule-report', methods=['POST'])
def schedule_report():
    """
    Handle scheduled report setup.
    Deduplicate on (customer_id, report_name, report_type).
    """
    try:
        data             = request.get_json()
        reports          = data.get('reports', [])
        report_type      = data.get('report_type')             # ← NEW
        frequency        = data.get('frequency')
        day              = data.get('day')
        custom_days      = data.get('custom_days')
        file_path        = data.get('file_path')
        recipients_email = data.get('recipients_email')
        date_filter      = data.get('date_filter', '')

        # Load canned reports
        canned_df = pd.read_excel('data/Canned_Reports.xlsx')

        # Load or create the scheduled-reports sheet (with report_type)
        sched_path = 'data/Scheduled_Reports.xlsx'
        if os.path.exists(sched_path):
            scheduled_df = pd.read_excel(sched_path, dtype=str)
        else:
            scheduled_df = pd.DataFrame(columns=[
                "customer_id","customer_name","report_name","report_identifier",
                "filter_identifier","report_type",    # ← ensure we have this
                "frequency","day","custom_days",
                "file_path","recipients_email","date_filter"
            ])

        # Make sure the column exists even if the file is old
        if 'report_type' not in scheduled_df.columns:
            scheduled_df['report_type'] = ''

        # Build a dedupe key including report_type
        scheduled_df['unique_id'] = (
            scheduled_df['customer_id'].astype(str) + "_" +
            scheduled_df['report_name'] + "_" +
            scheduled_df['report_type']
        )
        existing_ids = set(scheduled_df['unique_id'])

        # Collect only new rows
        new_rows = []
        for uniq in reports:  # uniq is the unique_report_name
            subset = canned_df[canned_df['unique_report_name'] == uniq]
            for _, r in subset.iterrows():
                uid = f"{r.customer_id}_{r.report_name}_{report_type}"
                if uid not in existing_ids:
                    new_rows.append({
                        "customer_id":       r.customer_id,
                        "customer_name":     r.customer_name,
                        "report_name":       r.report_name,
                        "report_identifier": r.report_identifier,
                        "filter_identifier": r.filter_identifier,
                        "report_type":       report_type,      # ← store it
                        "frequency":         frequency,
                        "day":               day,
                        "custom_days":       custom_days,
                        "file_path":         file_path,
                        "recipients_email":  recipients_email,
                        "date_filter":       date_filter
                    })
                    existing_ids.add(uid)

        if new_rows:
            scheduled_df = pd.concat([scheduled_df, pd.DataFrame(new_rows)], ignore_index=True)

        scheduled_df.drop(columns=['unique_id'], inplace=True)
        scheduled_df.to_excel(sched_path, index=False)

        return jsonify({"message": "Scheduled reports saved successfully!"}), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500



@app.route('/view-scheduled-reports', methods=['GET'])
def view_scheduled_reports():
    """
    Return all scheduled reports, including report_type.
    """
    path = os.path.join('data', 'Scheduled_Reports.xlsx')
    if not os.path.exists(path):
        return jsonify([]), 200

    df = pd.read_excel(path, dtype=str)
    if 'report_type' not in df.columns:
        df['report_type'] = ''   # ensure column exists

    df.fillna('', inplace=True)
    records = df.to_dict(orient='records')
    return jsonify(records), 200


@app.route('/delete-scheduled-report', methods=['POST'])
def delete_scheduled_report():
    """
    Delete a specific scheduled report based on
    customer_name, report_name, frequency, and report_type.
    """
    try:
        data = request.get_json()
        customer_name = data.get('customer_name', '').strip()
        report_name   = data.get('report_name', '').strip()
        frequency     = data.get('frequency', '').strip()
        report_type   = data.get('report_type', '').strip()   # ← read it

        # Validate
        if not (customer_name and report_name and frequency and report_type):
            return jsonify({
                "error": "Invalid data. Must provide customer_name, report_name, frequency, and report_type."
            }), 400

        path = os.path.join("data", "Scheduled_Reports.xlsx")
        if not os.path.exists(path):
            return jsonify({"error": "Scheduled reports file not found."}), 404

        df = pd.read_excel(path, dtype=str)
        df.fillna('', inplace=True)

        before = len(df)
        # Keep everything except the one matching all four fields
        mask = ~(
            (df['customer_name'].str.strip().str.lower() == customer_name.lower()) &
            (df['report_name'].str.strip().str.lower()   == report_name.lower())   &
            (df['frequency'].str.strip().str.lower()     == frequency.lower())     &
            (df['report_type'].str.strip().str.lower()   == report_type.lower())   # ← include it
        )
        updated_df = df[mask]
        after = len(updated_df)

        if before == after:
            return jsonify({"error": "No matching record found to delete."}), 404

        updated_df.to_excel(path, index=False)
        return jsonify({"message": "Report deleted successfully."}), 200

    except Exception as e:
        return jsonify({
            "error": "Failed to delete the report.",
            "details": str(e)
        }), 500
# Path to the Scheduled Reports Excel file
# Path to the Scheduled Reports Excel file
SCHEDULED_REPORTS_FILE = "data/Scheduled_Reports.xlsx"

# Load scheduled reports data
def load_scheduled_reports():
    try:
        return pd.read_excel(SCHEDULED_REPORTS_FILE)
    except Exception as e:
        print(f"Error reading Scheduled Reports Excel: {e}")
        return pd.DataFrame()

# APIAPI to fetch unique customer names
# @app.route("/get-customers")
# def get_customers():
#     df = load_scheduled_reports()
#     if df.empty:
#         return jsonify({"customers": []})

#     unique_customers = df["customer_name"].dropna().unique().tolist()
#     return jsonify({"customers": unique_customers})

# API to fetch filter columns based on selected customer
@app.route("/get-filter-columns")
def get_filter_columns():
    customer_name = request.args.get("customer_name", "")

    df = load_scheduled_reports()
    if df.empty or customer_name not in df["customer_name"].values:
        return jsonify({"filter_columns": []})

    # Get filter columns related to the selected customer
    customer_rows = df[df["customer_name"] == customer_name]
    filter_columns = customer_rows["filter_column"].dropna().unique().tolist()

    return jsonify({"filter_columns": filter_columns})

# API to fetch scheduled reports based on selected customer
@app.route("/filter-scheduled-reports")
def filter_scheduled_reports():
    customer_name = request.args.get("customer_name", "")

    df = load_scheduled_reports()
    if df.empty:
        return jsonify({"reports": []})

    # Filter only reports for the selected customer
    filtered_df = df[df["customer_name"] == customer_name]

    if filtered_df.empty:
        return jsonify({"reports": []})

    reports = filtered_df.to_dict(orient="records")
    return jsonify({"reports": reports})

import json
from flask import request, jsonify

@app.route('/get-alignments', methods=['GET'])
def get_alignments():
    try:
        with open('alignment_dict.json', 'r') as f:
            alignment_data = json.load(f)
        print("Loaded alignment from JSON:", alignment_data)  # Debug print
    except FileNotFoundError:
        from alignment_dictionary import alignment_dict as default_dict
        alignment_data = default_dict
        print("JSON file not found; using default dictionary")
    return jsonify(alignment_data)





@app.route('/update-alignments', methods=['POST'])
def update_alignments():
    try:
        data = request.get_json()
        # Debug log: Print the received data
        print("Received data for alignment update:", data)

        report = data.get('report')
        new_alignment = data.get('data')

        # Load current alignment dictionary from JSON file if it exists
        try:
            with open('alignment_dict.json', 'r') as f:
                current_dict = json.load(f)
        except FileNotFoundError:
            from alignment_dictionary import alignment_dict as default_dict
            current_dict = default_dict

        # Update the alignment for the specified report
        current_dict[report] = new_alignment

        # Write the updated dictionary back to the JSON file
        with open('alignment_dict.json', 'w') as f:
            json.dump(current_dict, f, indent=2)

        print("Updated alignment_dict.json with:", current_dict[report])
        return jsonify({"status": "success"}), 200
    except Exception as e:
        print("Error in update_alignments:", str(e))
        return jsonify({"status": "error", "message": str(e)}), 500
# @app.route('/view-security')

# def view_security():
#     try:
#         result = db.session.execute(text("SELECT * FROM reporting.vw_security_rls"))
#         rows = result.fetchall()
#         return render_template("view_security.html", rows=rows)

#     except OperationalError as e:
#         logging.error("Operational error during /view-security route: %s", str(e))

#         # Check if it's a connection-related error (code 08S01 or message contains 'forcibly closed')
#         if "08S01" in str(e.orig) or "forcibly closed by the remote host" in str(e.orig):
#             return render_template("error.html", message="Connection lost. Please reconnect to the user server.")
#         else:
#             raise  # re-raise if it’s not the specific error


# from flask import render_template

# @app.route('/delete-facility-access/<user_email>/<facility_id>', methods=['POST'])
# def delete_facility_access(user_email, facility_id):
#     try:
#         # Get the user_id from usermaster.
#         result = db.session.execute(
#             text("SELECT user_id FROM dbo.usermaster WHERE user_email = :email"),
#             {'email': user_email}
#         )
#         row = result.fetchone()
#         if not row:
#             return render_template('error.html', message="User not found.")

#         user_id = row._mapping['user_id']

#         # Delete the specific facility access record.
#         db.session.execute(
#             text("DELETE FROM dbo.userfacilityaccess WHERE user_id = :user_id AND facility_id = :facility_id"),
#             {'user_id': user_id, 'facility_id': facility_id}
#         )
#         db.session.commit()

#         # Check if any facility access rows remain for this user.
#         remaining = db.session.execute(
#             text("SELECT COUNT(*) FROM dbo.userfacilityaccess WHERE user_id = :user_id"),
#             {'user_id': user_id}
#         ).scalar()

#         if remaining == 0:
#             # Remove all associated records, then the user itself.
#             db.session.execute(
#                 text("DELETE FROM dbo.userfacilitygroupaccess WHERE user_id = :user_id"),
#                 {'user_id': user_id}
#             )
#             db.session.execute(
#                 text("DELETE FROM dbo.userrolemap WHERE user_id = :user_id"),
#                 {'user_id': user_id}
#             )
#             db.session.execute(
#                 text("DELETE FROM dbo.executiveaccess WHERE user_id = :user_id"),
#                 {'user_id': user_id}
#             )
#             db.session.execute(
#                 text("DELETE FROM dbo.usermaster WHERE user_id = :user_id"),
#                 {'user_id': user_id}
#             )
#             db.session.commit()
#             return render_template(
#                 'error.html',
#                 message="User and all associated access deleted successfully."
#             )

#         # If some facility access remains, just report that.
#         return render_template(
#             'error.html',
#             message="Facility access deleted successfully."
#         )

#     except Exception as e:
#         db.session.rollback()
#         return render_template('error.html', message=f"Error occurred: {e}")


# @app.route('/edit-row/<user_email>', methods=['GET', 'POST'])
# def edit_row(user_email):
#     if request.method == 'POST':
#         new_email = request.form.get('user_email')
#         new_name = request.form.get('user_name')
#         role_name = request.form.get('role_name')
#         facility_id = request.form.get('facility_id')
#         facility_name = request.form.get('facility_name')
#         facility_group_name = request.form.get('facility_group_name')
#         facility_group_id = request.form.get('facility_group_id')
#         is_executive = request.form.get('is_executive')
#         is_facility_lead = request.form.get('is_facility_lead')
#         is_account_manager = request.form.get('is_account_manager')
#         has_facility_group_access = request.form.get('has_facility_group_access')

#         # Get user_id from dbo.usermaster
#         user_id = db.session.execute(
#             text("SELECT user_id FROM dbo.usermaster WHERE user_email = :email"),
#             {'email': user_email}
#         ).fetchone()._mapping['user_id']

#         try:
#             # Update user details
#             db.session.execute(
#                 text("UPDATE dbo.usermaster SET user_email = :email, user_name = :name WHERE user_id = :id"),
#                 {'email': new_email, 'name': new_name, 'id': user_id}
#             )

#             if role_name:
#                 role_id = db.session.execute(
#                     text("SELECT role_id FROM dbo.userrole WHERE role_name = :name"),
#                     {'name': role_name}
#                 ).fetchone()._mapping['role_id']
#                 db.session.execute(
#                     text("DELETE FROM dbo.userrolemap WHERE user_id = :id"),
#                     {'id': user_id}
#                 )
#                 db.session.execute(
#                     text("INSERT INTO dbo.userrolemap (user_id, role_id, is_active) VALUES (:id, :role_id, 1)"),
#                     {'id': user_id, 'role_id': role_id}
#                 )

#             # Delete previous facility and group access entries
#             db.session.execute(
#                 text("DELETE FROM dbo.userfacilityaccess WHERE user_id = :id"),
#                 {'id': user_id}
#             )
#             db.session.execute(
#                 text("DELETE FROM dbo.userfacilitygroupaccess WHERE user_id = :id"),
#                 {'id': user_id}
#             )
#             db.session.execute(
#                 text("DELETE FROM dbo.executiveaccess WHERE user_id = :id"),
#                 {'id': user_id}
#             )

#             if is_facility_lead == "1":
#                 db.session.execute(
#                     text("""
#                     INSERT INTO dbo.userfacilityaccess (user_id, facility_id, access_type, is_active)
#                     VALUES (:id, :fid, 'Facility Lead', 1)
#                     """),
#                     {'id': user_id, 'fid': facility_id}
#                 )
#             elif is_account_manager == "1":
#                 db.session.execute(
#                     text("""
#                     INSERT INTO dbo.userfacilityaccess (user_id, facility_id, access_type, is_active)
#                     VALUES (:id, :fid, 'Account Manager', 1)
#                     """),
#                     {'id': user_id, 'fid': facility_id}
#                 )

#             if has_facility_group_access == "1":
#                 db.session.execute(
#                     text("""
#                     INSERT INTO dbo.userfacilitygroupaccess (user_id, facility_group_id, is_active)
#                     VALUES (:id, :fgid, 1)
#                     """),
#                     {'id': user_id, 'fgid': facility_group_id}
#                 )

#             # Updated executive access logic:
#             if is_executive == "1":
#                 existing_exec = db.session.execute(
#                     text("SELECT * FROM dbo.executiveaccess WHERE user_id = :id"),
#                     {'id': user_id}
#                 ).fetchone()
#                 if existing_exec:
#                     db.session.execute(
#                         text("UPDATE dbo.executiveaccess SET has_full_access = 1, is_active = 1, assigned_date = GETDATE() WHERE user_id = :id"),
#                         {'id': user_id}
#                     )
#                 else:
#                     db.session.execute(
#                         text("INSERT INTO dbo.executiveaccess (user_id, executive_title, has_full_access, assigned_date, is_active) VALUES (:id, 'admin', 1, GETDATE(), 1)"),
#                         {'id': user_id}
#                     )
#             else:
#                 db.session.execute(
#                     text("DELETE FROM dbo.executiveaccess WHERE user_id = :id"),
#                     {'id': user_id}
#                 )

#             db.session.commit()

#             # ✅ Send notification email
#             try:
#                 from email_graph_api import send_email_with_graph_api
#                 from auth_helper import get_graph_access_token

#                 access_token = get_graph_access_token()  # Fetch the access token
#                 sender_email = os.getenv("SENDER_EMAIL")  # Sender's email from .env
#                 recipient_emails = [os.getenv("ADMIN_EMAIL")]  # Admin's email from .env

#                 subject = f"User Edited: {new_email}"
#                 body = (
#                     f"The following user has been edited:\n\n"
#                     f"User Email: {new_email}\n"
#                     f"Name: {new_name}\n"
#                     f"Role: {role_name or 'Not Assigned'}\n"
#                     f"Facility ID: {facility_id or 'Not Assigned'}\n"
#                     f"Facility Group ID: {facility_group_id or 'Not Assigned'}\n"
#                     f"Executive: {'Yes' if is_executive == '1' else 'No'}\n"
#                     f"Facility Lead: {'Yes' if is_facility_lead == '1' else 'No'}\n"
#                     f"Account Manager: {'Yes' if is_account_manager == '1' else 'No'}\n"
#                     f"Group Access: {'Yes' if has_facility_group_access == '1' else 'No'}"
#                 )

#                 send_email_with_graph_api(
#                     access_token=access_token,
#                     sender_email=sender_email,
#                     recipient_emails=recipient_emails,
#                     subject=subject,
#                     body=body
#                 )
#             except Exception as email_error:
#                 print(f"❌ Email sending failed: {email_error}")

#             # Flash success message
#             flash("Edit successful. An email has been sent to the admin.", "success")
#             return redirect('/view-security')

#         except Exception as e:
#             db.session.rollback()
#             flash(f"Error occurred: {e}", "error")
#             return f"Error occurred: {e}", 500

#     else:
#         row = db.session.execute(
#             text("SELECT * FROM reporting.vw_security_rls WHERE user_email = :email"),
#             {'email': user_email}
#         ).fetchone()

#         groups = db.session.execute(
#             text("SELECT facility_group_id, facility_group_name FROM dbo.facilitygroup")
#         ).fetchall()

#         facilities = db.session.execute(
#             text("""
#                 SELECT 
#                     fgm.facility_group_id, 
#                     fg.facility_group_name,
#                     fm.facility_id,
#                     fm.name AS facility_name
#                 FROM dbo.facilitymaster fm
#                 LEFT JOIN dbo.facilitygroupmap fgm ON fm.facility_id = fgm.facility_id AND fgm.is_active = 1
#                 LEFT JOIN dbo.facilitygroup fg ON fgm.facility_group_id = fg.facility_group_id
#                 WHERE fm.is_active = 1
#             """)
#         ).fetchall()

#         # Fetch roles
#         roles = db.session.execute(text("SELECT role_name FROM dbo.userrole")).fetchall()
#         roles = [role._mapping['role_name'] for role in roles]

#         # Fetch the currently assigned role for the user
#         current_role = db.session.execute(text("""
#             SELECT ur.role_name
#             FROM dbo.userrolemap urm
#             JOIN dbo.userrole ur ON urm.role_id = ur.role_id
#             WHERE urm.user_id = (SELECT user_id FROM dbo.usermaster WHERE user_email = :user_email)
#         """), {'user_email': user_email}).fetchone()

#         selected_role = current_role.role_name if current_role else None

#         facility_map = {}
#         reverse_map = {}
#         for f in facilities:
#             group_id = str(f._mapping['facility_group_id']) if f._mapping['facility_group_id'] is not None else 'ungrouped'
#             if group_id not in facility_map:
#                 facility_map[group_id] = []
#             facility_map[group_id].append({
#                 'facility_id': f._mapping['facility_id'],
#                 'facility_name': f._mapping['facility_name']
#             })
#             reverse_map[str(f._mapping['facility_id'])] = {
#                 'facility_group_id': str(f._mapping['facility_group_id']) if f._mapping['facility_group_id'] is not None else '',
#                 'facility_group_name': f._mapping['facility_group_name'] or ''
#             }
                
#         return render_template('edit_form.html',
#                                row=dict(row._mapping),
#                                groups=groups,
#                                facilities=facilities,
#                                facility_map=facility_map,
#                                reverse_map=reverse_map,
#                                roles=roles,
#                                selected_role=selected_role)


# @app.route('/new-user', methods=['GET', 'POST'])
# def new_user():
#     if request.method == 'POST':
#         user_email = request.form.get('user_email')
#         user_name = request.form.get('user_name')
#         role_name = request.form.get('role_name')
#         facility_id = request.form.get('facility_id')
#         facility_group_id = request.form.get('facility_group_id')
#         is_executive = request.form.get('is_executive')
#         is_facility_lead = request.form.get('is_facility_lead')
#         is_account_manager = request.form.get('is_account_manager')
#         has_facility_group_access = request.form.get('has_facility_group_access')

#         # Check if user exists
#         existing_user = db.session.execute(text(
#             "SELECT * FROM dbo.usermaster WHERE user_email = :user_email"
#         ), {'user_email': user_email}).fetchone()

#         if existing_user:
#             flash("User already exists, redirected to assign roles.", "info")
#             return redirect(f'/assign-role/{user_email}')

#         try:
#             # Insert into usermaster
#             db.session.execute(text("""
#                 INSERT INTO dbo.usermaster (user_email, user_name, is_active)
#                 VALUES (:user_email, :user_name, 1)
#             """), {'user_email': user_email, 'user_name': user_name})

#             user_id_result = db.session.execute(text("""
#                 SELECT user_id FROM dbo.usermaster WHERE user_email = :user_email
#             """), {'user_email': user_email}).fetchone()

#             if not user_id_result:
#                 raise ValueError("Failed to retrieve user_id after insertion.")

#             user_id = user_id_result._mapping['user_id']

#             # Insert into userrolemap
#             if role_name:
#                 role_id_result = db.session.execute(text("""
#                     SELECT role_id FROM dbo.userrole WHERE role_name = :role_name
#                 """), {'role_name': role_name}).fetchone()

#                 if role_id_result:
#                     role_id = role_id_result._mapping['role_id']

#                     exists = db.session.execute(text("""
#                         SELECT 1 FROM dbo.userrolemap WHERE user_id = :user_id AND role_id = :role_id
#                     """), {'user_id': user_id, 'role_id': role_id}).fetchone()

#                     if not exists:
#                         db.session.execute(text("""
#                             INSERT INTO dbo.userrolemap (user_id, role_id, is_active)
#                             VALUES (:user_id, :role_id, 1)
#                         """), {'user_id': user_id, 'role_id': role_id})
#                 else:
#                     raise ValueError(f"Role '{role_name}' does not exist.")

#             # Insert facility access
#             if facility_id and is_facility_lead == "1":
#                 db.session.execute(text("""
#                     INSERT INTO dbo.userfacilityaccess (user_id, facility_id, access_type, is_active)
#                     VALUES (:user_id, :facility_id, 'Facility Lead', 1)
#                 """), {'user_id': user_id, 'facility_id': facility_id})

#             # Insert facility access for account managers
#             if facility_id and is_account_manager == "1":
#                 try:
#                     db.session.execute(text("""
#                         INSERT INTO dbo.userfacilityaccess (user_id, facility_id, access_type, is_active)
#                         VALUES (:user_id, :facility_id, 'Account Manager', 1)
#                     """), {'user_id': user_id, 'facility_id': facility_id})
#                 except IntegrityError:
#                     flash("This user already has Account Manager access for the selected facility.", "error")

#             # Facility Group Access
#             if facility_group_id and has_facility_group_access == "1":
#                 db.session.execute(text("""
#                     INSERT INTO dbo.userfacilitygroupaccess (user_id, facility_group_id, is_active)
#                     VALUES (:user_id, :facility_group_id, 1)
#                 """), {'user_id': user_id, 'facility_group_id': facility_group_id})

#             # Executive Access
#             if is_executive == "1":
#                 db.session.execute(text("""
#                     INSERT INTO dbo.executiveaccess (user_id, has_full_access, is_active)
#                     VALUES (:user_id, 1, 1)
#                 """), {'user_id': user_id})

#             db.session.commit()

#             # Redirect to assign-role page after successful user creation
#             flash("User created successfully. Redirecting to assign roles.", "success")
#             return redirect(f'/assign-role/{user_email}')

#         except Exception as e:
#             db.session.rollback()
#             flash(f"Error: {str(e)}", "error")
#             return render_template('new_user.html')

#     return render_template('new_user.html')




# @app.route('/assign-role/<user_email>', methods=['GET', 'POST'])
# def assign_role(user_email):
#     if request.method == 'POST':
#         role_name = request.form.get('role_name')
#         facility_id = request.form.get('facility_id')
#         facility_group_id = request.form.get('facility_group_id')
#         is_executive = request.form.get('is_executive')
#         is_facility_lead = request.form.get('is_facility_lead')
#         is_account_manager = request.form.get('is_account_manager')
#         has_facility_group_access = request.form.get('has_facility_group_access')

#         user_id = db.session.execute(text("SELECT user_id FROM dbo.usermaster WHERE user_email = :email"),
#                                      {'email': user_email}).fetchone()._mapping['user_id']

#         try:
#             if role_name:
#                 role_id = db.session.execute(text("SELECT role_id FROM dbo.userrole WHERE role_name = :name"),
#                                              {'name': role_name}).fetchone()._mapping['role_id']
#                 existing = db.session.execute(text("""
#                     SELECT 1 FROM dbo.userrolemap WHERE user_id = :id AND role_id = :role_id
#                 """), {'id': user_id, 'role_id': role_id}).fetchone()
#                 if not existing:
#                     db.session.execute(text("INSERT INTO dbo.userrolemap (user_id, role_id, is_active) VALUES (:id, :role_id, 1)"),
#                                        {'id': user_id, 'role_id': role_id})

#             if facility_id and is_facility_lead == "1":
#                 db.session.execute(text("INSERT INTO dbo.userfacilityaccess (user_id, facility_id, access_type, is_active) VALUES (:id, :fid, 'Facility Lead', 1)"),
#                                    {'id': user_id, 'fid': facility_id})
#             elif facility_id and is_account_manager == "1":
#                 db.session.execute(text("INSERT INTO dbo.userfacilityaccess (user_id, facility_id, access_type, is_active) VALUES (:id, :fid, 'Account Manager', 1)"),
#                                    {'id': user_id, 'fid': facility_id})

#             if facility_group_id and has_facility_group_access == "1":
#                 db.session.execute(text("INSERT INTO dbo.userfacilitygroupaccess (user_id, facility_group_id, is_active) VALUES (:id, :fgid, 1)"),
#                                    {'id': user_id, 'fgid': facility_group_id})

#             if is_executive == "1":
#                 db.session.execute(text("INSERT INTO dbo.executiveaccess (user_id, has_full_access, is_active) VALUES (:id, 1, 1)"),
#                                    {'id': user_id})

#             db.session.commit()

#             # ✅ Send notification email
#             try:
#                 from email_graph_api import send_email_with_graph_api
#                 from auth_helper import get_graph_access_token

#                 access_token = get_graph_access_token()  # Fetch the access token
#                 sender_email = os.getenv("SENDER_EMAIL")  # Sender's email from .env
#                 recipient_emails = [os.getenv("ADMIN_EMAIL")]  # Admin's email from .env

#                 subject = f"Role Assigned to User: {user_email}"
#                 body = (
#                     f"A role has been assigned to the user.\n\n"
#                     f"User Email: {user_email}\n"
#                     f"Role: {role_name or 'Not Assigned'}\n"
#                     f"Facility ID: {facility_id or 'Not Assigned'}\n"
#                     f"Facility Group ID: {facility_group_id or 'Not Assigned'}\n"
#                     f"Executive: {'Yes' if is_executive == '1' else 'No'}\n"
#                     f"Facility Lead: {'Yes' if is_facility_lead == '1' else 'No'}\n"
#                     f"Account Manager: {'Yes' if is_account_manager == '1' else 'No'}\n"
#                     f"Group Access: {'Yes' if has_facility_group_access == '1' else 'No'}"
#                 )

#                 send_email_with_graph_api(
#                     access_token=access_token,
#                     sender_email=sender_email,
#                     recipient_emails=recipient_emails,
#                     subject=subject,
#                     body=body
#                 )
#             except Exception as email_error:
#                 print(f"❌ Email sending failed: {email_error}")

#             flash("Role assigned successfully. Please allow up to 24 hours for the changes to take effect Mail sent to the Admin", "success")

#             return redirect(f'/assign-role/{user_email}')
#         except Exception as e:
#             db.session.rollback()
#             flash(f"Error occurred: {e}", "error")
#             return f"Error: {e}", 500

#     # For GET requests
#     groups = db.session.execute(text("SELECT facility_group_id, facility_group_name FROM dbo.facilitygroup")).fetchall()

#     facilities = db.session.execute(text("""
#     SELECT 
#         fgm.facility_group_id, 
#         fg.facility_group_name,
#         fm.facility_id,
#         fm.name AS facility_name
#     FROM dbo.facilitymaster fm
#         LEFT JOIN dbo.facilitygroupmap fgm ON fm.facility_id = fgm.facility_id AND fgm.is_active = 1
#         LEFT JOIN dbo.facilitygroup fg ON fgm.facility_group_id = fg.facility_group_id
#     WHERE fm.is_active = 1
# """)).fetchall()

#     # Fetch roles
#     roles = db.session.execute(text("SELECT role_name FROM dbo.userrole")).fetchall()
#     roles = [role._mapping['role_name'] for role in roles]

#     # Fetch the currently assigned role for the user
#     current_role = db.session.execute(text("""
#         SELECT ur.role_name
#         FROM dbo.userrolemap urm
#         JOIN dbo.userrole ur ON urm.role_id = ur.role_id
#         WHERE urm.user_id = (SELECT user_id FROM dbo.usermaster WHERE user_email = :user_email)
#     """), {'user_email': user_email}).fetchone()

#     selected_role = current_role.role_name if current_role else None

#     facility_map = {}
#     reverse_map = {}
#     for row in facilities:
#         group_id = row._mapping['facility_group_id'] or 'ungrouped'
#         if group_id not in facility_map:
#             facility_map[group_id] = []
#         facility_map[group_id].append({
#             'facility_id': row._mapping['facility_id'],
#             'facility_name': row._mapping['facility_name']
#         })

#         # Reverse mapping for facility groups
#         reverse_map[row._mapping['facility_id']] = {
#             'facility_group_id': row._mapping['facility_group_id'] or 'ungrouped',
#             'facility_group_name': row._mapping['facility_group_name'] or 'Ungrouped'
#         }

#     import json
#     return render_template(
#         "assign_role.html",
#         user_email=user_email,
#         groups=groups,
#         facility_map=json.dumps(facility_map),
#         facilities=facilities,
#         reverse_map=json.dumps(reverse_map),
#         roles=roles,
#         selected_role=selected_role
#     )

if __name__ == '__main__':
    """
    Entry point for the Flask application.
    Initializes the server with SocketIO support and enables debug mode.
    """
    socketio.run(app, debug=True, port=5000)
 

# if __name__ == '__main__':
#     from gevent import pywsgi
#     from geventwebsocket.handler import WebSocketHandler

#     # Provide your SSL certificate and key paths below
#     ssl_context = ('path/to/your/cert.pem', 'path/to/your/key.pem')

#     # Create a WSGI server with SSL context
#     server = pywsgi.WSGIServer(
#         ('0.0.0.0', 5002),
#         app,
#         handler_class=WebSocketHandler,
#         keyfile=ssl_context[1],
#         certfile=ssl_context[0]
#     )
#     server.serve_forever()