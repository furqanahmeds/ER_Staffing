import pandas as pd

ed = pd.read_csv("data/encounters.csv")
ed = ed[ed["ENCOUNTERCLASS"] == "emergency"].copy()

ACUITY_KEYWORDS = {
    1: ["cardiac arrest", "respiratory arrest", "shock", "stroke",
        "myocardial infarction", "anaphylaxis"],
    2: ["chest pain", "sepsis", "asthma", "fracture", "seizure",
        "acute", "severe"],
    3: ["laceration", "abdominal pain", "infection", "appendicitis",
        "dehydration", "injury"],
    4: ["sprain", "minor", "rash", "earache", "sore throat"],
}

def matched_level(reason):
    if pd.isna(reason):
        return "NO_REASON"
    reason_lower = str(reason).lower()
    for level, keywords in ACUITY_KEYWORDS.items():
        if any(kw in reason_lower for kw in keywords):
            return str(level)
    return "NO_MATCH"

ed["match_status"] = ed["REASONDESCRIPTION"].apply(matched_level)

print("=== Match status breakdown ===")
print(ed["match_status"].value_counts())
print(f"\nTotal: {len(ed)}")

print("\n=== Top 20 REASONDESCRIPTION values that did NOT match any keyword ===")
no_match = ed[ed["match_status"] == "NO_MATCH"]
print(no_match["REASONDESCRIPTION"].value_counts().head(20))
