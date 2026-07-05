"""
Day 3 (final): Arrival mix decision for the SimPy model.

FINDING:
Synthea's keyword-derived acuity mix, even after expanding keyword
coverage (see build_acuity_mapping.py v2), diverges meaningfully from
NHAMCS national benchmarks:

    Acuity Level | Synthea (v2) | NHAMCS Target | Diff
    1            | 2.8%         | 15.0%         | -12.2
    2            | 26.3%        | 27.0%         | -0.7
    3            | 59.4%        | 42.5%         | +16.9
    4            | 11.5%        | 15.5%         | -4.0

DECISION:
Rather than continue tuning keyword lists to force Synthea's mix toward
NHAMCS's numbers (which would risk overfitting the mapping to a target
rather than reflecting genuine clinical judgment), this project uses:

  - NHAMCS national percentages for the ARRIVAL MIX (acuity distribution
    of incoming patients) in the SimPy simulation, since this is an
    externally validated real-world benchmark.
  - Synthea for arrival TIMING patterns (hour-of-day volume shape) and
    as the source that validated the service-time distribution
    assumptions produce plausible results.

This is a documented modeling decision, not a data-quality workaround --
it should be stated plainly in the project write-up's V&V section.
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
