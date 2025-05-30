# # import os
# # import requests
# # import logging
# # from dotenv import load_dotenv
# # from datetime import datetime

# # # Load environment variables
# # load_dotenv()


# # def get_sharepoint_access_token():
# #     """
# #     Retrieves an access token for Microsoft Graph API to interact with SharePoint.
# #     """
# #     try:
# #         tenant_id = os.getenv("SHAREPOINT_TENANT_ID")
# #         client_id = os.getenv("SHAREPOINT_CLIENT_ID")
# #         client_secret = os.getenv("SHAREPOINT_CLIENT_SECRET")

# #         token_url = f"https://login.microsoftonline.com/{tenant_id}/oauth2/v2.0/token"
# #         payload = {
# #             "grant_type": "client_credentials",
# #             "client_id": client_id,
# #             "client_secret": client_secret,
# #             "scope": "https://graph.microsoft.com/.default"
# #         }

# #         response = requests.post(token_url, data=payload)
# #         response_json = response.json()

# #         if response.status_code == 200:
# #             return response_json.get("access_token")
# #         else:
# #             logging.error(f"❌ Failed to get SharePoint access token: {response_json}")
# #             return None
# #     except Exception as e:
# #         logging.error(f"❌ Error retrieving SharePoint access token: {e}")
# #         return None


# # def ensure_sharepoint_folder_exists(parent_folder, folder_path):
# #     """
# #     Ensures that a given folder path exists in SharePoint inside the specified parent folder.
# #     Fixes duplicate folder creation issue.
# #     """
# #     try:
# #         access_token = get_sharepoint_access_token()
# #         if not access_token:
# #             logging.error("❌ Failed to fetch SharePoint access token. Skipping folder creation.")
# #             return False

# #         drive_id = os.getenv("SHAREPOINT_DRIVE_ID")
# #         sharepoint_base_url = f"https://graph.microsoft.com/v1.0/drives/{drive_id}/root:/"

# #         # ✅ Fix duplicate folder creation by correctly splitting and iterating
# #         folder_list = folder_path.strip("/").split("/")
# #         parent_path = parent_folder  # Start from the given root folder (TEST 1)

# #         for folder in folder_list:
# #             full_folder_path = f"{parent_path}/{folder}"
# #             folder_url = f"{sharepoint_base_url}{full_folder_path}?expand=children"

# #             # Check if the folder exists
# #             response = requests.get(folder_url, headers={"Authorization": f"Bearer {access_token}"})

# #             if response.status_code == 200:
# #                 logging.info(f"📂 SharePoint folder '{full_folder_path}' already exists.")
# #             else:
# #                 # ✅ If folder doesn't exist, create it
# #                 create_folder_url = f"{sharepoint_base_url}{parent_path}:/children"
# #                 payload = {
# #                     "name": folder,
# #                     "folder": {},
# #                     "@microsoft.graph.conflictBehavior": "replace"
# #                 }
# #                 create_response = requests.post(
# #                     create_folder_url, json=payload, headers={"Authorization": f"Bearer {access_token}"}
# #                 )

# #                 if create_response.status_code in [200, 201]:
# #                     logging.info(f"✅ Created SharePoint folder: {full_folder_path}")
# #                 else:
# #                     logging.error(f"❌ Failed to create SharePoint folder '{full_folder_path}': {create_response.text}")
# #                     return False

# #             parent_path = full_folder_path  # Move to the next level

# #         return True

# #     except Exception as e:
# #         logging.error(f"❌ Error ensuring SharePoint folder exists: {e}")
# #         return False


# # def upload_to_sharepoint(file_path, file_path_from_excel, report_name, date_filter, customer_name):
# #     """
# #     Uploads a file to the SharePoint folder based on the file_path from Excel.

# #     Args:
# #         file_path (str): Local path of the file to upload.
# #         file_path_from_excel (str): Base folder name from the Excel input ("ABCD", "TEST 1", etc.).
# #         report_name (str): Name of the report being generated.
# #         date_filter (str): Date filter applied to the report.
# #         customer_name (str): Name of the customer for folder organization.
# #     """
# #     try:
# #         logging.info(f"📡 Uploading {file_path} to SharePoint under folder: {file_path_from_excel}")

