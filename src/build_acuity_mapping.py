"""
Filter Synthea encounters.csv for emergency department visits and assign
a simplified acuity level (1 = most critical, 5 = least urgent) based on
the encounter's REASONDESCRIPTION.

This mapping is a modeling assumption -- document it explicitly in your
write-up. Real EDs use a formal Emergency Severity Index (ESI) protocol
based on vital signs and resource needs, not just diagnosis text.
"""

import pandas as pd

# ---- Load data ----
encounters = pd.read_csv("data/encounters.csv")

# ---- Filter for emergency encounters only ----
ed = encounters[encounters["ENCOUNTERCLASS"] == "emergency"].copy()
print(f"Total encounters: {len(encounters)}")
print(f"Emergency encounters: {len(ed)}")

# ---- Parse timestamps ----
ed["START"] = pd.to_datetime(ed["START"])
ed["STOP"] = pd.to_datetime(ed["STOP"])
ed["LOS_MINUTES"] = (ed["STOP"] - ed["START"]).dt.total_seconds() / 60

# ---- Acuity mapping (simplified, keyword-based) ----
# ESI 1 = immediate/life-threatening
# ESI 2 = high risk, should be seen very quickly
# ESI 3 = moderate, needs multiple resources
# ESI 4 = low, needs one resource
# ESI 5 = least urgent, minimal resources

ACUITY_KEYWORDS = {
    1: ["cardiac arrest", "respiratory arrest", "shock", "stroke",
        "myocardial infarction", "anaphylaxis"],
    2: ["chest pain", "sepsis", "asthma", "fracture", "seizure",
        "acute", "severe"],
    3: ["laceration", "abdominal pain", "infection", "appendicitis",
        "dehydration", "injury"],
    4: ["sprain", "minor", "rash", "earache", "sore throat"],
    5: ["wellness", "screening", "checkup", "follow-up"],
}

def assign_acuity(reason):
    if pd.isna(reason):
        return 3  # default to moderate if no reason given
    reason_lower = str(reason).lower()
    for level, keywords in ACUITY_KEYWORDS.items():
        if any(kw in reason_lower for kw in keywords):
            return level
    return 3  # default fallback

ed["ACUITY"] = ed["REASONDESCRIPTION"].apply(assign_acuity)

# ---- Quick sanity check ----
print("\nAcuity level distribution:")
print(ed["ACUITY"].value_counts().sort_index())

print("\nAverage length of stay by acuity level (minutes):")
print(ed.groupby("ACUITY")["LOS_MINUTES"].agg(["mean", "median", "count"]))

# ---- Save filtered + labeled dataset ----
ed.to_csv("data/ed_encounters_with_acuity.csv", index=False)
print("\nSaved to data/ed_encounters_with_acuity.csv")
