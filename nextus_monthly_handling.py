import pandas as pd
import logging
import numpy as np
# Set up logging
logging.basicConfig(level=logging.ERROR)

def transform_nextus_monthly_report(file_path):
    """
    Transforms the 'NEXTUS MONTHLY DETAIL PAYMENT REPORT' by:
    - Extracting data after detecting the 'Facility Name' row.
    - Normalizing patient names and formatting financial columns.
    - Calculating the 'Percentage' column.
    - Inserting 'Total' rows after each patient group.
    - Formatting monetary columns with $ and commas.
    - Applying bold formatting to total rows in the output Excel file.
    """
    try:
        # Load the data into a DataFrame
        data = pd.read_excel(file_path, header=None)

        # Find the row index where "Facility Name" is located
        header_row = data[data.apply(lambda row: row.astype(str).str.contains('Facility Name').any(), axis=1)].index[0]

        # Load the DataFrame starting from the header row
        df = pd.read_excel(file_path, skiprows=header_row)

        # Convert date columns to proper format
        for col in df.select_dtypes(include=['datetime64']).columns:
            df[col] = df[col].dt.strftime('%Y-%m-%d')

        # Normalize patient names (strip spaces and lowercase)
        df['Patient Full Name'] = df['Patient Full Name'].str.strip().str.lower()

        # Convert financial columns to numeric format
        df['Payment Total Paid'] = pd.to_numeric(df['Payment Total Paid'].replace('[\\$,]', '', regex=True),
                                                 errors='coerce').fillna(0)
        df['Charge Amount'] = pd.to_numeric(df['Charge Amount'].replace('[\\$,]', '', regex=True),
                                            errors='coerce').fillna(0)

        # ✅ Calculate Percentage for Every Row
        df['Percentage'] = df.apply(
            lambda row: f"{int(round((row['Payment Total Paid'] / row['Charge Amount']) * 100))}%"
            if row['Charge Amount'] != 0 else "0%", axis=1
        )

        # Grouping by Patient Name and calculating totals
        grouped = df.groupby('Patient Full Name').agg({
            'Payment Total Paid': 'sum',
            'Charge Amount': 'sum'
        }).reset_index()

        grouped['Percentage'] = grouped.apply(
            lambda row: f"{int(round((row['Payment Total Paid'] / row['Charge Amount']) * 100))}%"
            if row['Charge Amount'] != 0 else "0%", axis=1
        )

        # Create new DataFrame with empty rows after each patient group
        new_rows = []
        for patient_name in df['Patient Full Name'].unique():
            patient_data = df[df['Patient Full Name'] == patient_name].copy()
            new_rows.append(patient_data)  # Add all records for the patient

            # Fetch the calculated totals
            patient_total = grouped[grouped['Patient Full Name'] == patient_name]

            if not patient_total.empty:
                total_row = patient_data.iloc[0].copy()  # Copy structure
                total_row['Patient Full Name'] = f"{patient_name} Total"
                total_row['Payment Total Paid'] = f"${patient_total['Payment Total Paid'].values[0]:,.2f}"
                total_row['Charge Amount'] = f"${patient_total['Charge Amount'].values[0]:,.2f}"
                total_row['Percentage'] = patient_total['Percentage'].values[0]

                # Clear other columns
                for col in total_row.index:
                    if col not in ['Patient Full Name', 'Payment Total Paid', 'Charge Amount', 'Percentage']:
                        total_row[col] = ''

                new_rows.append(pd.DataFrame([total_row]))  # Append as DataFrame

        # Convert list to DataFrame
        df_with_totals = pd.concat(new_rows).reset_index(drop=True)

        # Format currency columns properly
        df_with_totals['Payment Total Paid'] = df_with_totals['Payment Total Paid'].apply(
            lambda x: f"${x:,.2f}" if isinstance(x, (int, float)) else x)
        df_with_totals['Charge Amount'] = df_with_totals['Charge Amount'].apply(
            lambda x: f"${x:,.2f}" if isinstance(x, (int, float)) else x)

        return df_with_totals
    except Exception as e:
        logging.error(f"Error transforming 'NEXTUS MONTHLY DETAIL PAYMENT REPORT': {e}")
        return None  # Prevents script from breaking