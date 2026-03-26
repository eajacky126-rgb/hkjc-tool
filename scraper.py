import requests
import pandas as pd
import os
from datetime import datetime

# --- CONFIG ---
API_KEY = "14de051f2c5f97f2ad8898a88bc7cb0e"  # Get this for free from scraperapi.com
TARGET_DATE = datetime.now().strftime("%Y/%m/%d") 
URL = f"https://racing.hkjc.com/racing/information/English/Racing/LocalResults.aspx?RaceDate={TARGET_DATE}"

def run_automated_sync():
    # Use ScraperAPI as a proxy to hide the cloud IP
    proxy_url = f"http://scraperapi:{API_KEY}@proxy-server.scraperapi.com:8001"
    proxies = {"http": proxy_url, "https": proxy_url}

    print(f"[*] Fetching data for {TARGET_DATE}...")
    try:
        # verify=False handles SSL issues often found in proxies
        response = requests.get(URL, proxies=proxies, verify=False, timeout=60)
        
        if response.status_code == 200:
            tables = pd.read_html(response.text)
            all_data = []
            for df in tables:
                if 'Horse' in df.columns:
                    df['date'] = TARGET_DATE
                    all_data.append(df)
            
            if all_data:
                final_df = pd.concat(all_data)
                # Save to CSV in the repo
                final_df.to_csv("data/latest_results.csv", index=False)
                print("[+] Data saved to data/latest_results.csv")
            else:
                print("[-] No tables found.")
        else:
            print(f"[-] Blocked: {response.status_code}")
    except Exception as e:
        print(f"[-] Error: {e}")

if __name__ == "__main__":
    run_automated_sync()
