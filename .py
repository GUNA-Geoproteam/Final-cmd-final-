import os
from flask import Flask, render_template, request, redirect
from flask_sqlalchemy import SQLAlchemy
from dotenv import load_dotenv  # Corrected import
from sqlalchemy import text

# 1) Load .env
load_dotenv()  # Fixed typo

# 2) Flask + SQLAlchemy setup
app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = (
    f"postgresql://{os.getenv('DB_USER')}:{os.getenv('DB_PASSWORD')}@"
    f"{os.getenv('DB_HOST')}:{os.getenv('DB_PORT')}/{os.getenv('DB_NAME')}"
)
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# 3) Simple test route
@app.route('/test-db')
def test_db():
    # raw SQL to verify connection
    result = db.session.execute(text("SELECT version();"))
    version = result.scalar()
    return f"Connected to: {version}"


@app.route('/debug-env')
def debug_env():
    return {
        "DB_HOST": os.getenv("DB_HOST"),
        "DB_PORT": os.getenv("DB_PORT"),
        "DB_NAME": os.getenv("DB_NAME"),
        "DB_USER": os.getenv("DB_USER"),
        # don't print passwords in production!
        "DB_PASSWORD": os.getenv("DB_PASSWORD")
    }


from sqlalchemy import text

@app.route('/view-security')
def view_security():
    db.session.execute(text("SET search_path TO dbo, public;"))
    result = db.session.execute(text("SELECT * FROM vw_security_rls;"))
    rows = [dict(row._mapping) for row in result.fetchall()]
    return render_template('view_security.html', rows=rows)




@app.route('/')
def home():
    return '''
        <h1>Welcome!</h1>
        <p>Try the following routes:</p>
        <ul>
            <li><a href="/test-db">Test DB Connection</a></li>
            <li><a href="/debug-env">View Environment Variables</a></li>
            <li><a href="/view-security">View Security RLS Table</a></li>
        </ul>
    '''


@app.route('/delete-row/<user_email>', methods=['POST'])
def delete_row(user_email):
    db.session.execute(text("DELETE FROM dbo.vw_security_rls WHERE user_email = :email"), {'email': user_email})
    db.session.commit()
    return "Deleted successfully. <a href='/view-security'>Go back</a>"


# 1 edit working code

# @app.route('/edit-row/<user_email>', methods=['GET', 'POST'])
# def edit_row(user_email):
#     if request.method == 'POST':
#         new_name = request.form.get('user_name')
#         db.session.execute(text("UPDATE dbo.vw_security_rls SET user_name = :name WHERE user_email = :email"),
#                    {'name': new_name, 'email': user_email})

#         db.session.commit()
#         return redirect('/view-security')
#     else:
#         result = db.session.execute(text("SELECT * FROM dbo.vw_security_rls WHERE user_email = :email"),
#                               {'email': user_email})

#         row = dict(result.fetchone()._mapping)
#         return render_template('edit_form.html', row=row)




# 2 edit working code


# @app.route('/edit-row/<user_email>', methods=['GET', 'POST'])
# def edit_row(user_email):
#     if request.method == 'POST':
#         # Get the new values from the form
#         new_email = request.form.get('user_email')
#         new_name = request.form.get('user_name')
#         # (Add other fields as needed)

#         # Execute the update (which will fire your trigger)
#         db.session.execute(text("""
#             UPDATE dbo.vw_security_rls
#             SET user_email = :new_email,
#                 user_name  = :new_name
#             WHERE user_email = :old_email
#         """), {'new_email': new_email, 'new_name': new_name, 'old_email': user_email})
#         db.session.commit()
#         return redirect('/view-security')
#     else:
#         result = db.session.execute(text("""
#             SELECT * FROM dbo.vw_security_rls WHERE user_email = :email
#         """), {'email': user_email})
#         row = dict(result.fetchone()._mapping)
#         return render_template('edit_form.html', row=row)

@app.route('/edit-row/<user_email>', methods=['GET', 'POST'])
def edit_row(user_email):
    if request.method == 'POST':
        # Retrieve new values from the form
        new_email = request.form.get('user_email')
        new_name = request.form.get('user_name')
        # (Include other fields as needed)

        # The update query uses the original email (from URL) as the key.
        db.session.execute(text("""
            UPDATE dbo.vw_security_rls
            SET user_email = :new_email,
                user_name  = :new_name
            WHERE user_email = :old_email
        """), {'new_email': new_email, 'new_name': new_name, 'old_email': user_email})
        db.session.commit()
        return redirect('/view-security')
    else:
        result = db.session.execute(text("""
            SELECT * FROM dbo.vw_security_rls WHERE user_email = :email
        """), {'email': user_email})
        row = dict(result.fetchone()._mapping)
        return render_template('edit_form.html', row=row)
