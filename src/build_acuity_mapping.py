"""
Filter Synthea encounters.csv for emergency department visits and assign
a simplified acuity level (1 = most critical, 5 = least urgent) based on
the encounter's REASONDESCRIPTION.

v2: expanded keyword coverage based on diagnostic review of actual
REASONDESCRIPTION values that fell through to the default bucket in v1
(see diagnose_acuity_mapping.py output). Roughly 60% of encounters were
previously defaulting to level 3 due to missing keyword coverage --
this version explicitly maps the specific conditions found in the data.

This mapping remains a modeling assumption -- document it explicitly in
your write-up. Real EDs use a formal Emergency Severity Index (ESI)
protocol based on vital signs and resource needs, not diagnosis text alone.
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
        return 3  # documented assumption: unspecified reason -> moderate
    reason_lower = str(reason).lower()
    for level, keywords in ACUITY_KEYWORDS.items():
        if any(kw in reason_lower for kw in keywords):
            return level
    return 3  # documented assumption: no keyword match -> moderate

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