import pandas as pd

ed = pd.read_csv("data/ed_encounters_with_acuity.csv")

print("=== LOS distribution details by acuity ===")
for level in sorted(ed["ACUITY"].unique()):
    subset = ed[ed["ACUITY"] == level]["LOS_MINUTES"]
    print(f"\nAcuity {level} (n={len(subset)}):")
    print(subset.describe())
    print(f"  Unique values (first 10): {sorted(subset.unique())[:10]}")
    print(f"  Max: {subset.max():.1f} min ({subset.max()/60:.1f} hours)")

print("\n=== Encounters over 6 hours (likely admissions, not ED-only stays) ===")
long_stays = ed[ed["LOS_MINUTES"] > 360]
print(f"Count: {len(long_stays)} out of {len(ed)} ({100*len(long_stays)/len(ed):.1f}%)")
print(long_stays[["REASONDESCRIPTION", "LOS_MINUTES", "ACUITY"]].head(10))

print("\n=== Encounter DESCRIPTION field (may indicate admission vs ED-only) ===")
print(ed["DESCRIPTION"].value_counts().head(15))