#kotha working



# @app.route('/new-user', methods=['GET', 'POST'])
# def new_user():
#     if request.method == 'POST':
#         user_email = request.form.get('user_email')
#         user_name = request.form.get('user_name')
#         role_name = request.form.get('role_name')
#         facility_id = request.form.get('facility_id')
#         facility_name = request.form.get('facility_name')
#         facility_group_id = request.form.get('facility_group_id')
#         facility_group_name = request.form.get('facility_group_name')
#         is_executive = request.form.get('is_executive')
#         is_facility_lead = request.form.get('is_facility_lead')
#         is_account_manager = request.form.get('is_account_manager')
#         has_facility_group_access = request.form.get('has_facility_group_access')

#         # Start a transaction
#         try:
#             # Insert into usermaster
#             db.session.execute(text("""
#                 INSERT INTO dbo.usermaster (user_email, user_name)
#                 VALUES (:user_email, :user_name)
#             """), {'user_email': user_email, 'user_name': user_name})
            
#             # Insert into userrolemap if role_name is provided
#             if role_name:
#                 # First, lookup the role_id from dbo.userrole
#                 role_result = db.session.execute(text("""
#                     SELECT role_id FROM dbo.userrole WHERE role_name = :role_name
#                 """), {'role_name': role_name})
#                 role_row = role_result.fetchone()
#                 if role_row:
#                     role_id = role_row._mapping['role_id']
#                     # Now, insert into userrolemap (assuming user_id is auto-generated and you retrieve it)
#                     # For example, you might need to fetch the newly created user_id from usermaster.
#                     user_result = db.session.execute(text("""
#                         SELECT user_id FROM dbo.usermaster WHERE user_email = :user_email
#                     """), {'user_email': user_email})
#                     user_id = user_result.fetchone()._mapping['user_id']
#                     db.session.execute(text("""
#                         INSERT INTO dbo.userrolemap (user_id, role_id, is_active)
#                         VALUES (:user_id, :role_id, 1)
#                     """), {'user_id': user_id, 'role_id': role_id})
            
#             # Similarly, insert into facilityaccess and facilitygroupaccess tables as needed.
#             # For simplicity, the example is kept brief.

#             db.session.commit()
#             return redirect('/view-security')
#         except Exception as e:
#             db.session.rollback()
#             return str(e)
#     else:
#         return render_template('new_user.html')

# @app.route('/new-user', methods=['GET', 'POST'])
# def new_user():
#     if request.method == 'POST':
#         user_email = request.form.get('user_email')
#         user_name = request.form.get('user_name')
#         role_name = request.form.get('role_name')
#         facility_id = request.form.get('facility_id')
#         facility_name = request.form.get('facility_name')
#         facility_group_id = request.form.get('facility_group_id')
#         facility_group_name = request.form.get('facility_group_name')
#         is_executive = request.form.get('is_executive')
#         is_facility_lead = request.form.get('is_facility_lead')
#         is_account_manager = request.form.get('is_account_manager')
#         has_facility_group_access = request.form.get('has_facility_group_access')

#         try:
#             # Insert into usermaster
#             db.session.execute(text("""
#                 INSERT INTO dbo.usermaster (user_email, user_name)
#                 VALUES (:user_email, :user_name)
#             """), {'user_email': user_email, 'user_name': user_name})
            
#             # Retrieve new user_id (assuming it's auto-generated)
#             user_result = db.session.execute(text("""
#                 SELECT user_id FROM dbo.usermaster WHERE user_email = :user_email
#             """), {'user_email': user_email})
#             user_row = user_result.fetchone()
#             if not user_row:
#                 return "Error retrieving new user."
#             user_id = user_row._mapping['user_id']

#             # Insert into userrolemap if role_name is provided
#             if role_name:
#                 role_result = db.session.execute(text("""
#                     SELECT role_id FROM dbo.userrole WHERE role_name = :role_name
#                 """), {'role_name': role_name})
#                 role_row = role_result.fetchone()
#                 if role_row:
#                     role_id = role_row._mapping['role_id']
#                     db.session.execute(text("""
#                         INSERT INTO dbo.userrolemap (user_id, role_id, is_active)
#                         VALUES (:user_id, :role_id, 1)
#                     """), {'user_id': user_id, 'role_id': role_id})

#             # Insert into userfacilityaccess if facility_id is provided
#             if facility_id:
#                 # Determine access type based on form values
#                 access_type = None
#                 if is_facility_lead == "1":
#                     access_type = "Facility Lead"
#                 elif is_account_manager == "1":
#                     access_type = "Account Manager"
#                 # Insert only if an access type is determined
#                 if access_type:
#                     db.session.execute(text("""
#                         INSERT INTO dbo.userfacilityaccess (user_id, facility_id, access_type, is_active)
#                         VALUES (:user_id, :facility_id, :access_type, 1)
#                     """), {'user_id': user_id, 'facility_id': facility_id, 'access_type': access_type})
            
