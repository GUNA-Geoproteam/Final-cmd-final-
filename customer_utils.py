# customer_utils.py
import os
import logging
import pandas as pd

# # Load customer data from Excel (this can be adapted if you later want to move it to a config or DB)
customer_data = pd.read_excel("data/customer-logo-master.xlsx")
# customer_logo_map = customer_data.set_index("customer_id")[["right_logo_file_name"]].to_dict("index")
customer_logo_map = customer_data.set_index("customer_id")[["right_logo_file_name", "isActive", "facility_acronym"]].to_dict("index")


# def get_customer_logo(customer_id):
#     """
#     Retrieve the logo path for a given customer. Returns default logo if specific logo is missing.
#     """
#     default_logo = os.path.join("static", "images", "Nextus-logo.png")
#     logo_filename = customer_logo_map.get(customer_id, {}).get("right_logo_file_name")
#     if logo_filename:
#         logo_path = os.path.join("static", "images", "customer_logos", logo_filename)
#         if os.path.exists(logo_path):
#             return logo_path
#         else:

#             logging.warning(f"Logo file not found for Customer ID {customer_id}")
#     return default_logo



def get_customer_logo(customer_id):
    """
    Retrieve the logo path for a given customer. Returns fallback logo (no_name.png) if specific logo is missing.
    """
    fallback_logo = os.path.join("static", "images", "no_name.png")  # Now using no_name.png instead of Nextus-logo.png
    logo_filename = customer_logo_map.get(customer_id, {}).get("right_logo_file_name")

    if logo_filename:
        logo_path = os.path.join("static", "images", "customer_logos", logo_filename)
        if os.path.exists(logo_path):
            return logo_path
        else:
            logging.warning(f"Logo file not found for Customer ID {customer_id}. Using fallback logo.")

    return fallback_logo  # Always return no_name.png if no specific logo exists


def is_customer_active(customer_id):
    """
    Checks if a customer is active (Y) or inactive (N) based on customer-logo-master.xlsx.
    Returns True if active, False if inactive.
    """
    customer_info = customer_logo_map.get(customer_id, {})
    is_active = customer_info.get("isActive", "N")
    print(f"Customer ID: {customer_id}, isActive: {is_active}")  # For verification
    return is_active


def get_facility_acronym(customer_id):
    """
    Retrieves the facility acronym for a given customer ID.
    """
    return customer_logo_map.get(customer_id, {}).get("facility_acronym", "Unknown")  # Default to 'Unknown' if missing

# def get_facility_acronym(customer_id):
#     """
#     Retrieves the facility acronym for a given customer ID.
#     Returns both the acronym and a status message for verification.
#     """
#     facility_acronym = customer_logo_map.get(customer_id, {}).get("facility_acronym", "Unknown")
#     verification_message = f"Facility Acronym for Customer ID {customer_id}: {facility_acronym}"
#     return facility_acronym, verification_message



