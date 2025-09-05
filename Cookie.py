import pandas as pd
import requests
import json
import numpy as np  # Handle NaN values

# Mist API Details
API_BASE_URL = "https://api.ac2.mist.com/api/v1"
API_TOKEN = "Your Mist API Token"  # Replace with your actual Mist API token

# Headers for API requests
HEADERS = {
    "Authorization": f"Token {API_TOKEN}",
    "Content-Type": "application/json"
}

# -------------------- LOAD EXCEL FILE --------------------
file_path = "DCF_Template.xlsx"  # Replace with actual file path
df = pd.read_excel(file_path, sheet_name="Org Details", header=None)

# -------------------- STEP 1: GET ORG DETAILS --------------------
org_name = df.iloc[1, 0]  # New Org Name
source_org_id = str(df.iloc[1, 7]).strip()  # Org ID to clone from (column H remains unchanged)

if source_org_id.lower() == "nan" or source_org_id == "":
    print("❌ ERROR: No valid Org ID found in H2 of the DCF file.")
    exit()

# -------------------- STEP 2: CLONE ORG USING THE CORRECT METHOD --------------------
clone_payload = {"name": org_name}  # New Org Name

clone_response = requests.post(f"{API_BASE_URL}/orgs/{source_org_id}/clone", headers=HEADERS, json=clone_payload)

if clone_response.status_code in [200, 201]:
    new_org_id = clone_response.json().get("id")
    print(f"✅ Org Cloned Successfully: {org_name} (ID: {new_org_id})")
else:
    print(f"❌ Failed to clone org. Response: {clone_response.text}")
    exit()

# -------------------- STEP 3: PROCESS SITES FROM DCF --------------------
variable_columns = {}  # Store column indexes & variable names
for col in range(10, len(df.columns)):  # Start at column 11 (new shifted index)
    header_value = df.iloc[4, col]  # Row 5 (zero-indexed: 4)
    if pd.isna(header_value):  # Stop when hitting an empty column
        break
    if isinstance(header_value, str) and header_value.startswith("{{") and header_value.endswith("}}"):
        variable_columns[col] = header_value.strip("{}")  # Remove curly braces

site_rows = df.iloc[5:].dropna(how="all")

for _, row in site_rows.iterrows():
    site_data = {
        "name": row[0],  # Site Name
        "address": row[1],  # Address
        "country_code": row[2],  # Country
        "latlng": {  # Fix for proper Mist API format
            "lat": row[3],  # Latitude
            "lng": row[4],  # Longitude
        },
        "timezone": row[5],  # Time Zone (new column F, for sites only)
        "contact_name": row[6],  # Contact Name
        "contact_email": row[7],  # Contact Email
        "contact_phone": row[8],  # Contact Phone
        "site_type": row[9],  # Site Type
    }

    # Convert NaN values to None for JSON compliance
    for key, value in site_data.items():
        if isinstance(value, float) and (np.isnan(value) or not np.isfinite(value)):
            site_data[key] = None  

    # Debugging: Print the site payload
    print(f"📤 Site Payload for {site_data['name']}: {json.dumps(site_data, indent=2)}")

    site_response = requests.post(f"{API_BASE_URL}/orgs/{new_org_id}/sites", headers=HEADERS, json=site_data)

    if site_response.status_code in [200, 201]:
        site_id = site_response.json().get("id")
        print(f"✅ Site Created: {site_data['name']} (ID: {site_id})")

        # -------------------- APPLY SITE VARIABLES --------------------
        site_variables = {}
        for col, var_name in variable_columns.items():
            variable_value = row[col] if pd.notna(row[col]) else None
            site_variables[var_name] = variable_value  

        payload = {"vars": site_variables}

        # Debugging: Print site variable payload
        print(f"📤 Sending Site Variables for {site_data['name']}: {json.dumps(payload, indent=2)}")

        var_response = requests.put(f"{API_BASE_URL}/sites/{site_id}/setting", headers=HEADERS, json=payload)

        if var_response.status_code in [200, 201]:
            print(f"   ✅ Site Variables Set Successfully for {site_data['name']}")
        else:
            print(f"   ❌ Failed to set site variables. Response: {var_response.text}")

    else:
        print(f"❌ Failed to create site: {site_data['name']}. Response: {site_response.text}")
