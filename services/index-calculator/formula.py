import math
from datetime import datetime, timezone
from typing import List, Dict

# Crime type severity weights (1-10)
SEVERITY_WEIGHTS = {
    "murder":     10,
    "rape":        9,
    "kidnapping":  8,
    "assault":     6,
    "robbery":     6,
    "theft":       4,
    "vandalism":   3,
    "accident":    3,
    "other":       2,
    "none":        1,
}

# Exponential decay constant (lambda)
# Higher = faster decay. 0.05 means a 14-day-old event has ~50% weight.
DECAY_LAMBDA = 0.05

def recency_weight(event_date: datetime) -> float:
    """Apply exponential decay based on how old the event is."""
    now = datetime.now(timezone.utc)
    if event_date.tzinfo is None:
        event_date = event_date.replace(tzinfo=timezone.utc)
    days_ago = max(0, (now - event_date).days)
    return math.exp(-DECAY_LAMBDA * days_ago)

def compute_crime_index(events: List[Dict], area_size_km2: float = 1.0) -> float:
    """
    Crime Index Formula:
    
    CrimeIndex = [ Σ (Severity_i × Recency_i × VictimFactor_i) / AreaSize ]
                 × FrequencyWeight
    
    Where:
    - Severity_i      = weight by crime type (1-10)
    - Recency_i       = e^(-λ × days_ago)  [exponential decay]
    - VictimFactor_i  = log(1 + victim_count)
    - AreaSize        = normalized area size in km² (defaults to 1.0 for now)
    - FrequencyWeight = log(1 + total_events_last_30_days)
    
    Result is normalized to 0–100 scale.
    """
    if not events:
        return 0.0

    raw_sum = 0.0
    for event in events:
        severity = SEVERITY_WEIGHTS.get(event.get("crime_type", "other"), 2)
        
        # Determine event date
        evt_date = event.get("published_at") or event.get("crawled_at") or datetime.now(timezone.utc)
        recency = recency_weight(evt_date)
        
        victims = event.get("victim_count", 0) or 0
        victim_factor = math.log1p(victims)  # log(1 + victims)

        raw_sum += severity * recency * max(victim_factor, 1.0)

    area_normalized = max(area_size_km2, 0.1)  # avoid division by zero
    frequency_weight = math.log1p(len(events))

    raw_index = (raw_sum / area_normalized) * frequency_weight

    # Normalize to 0-100 (empirically capped at raw=200 for Dhaka scale)
    normalized = min(100.0, (raw_index / 200.0) * 100.0)
    return round(normalized, 2)