#             # Insert into userfacilitygroupaccess if facility_group_id is provided
#             if facility_group_id:
#                 db.session.execute(text("""
#                     INSERT INTO dbo.userfacilitygroupaccess (user_id, facility_group_id, is_active)
#                     VALUES (:user_id, :facility_group_id, 1)
#                 """), {'user_id': user_id, 'facility_group_id': facility_group_id})
            
#             # Insert into executiveaccess if is_executive is "1"
#             if is_executive == "1":
#                 db.session.execute(text("""
#                     INSERT INTO dbo.executiveaccess (user_id, is_active)
#                     VALUES (:user_id, 1)
#                 """), {'user_id': user_id})
            
#             db.session.commit()
#             return redirect('/view-security')
#         except Exception as e:
#             db.session.rollback()
#             return str(e)
#     else:
#         return render_template('new_user.html')




# working perfect code

# from flask import Flask, render_template, request, redirect, flash
# # ... other imports ...
# app.secret_key = 'your_secret_key_here'  # Ensure you have a secure secret key

# @app.route('/new-user', methods=['GET', 'POST'])
# def new_user():
#     if request.method == 'POST':
#         user_email = request.form.get('user_email')
#         user_name = request.form.get('user_name')
#         role_name = request.form.get('role_name')
#         facility_id = request.form.get('facility_id')
#         facility_name = request.form.get('facility_name')
#         facility_group_id = request.form.get('facility_group_id')
#         facility_group_name = request.form.get('facility_group_name')
#         is_executive = request.form.get('is_executive')
#         is_facility_lead = request.form.get('is_facility_lead')
#         is_account_manager = request.form.get('is_account_manager')
#         has_facility_group_access = request.form.get('has_facility_group_access')

#         # Duplicate email check:
#         existing_user = db.session.execute(text("""
#             SELECT * FROM dbo.usermaster WHERE user_email = :user_email
#         """), {'user_email': user_email}).fetchone()
#         if existing_user:
#             flash("Email already exists. Please use a different email.", "error")
#             return render_template('new_user.html')
        
#         try:
#             # Insert into usermaster
#             db.session.execute(text("""
#                 INSERT INTO dbo.usermaster (user_email, user_name)
#                 VALUES (:user_email, :user_name)
#             """), {'user_email': user_email, 'user_name': user_name})
            
#             # Retrieve new user_id (assuming it's auto-generated)
#             user_result = db.session.execute(text("""
#                 SELECT user_id FROM dbo.usermaster WHERE user_email = :user_email
#             """), {'user_email': user_email})
#             user_row = user_result.fetchone()
#             if not user_row:
#                 return "Error retrieving new user."
#             user_id = user_row._mapping['user_id']

#             # Insert into userrolemap if role_name is provided
#             if role_name:
#                 role_result = db.session.execute(text("""
#                     SELECT role_id FROM dbo.userrole WHERE role_name = :role_name
#                 """), {'role_name': role_name})
#                 role_row = role_result.fetchone()
#                 if role_row:
#                     role_id = role_row._mapping['role_id']
#                     db.session.execute(text("""
#                         INSERT INTO dbo.userrolemap (user_id, role_id, is_active)
#                         VALUES (:user_id, :role_id, 1)
#                     """), {'user_id': user_id, 'role_id': role_id})
            
#             # Insert into userfacilityaccess if facility_id is provided
#             if facility_id:
#                 # Determine access type based on form values
#                 access_type = None
#                 if is_facility_lead == "1":
#                     access_type = "Facility Lead"
#                 elif is_account_manager == "1":
#                     access_type = "Account Manager"
#                 # Insert only if an access type is determined
#                 if access_type:
#                     db.session.execute(text("""
#                         INSERT INTO dbo.userfacilityaccess (user_id, facility_id, access_type, is_active)
#                         VALUES (:user_id, :facility_id, :access_type, 1)
#                     """), {'user_id': user_id, 'facility_id': facility_id, 'access_type': access_type})
            
#             # Insert into userfacilitygroupaccess if facility_group_id is provided
#             if facility_group_id:
#                 db.session.execute(text("""
#                     INSERT INTO dbo.userfacilitygroupaccess (user_id, facility_group_id, is_active)
#                     VALUES (:user_id, :facility_group_id, 1)
#                 """), {'user_id': user_id, 'facility_group_id': facility_group_id})
            
