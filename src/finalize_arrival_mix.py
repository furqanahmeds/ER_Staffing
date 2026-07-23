"""
Locks in the acuity mix the simulation actually uses for arrivals.

Even after tightening up the keyword mapping (build_acuity_mapping.py
v2), Synthea's acuity distribution still didn't line up with NHAMCS's
national numbers:

    Acuity Level | Synthea (v2) | NHAMCS Target | Diff
    1            | 2.8%         | 15.0%         | -12.2
    2            | 26.3%        | 27.0%         | -0.7
    3            | 59.4%        | 42.5%         | +16.9
    4            | 11.5%        | 15.5%         | -4.0

I could keep tweaking keywords to chase these numbers, but at some
point that stops being validation and starts being curve-fitting to a
target. So instead:

  - Arrivals in the simulation use NHAMCS's national acuity percentages
    directly -- it's the externally validated number.
  - Synthea still earns its keep for arrival timing (the hour-of-day
    shape) and as the sanity check that made the service-time
    assumptions look reasonable in the first place.
"""

import json

# NHAMCS national acuity mix -- used directly as SimPy arrival mix
ARRIVAL_MIX_PCT = {
    1: 15.0,
    2: 27.0,
    3: 42.5,
    4: 15.5,
}

with open("data/arrival_mix.json", "w") as f:
    json.dump(ARRIVAL_MIX_PCT, f, indent=2)

print("Saved data/arrival_mix.json (NHAMCS-derived arrival mix for SimPy model)")
print(json.dumps(ARRIVAL_MIX_PCT, indent=2))
