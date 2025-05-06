# scrapers/police_stats.py

import pandas as pd
from datetime import datetime

def scrape_police_crime_stats(output_dir="data"):
    url = "https://www.police.gov.bd/en/crime_statistics"
    try:
        dfs = pd.read_html(url)
        if dfs:
            crime_data = dfs[0]  # Adjust based on actual table structure
            timestamp = datetime.now().strftime('%Y%m%d_%H%M')
            filename = f"{output_dir}/police_crime_{timestamp}.csv"
            crime_data.to_csv(filename, index=False)
            print(f"[✓] Police data saved to {filename}")
        else:
            print("[!] No tables found on police site")
    except Exception as e:
        print(f"[X] Failed to scrape police crime stats: {e}")
