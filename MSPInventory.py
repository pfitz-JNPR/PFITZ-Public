import requests
import pandas as pd
import json

# -------------------- CLOUD REGION MAPPING --------------------
"""
Mist Cloud Region Reference:

| Cloud Name | Key       | Provider | Management URL         | API Base URL                        |
|------------|-----------|----------|------------------------|-------------------------------------|
| Global01   | mist      | AWS      | manage.mist.com        | https://api.mist.com/api/v1         |
| Global02   | gc1       | GCP      | manage.gc1.mist.com    | https://api.gc1.mist.com/api/v1     |
| Global03   | ac2       | AWS      | manage.ac2.mist.com    | https://api.ac2.mist.com/api/v1     |
| Global04   | gc2       | GCP      | manage.gc2.mist.com    | https://api.gc2.mist.com/api/v1     |
| EMEA01     | eu        | AWS      | manage.eu.mist.com     | https://api.eu.mist.com/api/v1      |
| EMEA02     | gc3       | GCP      | manage.gc3.mist.com    | https://api.gc3.mist.com/api/v1     |
| APAC01     | ac5       | AWS      | manage.ac5.mist.com    | https://api.ac5.mist.com/api/v1     |
"""

# Define region mapping
REGION_LOOKUP = {
    "Global01": "",
    "Global02": ".gc1",
    "Global03": ".ac2",
    "Global04": ".gc2",
    "EMEA01": ".eu",
    "EMEA02": ".gc3",
    "APAC01": ".ac5"
}

# -------------------- CONFIGURATION --------------------
# 
# To generate your API_TOKEN, Log into one of your Mist Orgs, and click on 
# your account Avatar, then Click "My Account"
# In the API Token section Click "Create Token", give it a name and
# click "Generate", copy to clipboard, paste over the appropriate text below
#
# The MSP_ID can be found in the MSP Dashboard under MSP, then MSP Info
# Copy it to the clipboard, paste over the appropriate text below
#
# ----------------- PARAMETERS TO ENTER -----------------
CLOUD_REGION = "Global03"  # Change this to switch regions (e.g., Global01, EMEA01, APAC01)
API_TOKEN = "REPLACE_WITH_YOUR_API_TOKEN"
MSP_ID = "REPLACE_WITH_YOUR_MSP_ID"
# --------------- END PARAMETERS TO ENTER ---------------

MIST_API_DOMAIN = REGION_LOOKUP[CLOUD_REGION]
API_BASE_URL = f"https://api{MIST_API_DOMAIN}.mist.com/api/v1"

HEADERS = {
    "Authorization": f"Token {API_TOKEN}",
    "Content-Type": "application/json"
}

# -------------------- HELPER FUNCTIONS --------------------
def get_orgs_in_msp(msp_id):
    url = f"{API_BASE_URL}/msps/{msp_id}/orgs"
    response = requests.get(url, headers=HEADERS)
    return response.json() if response.ok else []

def get_sites_in_org(org_id):
    url = f"{API_BASE_URL}/orgs/{org_id}/sites"
    response = requests.get(url, headers=HEADERS)
    return response.json() if response.ok else []

def get_device_stats(site_id):
    url = f"{API_BASE_URL}/sites/{site_id}/stats/devices?type=all&status=all"
    response = requests.get(url, headers=HEADERS)
    return response.json() if response.ok else []

# -------------------- MAIN INVENTORY COLLECTION --------------------
def collect_full_inventory(msp_id):
    all_data = []
    orgs = get_orgs_in_msp(msp_id)

    for org in orgs:
        org_id = org.get("id")
        org_name = org.get("name")
        print(f"📦 Processing Org: {org_name}")

        sites = get_sites_in_org(org_id)
        for site in sites:
            site_id = site.get("id")
            site_name = site.get("name")
            print(f"  🔍 Checking Site: {site_name}")

            devices = get_device_stats(site_id)
            for d in devices:
                all_data.append({
                    "Org Name": org_name,
                    "Org ID": org_id,
                    "Site Name": site_name,
                    "MAC": d.get("mac"),
                    "Type": d.get("type"),
                    "Model": d.get("model"),
                    "Serial": d.get("serial"),
                    "Name": d.get("name"),
                    "Hostname": d.get("hostname"),
                    "IP": d.get("ip"),
                    "External IP": d.get("ext_ip"),
                    "Status": d.get("status"),
                    "Firmware": d.get("version"),
                    "Uptime (s)": d.get("uptime"),
                    "# Clients": d.get("num_clients"),
                    "# WLANs": d.get("num_wlans"),
                    "Tx bps": d.get("tx_bps"),
                    "Rx bps": d.get("rx_bps"),
                    "Tx bytes": d.get("tx_bytes"),
                    "Rx bytes": d.get("rx_bytes"),
                    "Tx pkts": d.get("tx_pkts"),
                    "Rx pkts": d.get("rx_pkts"),
                    "CPU Temp (C)": d.get("env_stat", {}).get("cpu_temp"),
                    "Ambient Temp (C)": d.get("env_stat", {}).get("ambient_temp"),
                    "Humidity (%)": d.get("env_stat", {}).get("humidity"),
                    "Power Source": d.get("power_src"),
                    "PoE Budget": d.get("power_budget"),
                    "Locked": d.get("locked")
                })

    return pd.DataFrame(all_data)

# -------------------- EXPORT TO CSV --------------------
if __name__ == "__main__":
    df = collect_full_inventory(MSP_ID)
    df.to_csv("msp_inventory.csv", index=False)
    print("✅ Inventory export complete: msp_inventory.csv")
