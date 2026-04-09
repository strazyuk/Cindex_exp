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

# Source-based multipliers
SOURCE_WEIGHTS = {
    "historical": 4.0,
    "live":       1.0
}

# Exponential decay constant (lambda) for live data
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
    Reworked Crime Index Formula:
    
    1. Base Score = Σ (Severity × SourceWeight × TimeWeight × VictimFactor)
    2. DensityScore = BaseScore / AreaSize
    3. Log-Frequency = log1p(DensityScore) × log1p(TotalEvents)
    4. Normalization = Sigmoid/Log based scaling to 0-100
    """
    if not events:
        return 0.0

    raw_sum = 0.0
    for event in events:
        severity = SEVERITY_WEIGHTS.get(event.get("crime_type", "other"), 2)
        
        # Source Multiplier
        source = event.get("source", "live")
        source_mult = SOURCE_WEIGHTS.get(source, 1.0) if emphasize_history else 1.0
        
        # Time weighting (Only for live data, or if date exists)
        evt_date = event.get("published_at") or event.get("crawled_at")
        time_mult = 1.0
        if evt_date:
            if not emphasize_history:
                time_mult = recency_weight(evt_date)
            else:
                # In historical mode, dated events don't decay, they stay relevant
                time_mult = 1.0

        victims = event.get("victim_count", 0) or 0
        victim_factor = math.log1p(victims)

        raw_sum += severity * source_mult * time_mult * max(victim_factor, 1.0)

    # Normalize by area
    area_normalized = max(area_size_km2, 1.0)
    density_score = raw_sum / area_normalized
    
    # Frequency impact (non-linear)
    frequency_boost = math.log1p(len(events))
    
    # Logarithmic scaling to avoid being squashed by high-density areas
    # This makes the scale more "dynamic" and easier to see differences
    log_index = math.log1p(density_score * frequency_boost)
    
    # Scale log_index to 0-100 range. 
    # A log_index of 6.0 (approx 400 linear) starts reaching the top.
    normalized = (log_index / 6.0) * 100.0
    
    return round(min(100.0, normalized), 2)