# #         # Retrieve access token
# #         access_token = get_sharepoint_access_token()
# #         if not access_token:
# #             logging.error("❌ Failed to fetch SharePoint access token. Skipping upload.")
# #             return False

# #         # Get Drive ID from environment variables
# #         drive_id = os.getenv("SHAREPOINT_DRIVE_ID")
# #         sharepoint_base_url = f"https://graph.microsoft.com/v1.0/drives/{drive_id}/root:/"

# #         # Extract year and month for folder structure
# #         current_year = datetime.now().strftime("%Y")
# #         current_month = datetime.now().strftime("%b")

# #         # ✅ Build folder structure using file_path from Excel as the root
# #         folder_structure = f"{file_path_from_excel}/{current_year}/{current_month}/{report_name}/{report_name} - {date_filter}/{customer_name}"

# #         # Ensure the SharePoint folder exists
# #         if not ensure_sharepoint_folder_exists(file_path_from_excel,
# #                                                f"{current_year}/{current_month}/{report_name}/{report_name} - {date_filter}/{customer_name}"):
# #             logging.error(f"❌ Failed to ensure folder '{folder_structure}' exists. Skipping upload.")
# #             return False

# #         # Get file name
# #         file_name = os.path.basename(file_path)

# #         # Construct the full SharePoint upload URL using the folder path from Excel
# #         sharepoint_upload_url = f"{sharepoint_base_url}{folder_structure}/{file_name}:/content"

# #         # Read file data
# #         with open(file_path, "rb") as file:
# #             file_data = file.read()

# #         # Set headers for API request
# #         headers = {
# #             "Authorization": f"Bearer {access_token}",
# #             "Content-Type": "application/octet-stream"
# #         }

# #         # Upload file to SharePoint
# #         response = requests.put(sharepoint_upload_url, headers=headers, data=file_data)

# #         if response.status_code in [200, 201]:
# #             logging.info(f"✅ Successfully uploaded {file_name} to SharePoint at {folder_structure}")
# #             return True
# #         else:
# #             logging.error(f"❌ Failed to upload {file_name} to SharePoint: {response.text}")
# #             return False

# #     except Exception as e:
# #         logging.error(f"❌ Error uploading to SharePoint: {e}")
# #         return False



# import os
# import requests
# import logging
# from dotenv import load_dotenv
# from datetime import datetime

# # Load environment variables
# load_dotenv()

# # 🔒 Hardcoded SharePoint folder mapping based on report_id + filter_id
# SHAREPOINT_FOLDER_MAP = {
#     ("10064076", "10137003"): "General/RAM Pending Status Reports/Allie",
#     ("10064076", "10137004"): "General/RAM Pending Status Reports/Brian",
#     ("10064076", "10137005"): "General/RAM Pending Status Reports/James",
#     ("10064076", "10137006"): "General/RAM Pending Status Reports/Tiffany",
#     ("10064076", "10137007"): "General/RAM Pending Status Reports/RBH",
#     ("10064358", "10137001"): "General/Rejections Reports/Rejections",
#     ("10062836", "10136998"): "General/PENDING AUTH REPORT/Leanne"
# }


# def get_sharepoint_access_token():
#     """
#     Retrieves an access token for Microsoft Graph API to interact with SharePoint.
#     """
#     tenant_id = os.getenv("SHAREPOINT_TENANT_ID")
#     client_id = os.getenv("SHAREPOINT_CLIENT_ID")
#     client_secret = os.getenv("SHAREPOINT_CLIENT_SECRET")

#     if not all([tenant_id, client_id, client_secret]):
#         logging.error("❌ Missing one or more SharePoint env variables.")
#         return None

#     token_url = f"https://login.microsoftonline.com/{tenant_id}/oauth2/v2.0/token"
#     payload = {
#         "grant_type": "client_credentials",
#         "client_id": client_id,
#         "client_secret": client_secret,
#         "scope": "https://graph.microsoft.com/.default"
#     }

#     try:
#         response = requests.post(token_url, data=payload, timeout=10)
#         response.raise_for_status()
#         data = response.json()
#         return data.get("access_token")
#     except Exception as e:
#         logging.error(f"❌ Failed to retrieve SharePoint token: {e}")
#         return None