#             # Insert into executiveaccess if is_executive is "1"
#             if is_executive == "1":
#                 db.session.execute(text("""
#                     INSERT INTO dbo.executiveaccess (user_id, is_active)
#                     VALUES (:user_id, 1)
#                 """), {'user_id': user_id})
            
#             db.session.commit()
#             return redirect('/view-security')
#         except Exception as e:
#             db.session.rollback()
#             return str(e)
#     else:
#         return render_template('new_user.html')



from flask import Flask, render_template, request, redirect, flash
from sqlalchemy import text
from sqlalchemy.exc import IntegrityError

app.secret_key = 'your_secret_key_here'  # Make sure this is a strong secret key

@app.route('/new-user', methods=['GET', 'POST'])
def new_user():
    if request.method == 'POST':
        user_email = request.form.get('user_email')
        user_name = request.form.get('user_name')
        role_name = request.form.get('role_name')
        facility_id = request.form.get('facility_id')
        facility_name = request.form.get('facility_name')
        facility_group_id = request.form.get('facility_group_id')
        facility_group_name = request.form.get('facility_group_name')
        is_executive = request.form.get('is_executive')
        is_facility_lead = request.form.get('is_facility_lead')
        is_account_manager = request.form.get('is_account_manager')
        has_facility_group_access = request.form.get('has_facility_group_access')

        # Check for existing email
        existing_user = db.session.execute(text("""
            SELECT * FROM dbo.usermaster WHERE user_email = :user_email
        """), {'user_email': user_email}).fetchone()
        if existing_user:
            flash("Email already exists. Please use a different email.", "error")
            return render_template('new_user.html')

        try:
            # Step 1: Insert into usermaster
            db.session.execute(text("""
                INSERT INTO dbo.usermaster (user_email, user_name)
                VALUES (:user_email, :user_name)
            """), {'user_email': user_email, 'user_name': user_name})

            # Step 2: Retrieve user_id
            user_result = db.session.execute(text("""
                SELECT user_id FROM dbo.usermaster WHERE user_email = :user_email
            """), {'user_email': user_email})
            user_row = user_result.fetchone()
            if not user_row:
                return "Error retrieving new user."
            user_id = user_row._mapping['user_id']

            # Step 3: Insert into userrolemap
            if role_name:
                role_result = db.session.execute(text("""
                    SELECT role_id FROM dbo.userrole WHERE role_name = :role_name
                """), {'role_name': role_name})
                role_row = role_result.fetchone()
                if role_row:
                    role_id = role_row._mapping['role_id']
                    db.session.execute(text("""
                        INSERT INTO dbo.userrolemap (user_id, role_id, is_active)
                        VALUES (:user_id, :role_id, 1)
                    """), {'user_id': user_id, 'role_id': role_id})

            # Step 4: Insert into userfacilityaccess
            if facility_id:
                access_type = None
                if is_facility_lead == "1":
                    access_type = "Facility Lead"
                elif is_account_manager == "1":
                    access_type = "Account Manager"
                if access_type:
                    db.session.execute(text("""
                        INSERT INTO dbo.userfacilityaccess (user_id, facility_id, access_type, is_active)
                        VALUES (:user_id, :facility_id, :access_type, 1)
                    """), {
                        'user_id': user_id,
                        'facility_id': facility_id,
                        'access_type': access_type
                    })

            # Step 5: Insert into userfacilitygroupaccess
            if facility_group_id and facility_group_id != "None":
                db.session.execute(text("""
                    INSERT INTO dbo.userfacilitygroupaccess (user_id, facility_group_id, is_active)
                    VALUES (:user_id, :facility_group_id, 1)
                """), {'user_id': user_id, 'facility_group_id': int(facility_group_id)})

            # Step 6: Insert into executiveaccess
            if is_executive == "1":
                db.session.execute(text("""
                    INSERT INTO dbo.executiveaccess (user_id, is_active)
                    VALUES (:user_id, 1)
                """), {'user_id': user_id})

            db.session.commit()
            return redirect('/view-security')

        except IntegrityError as e:
            db.session.rollback()
            if 'fk_userfacilityaccess_facility_id' in str(e.orig):
                flash(f"There is no facility with number {facility_id}", "error")
                return render_template('new_user.html')
            elif 'userfacilitygroupaccess_facility_group_id_fkey' in str(e.orig):
                flash(f"There is no facility group with number {facility_group_id}", "error")
                return render_template('new_user.html')
            else:
                flash(f"Integrity error: {str(e.orig)}", "error")
                return render_template('new_user.html')
        except Exception as e:
            db.session.rollback()
            flash(f"Unexpected error: {str(e)}", "error")
            return render_template('new_user.html')
    else:
        return render_template('new_user.html')

if __name__ == '__main__':
    app.run(debug=True)