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

def compute_crime_index(events: List[Dict], area_size_km2: float = 1.0) -> float:
    """
    Crime Index Formula:

    CrimeIndex = [ Σ (Severity_i × Recency_i × VictimFactor_i) / AreaSize ]
                 × FrequencyWeight

    Normalization:
    - Adaptive cap = max(200, n_events × 8) prevents cumulative scores
      from prematurely hitting 100 for high-volume areas.
    - Result clamped to 0–100 scale.
    """
    if not events:
        return 0.0

    raw_sum = 0.0
    for event in events:
        severity = SEVERITY_WEIGHTS.get(event.get("crime_type", "other"), 2)

        # Historical events have no date → use a slightly higher base weight.
        # 0.1 ≈ equally weighted to an event ~46 days old.
        evt_date = event.get("published_at") or event.get("crawled_at")
        if evt_date:
            recency = recency_weight(evt_date)
        else:
            recency = 0.1    # Base weight for historical events to ensure visibility

        victims = event.get("victim_count", 0) or 0
        victim_factor = math.log1p(victims)

        raw_sum += severity * recency * max(victim_factor, 1.0)

    area_normalized = max(area_size_km2, 0.1)
    frequency_weight = math.log1p(len(events))

    raw_index = (raw_sum / area_normalized) * frequency_weight

    # Adaptive normalization cap: scales with volume of data
    raw_cap = max(200.0, len(events) * 10.0)
    normalized = min(100.0, (raw_index / raw_cap) * 100.0)
    return round(normalized, 2)