# def ensure_sharepoint_folder_exists(parent_folder, folder_path):
#     """
#     Ensures that a given folder path exists in SharePoint inside the specified parent folder.
#     """
#     try:
#         access_token = get_sharepoint_access_token()
#         if not access_token:
#             logging.error("❌ Cannot proceed without access token.")
#             return False

#         drive_id = os.getenv("SHAREPOINT_DRIVE_ID")
#         base_url = f"https://graph.microsoft.com/v1.0/drives/{drive_id}/root:/"
#         folder_list = folder_path.strip("/").split("/")
#         parent_path = parent_folder

#         for folder in folder_list:
#             full_folder_path = f"{parent_path}/{folder}"
#             check_url = f"{base_url}{full_folder_path}?expand=children"

#             response = requests.get(check_url, headers={"Authorization": f"Bearer {access_token}"})
#             if response.status_code == 200:
#                 logging.info(f"📂 Folder already exists: {full_folder_path}")
#             else:
#                 create_url = f"{base_url}{parent_path}:/children"
#                 payload = {
#                     "name": folder,
#                     "folder": {},
#                     "@microsoft.graph.conflictBehavior": "replace"
#                 }
#                 create_resp = requests.post(create_url, headers={"Authorization": f"Bearer {access_token}"}, json=payload)
#                 if create_resp.status_code in (200, 201):
#                     logging.info(f"✅ Created folder: {full_folder_path}")
#                 else:
#                     logging.error(f"❌ Failed to create folder '{full_folder_path}': {create_resp.text}")
#                     return False

#             parent_path = full_folder_path

#         return True

#     except Exception as e:
#         logging.error(f"❌ Error ensuring SharePoint folder exists: {e}")
#         return False


# def upload_to_sharepoint(file_path, report_identifier, filter_identifier, report_name, _date_filter, customer_name, report_type="single"):
    
    
    
    
    
    
#     """
#     Uploads a file to SharePoint under:
#     For single report:
#        <MappedFolder>/<YYYY>/<Month>/<ReportName> - <Date>/<Customer>/<Filename>
#     For bulk reports (report_type=="bulk"):
#        <MappedFolder>/<YYYY>/<Month>/<ReportName> - <Date>/<Filename>
#     """
#     try:
#         # Step 1: Get mapped SharePoint path
#         lookup_key = (str(report_identifier), str(filter_identifier))
#         base_folder = SHAREPOINT_FOLDER_MAP.get(lookup_key)
#         if not base_folder:
#             logging.error(f"❌ No SharePoint folder mapping found for: {lookup_key}")
#             return False

#         # Step 2: Get SharePoint token
#         token = get_sharepoint_access_token()
#         if not token:
#             logging.error("❌ No access token; skipping upload.")
#             return False

#         # Step 3: Setup URL structure
#         drive_id = os.getenv("SHAREPOINT_DRIVE_ID")
#         base_url = f"https://graph.microsoft.com/v1.0/drives/{drive_id}/root:/"

#         today = datetime.now()
#         date_str = today.strftime("%Y-%m-%d")
#         year = today.strftime("%Y")
#         month = today.strftime("%b")

#         # Build folder structure based on report type
#         if report_type.lower() == "bulk":
#             folder_structure = f"{base_folder}/{year}/{month}/{report_name} - {date_str}"
#         else:
#             folder_structure = f"{base_folder}/{year}/{month}/{report_name} - {date_str}/{customer_name}"

#         # Step 4: Ensure folder exists
#         if not ensure_sharepoint_folder_exists(base_folder, f"{year}/{month}/{report_name} - {date_str}" + ("" if report_type.lower() == "bulk" else f"/{customer_name}")):
#             return False

#         # Step 5: Upload file
#         filename = os.path.basename(file_path)
#         upload_url = f"{base_url}{folder_structure}/{filename}:/content"

#         with open(file_path, "rb") as f:
#             file_data = f.read()

#         headers = {
#             "Authorization": f"Bearer {token}",
#             "Content-Type": "application/octet-stream"
#         }

#         response = requests.put(upload_url, headers=headers, data=file_data)

#         if response.status_code in (200, 201):
#             logging.info(f"✅ Uploaded '{filename}' to '{folder_structure}'")
#             return True
#         else:
#             logging.error(f"❌ Upload failed ({response.status_code}): {response.text}")
#             return False

#     except Exception as e:
#         logging.error(f"❌ Exception in upload_to_sharepoint: {e}")
#         return False

