import sys
import os
import math
from datetime import datetime, timedelta, timezone

# Add service dir to path to import formula
sys.path.append(os.path.abspath('services/index-calculator'))
from formula import compute_crime_index

def verify_weighting():
    results = []
    now = datetime.now(timezone.utc)
    
    # 1. Test Historical Dataset Record (No Date)
    historical_event = [{"crime_type": "murder", "victim_count": 1}]
    hist_score = compute_crime_index(historical_event, emphasize_history=True)
    live_hist_score = compute_crime_index(historical_event, emphasize_history=False)
    
    results.append("--- Historical Dataset Record (No Date) ---")
    results.append(f"Score (History Mode, Weight 2.5): {hist_score}")
    results.append(f"Score (Live Mode, Weight 0.1):    {live_hist_score}")
    results.append(f"Ratio: {hist_score / max(live_hist_score, 0.1):.2f}x increase\n")
    
    # 2. Test Live Events in Cumulative/History Mode
    recent_date = now - timedelta(days=1)
    old_date = now - timedelta(days=800) # > 2 years
    
    recent_event = [{"crime_type": "murder", "victim_count": 1, "published_at": recent_date}]
    old_event = [{"crime_type": "murder", "victim_count": 1, "published_at": old_date}]
    
    recent_score_hist = compute_crime_index(recent_event, emphasize_history=True)
    old_score_hist = compute_crime_index(old_event, emphasize_history=True)
    
    results.append("--- Live Events in Cumulative Mode (Emphasize History) ---")
    results.append(f"Recent (1 day ago, weight ~1.0): {recent_score_hist}")
    results.append(f"Old (800 days ago, weight 2.0):    {old_score_hist}")
    results.append(f"Ratio (Old/Recent): {old_score_hist / max(recent_score_hist, 0.1):.2f}x (Expect ~2.0x)\n")

    # 3. Test Live Events in Standard 30-day Mode
    recent_score_live = compute_crime_index(recent_event, emphasize_history=False)
    old_score_live = compute_crime_index(old_event, emphasize_history=False)
    
    results.append("--- Live Events in Standard 30-day Mode ---")
    results.append(f"Recent (1 day ago, weight ~0.95): {recent_score_live}")
    results.append(f"Old (800 days ago, weight ~0.0):  {old_score_live}")
    results.append(f"Recency Effect: {recent_score_live / max(old_score_live, 0.01):.2f}x decay for old event")

    with open('weight_results.txt', 'w') as f:
        f.write('\n'.join(results))

if __name__ == "__main__":
    verify_weighting()
