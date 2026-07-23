"""
Filters Synthea's encounters.csv down to ED visits and assigns each one
a simplified acuity level (1 = most critical, 4 = least urgent) based on
keywords in REASONDESCRIPTION.

Second pass at this mapping -- my first attempt defaulted about 60% of
encounters to level 3 because the keyword list was too thin. I dug into
which REASONDESCRIPTION values were falling through unmatched
(diagnose_acuity_mapping.py) and expanded the lists to cover them.

Worth being upfront that this is still a rough stand-in for a real
triage protocol. Actual EDs use the Emergency Severity Index, which
factors in vitals and resource needs, not just diagnosis text.
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

# ---- Acuity mapping (expanded, keyword-based) ----
# ESI 1 = immediate/life-threatening
# ESI 2 = high risk, should be seen very quickly
# ESI 3 = moderate, needs multiple resources
# ESI 4 = low, needs one resource
# Ordered dict matters: more specific/severe terms checked first so a
# condition doesn't accidentally match a broader, less urgent keyword.

ACUITY_KEYWORDS = {
    1: [
        "cardiac arrest", "respiratory arrest", "shock", "stroke",
        "cerebrovascular accident", "myocardial infarction", "anaphylaxis",
        "gunshot wound", "suicidal poisoning", "cva",
    ],
    2: [
        "chest pain", "sepsis", "asthma", "fracture", "seizure",
        "overdose", "congestive heart failure", "pneumonia",
        "pyelonephritis", "suspected lung cancer", "acute", "severe",
    ],
    3: [
        "laceration", "abdominal pain", "infection", "appendicitis",
        "dehydration", "injury", "chronic pain", "migraine",
        "normal pregnancy", "fibromyalgia",
    ],
    4: [
        "sprain", "minor", "rash", "earache", "sore throat",
        "impacted molars", "dislocation of temporomandibular",
    ],
}

def assign_acuity(reason):
    if pd.isna(reason):
        return 3  # no reason given -- defaulting to moderate acuity
    reason_lower = str(reason).lower()
    for level, keywords in ACUITY_KEYWORDS.items():
        if any(kw in reason_lower for kw in keywords):
            return level
    return 3  # nothing matched -- defaulting to moderate acuity

ed["ACUITY"] = ed["REASONDESCRIPTION"].apply(assign_acuity)

# ---- Confirm match coverage improved ----
def match_status(reason):
    if pd.isna(reason):
        return "NO_REASON"
    reason_lower = str(reason).lower()
    for level, keywords in ACUITY_KEYWORDS.items():
        if any(kw in reason_lower for kw in keywords):
            return "MATCHED"
    return "NO_MATCH"

ed["match_status"] = ed["REASONDESCRIPTION"].apply(match_status)
print("\nMatch coverage:")
print(ed["match_status"].value_counts())

# ---- Quick sanity check ----
print("\nAcuity level distribution:")
print(ed["ACUITY"].value_counts().sort_index())
print("\nAs percentage:")
print((ed["ACUITY"].value_counts(normalize=True).sort_index() * 100).round(1))

print("\nAverage length of stay by acuity level (minutes):")
print(ed.groupby("ACUITY")["LOS_MINUTES"].agg(["mean", "median", "count"]))

# ---- Save filtered + labeled dataset ----
ed = ed.drop(columns=["match_status"])
ed.to_csv("data/ed_encounters_with_acuity.csv", index=False)
print("\nSaved to data/ed_encounters_with_acuity.csv")