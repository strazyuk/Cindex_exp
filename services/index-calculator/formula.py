import math
from datetime import datetime, timezone
from typing import List, Dict

# Crime type severity weights (1-10)
# Includes labels from live data AND historical dataset
SEVERITY_WEIGHTS = {
    # Live pipeline labels
    "murder":     10,
    "rape":        9,
    "kidnapping":  8,
    "assault":     6,
    "robbery":     6,
    "fraud":       5,
    "theft":       4,
    "vandalism":   3,
    "accident":    3,
    "other":       2,
    "none":        1,
    # Historical dataset labels
    "kidnap":      8,  # alias for kidnapping
    "bodyfound":   7,  # found body (suspicious death)
}

# Exponential decay constant (lambda)
# 0.05 means a 14-day-old event has ~50% weight.
DECAY_LAMBDA = 0.05

def recency_weight(event_date: datetime) -> float:
    """Apply exponential decay based on how old the event is."""
    now = datetime.now(timezone.utc)
    if event_date.tzinfo is None:
        event_date = event_date.replace(tzinfo=timezone.utc)
    days_ago = max(0, (now - event_date).days)
    return math.exp(-DECAY_LAMBDA * days_ago)

def compute_crime_index(events: List[Dict], area_size_km2: float = 1.0, emphasize_history: bool = False) -> float:
    """
    Crime Index Formula:

    CrimeIndex = [ Σ (Severity_i × Weight_i × VictimFactor_i) / AreaSize ]
                 × FrequencyWeight

    New Historical Emphasis Logic:
    - If emphasize_history=True:
        - Events without dates (historical dataset) get a massive Weight (2.5)
        - Dated events increase in weight slightly as they age (establishing "risk basement")
    - Else (30d index):
        - Uses standard exponential decay.
    """
    if not events:
        return 0.0

    now = datetime.now(timezone.utc)
    raw_sum = 0.0
    for event in events:
        severity = SEVERITY_WEIGHTS.get(event.get("crime_type", "other"), 2)

        evt_date = event.get("published_at") or event.get("crawled_at")
        if evt_date:
            if evt_date.tzinfo is None:
                evt_date = evt_date.replace(tzinfo=timezone.utc)
            
            if emphasize_history:
                # Older events = more "established" risk. 
                # Weight grows from 1.0 (recent) to 2.0 (older than 2 years)
                days_ago = max(0, (now - evt_date).days)
                weight = min(2.0, 1.0 + (days_ago / 730.0))
            else:
                weight = recency_weight(evt_date)
        else:
            # Historical dataset records have no date.
            # When emphasizing history, they become the "bedrock" of the score.
            weight = 2.5 if emphasize_history else 0.1

        victims = event.get("victim_count", 0) or 0
        victim_factor = math.log1p(victims)

        raw_sum += severity * weight * max(victim_factor, 1.0)

    area_normalized = max(area_size_km2, 0.1)
    frequency_weight = math.log1p(len(events))

    raw_index = (raw_sum / area_normalized) * frequency_weight

    # Adaptive normalization cap: scales with volume of data
    raw_cap = max(200.0, len(events) * 10.0)
    normalized = min(100.0, (raw_index / raw_cap) * 100.0)
    return round(normalized, 2)
