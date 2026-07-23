"""
Trade-space search across staffing configurations.

Sweeps triage nurses, treatment bays, and physicians together, and
checks each combination against REQ-1 through REQ-3 plus a weighted
staffing cost. Calling this a "trade-space search" rather than an
optimization on purpose -- there's rarely one dominant answer here, the
point is to map out the cost/performance frontier and pick a
defensible recommendation off it.

Cost weights: physicians weighted heaviest (highest labor cost per hour
in a real ED), nurses moderate, bays lowest (closer to a capital/space
cost than an hourly labor cost). These are relative ratios I chose to
be directionally realistic -- not pulled from actual wage data.
"""

import simpy
import numpy as np
import json
import pandas as pd
import itertools

with open("data/arrival_mix.json") as f:
    ARRIVAL_MIX = json.load(f)
with open("data/arrival_rate.json") as f:
    ARRIVAL_RATE = json.load(f)
with open("data/service_time_distributions.json") as f:
    SERVICE_TIMES = json.load(f)

ACUITY_LEVELS = [int(k) for k in ARRIVAL_MIX.keys()]
ACUITY_WEIGHTS = [ARRIVAL_MIX[str(a)] for a in ACUITY_LEVELS]

PHYSICIAN_CONTACT_FRACTION = 0.2
SIM_DURATION_MIN = 60 * 24 * 7
WARMUP_MIN = 60 * 24
RANDOM_SEED = 12345

REQ2_TARGETS_MIN = {1: 20, 2: 40, 3: 75, 4: 150}
REQ3_CEILING_MIN = 240

COST_WEIGHTS = {"triage_nurses": 1.5, "treatment_bays": 1.0, "physicians": 4.0}

# ---- Candidate staffing configurations to search ----
# Grid kept intentionally modest (~budget-realistic ranges around the
# baseline) rather than an exhaustive search, since each config requires
# a full 7-day simulation run.
CANDIDATE_CONFIGS = []
for nurses in [1, 2, 3]:
    for bays in [16, 18, 20, 22, 24]:
        for physicians in [4, 5, 6, 7, 8]:
            CANDIDATE_CONFIGS.append({
                "triage_nurses": nurses,
                "treatment_bays": bays,
                "physicians": physicians,
            })


class ERSystem:
    def __init__(self, env, staffing):
        self.env = env
        self.triage_nurse = simpy.Resource(env, capacity=staffing["triage_nurses"])
        self.treatment_bay = simpy.PriorityResource(env, capacity=staffing["treatment_bays"])
        self.physician = simpy.Resource(env, capacity=staffing["physicians"])


def patient(env, patient_id, acuity, er, rng, results):
    arrival_time = env.now
    record = {"patient_id": patient_id, "acuity": acuity, "arrival_time": arrival_time}

    with er.triage_nurse.request() as req:
        yield req
        record["triage_start"] = env.now
        triage_duration = max(1, rng.lognormal(mean=1.6, sigma=0.4))
        yield env.timeout(triage_duration)
        record["triage_end"] = env.now

    with er.treatment_bay.request(priority=acuity) as req:
        yield req
        record["bay_start"] = env.now
        record["wait_time_min"] = record["bay_start"] - record["triage_end"]

        treat_params = SERVICE_TIMES[str(acuity)]["treatment_time_lognormal"]
        treatment_min = max(5, rng.lognormal(mean=treat_params["mu"], sigma=treat_params["sigma"]))
        physician_contact_min = max(2, treatment_min * PHYSICIAN_CONTACT_FRACTION)

        with er.physician.request() as phys_req:
            yield phys_req
            yield env.timeout(physician_contact_min)

        remaining = treatment_min - physician_contact_min
        if remaining > 0:
            yield env.timeout(remaining)

    record["departure_time"] = env.now
    results.append(record)


def arrival_process(env, er, rng, results):
    patient_id = 0
    avg_per_day = ARRIVAL_RATE["avg_arrivals_per_day"]
    hourly_fraction = ARRIVAL_RATE["hourly_fraction"]
    while True:
        current_hour = int((env.now // 60) % 24)
        hour_frac = hourly_fraction[str(current_hour)]
        rate_per_min = max((avg_per_day * hour_frac) / 60, 0.001)
        yield env.timeout(rng.exponential(1 / rate_per_min))
        patient_id += 1
        acuity = rng.choice(ACUITY_LEVELS, p=np.array(ACUITY_WEIGHTS) / sum(ACUITY_WEIGHTS))
        env.process(patient(env, patient_id, int(acuity), er, rng, results))


def run_config(staffing, seed=RANDOM_SEED):
    rng = np.random.default_rng(seed)
    env = simpy.Environment()
    er = ERSystem(env, staffing)
    results = []
    env.process(arrival_process(env, er, rng, results))
    env.run(until=SIM_DURATION_MIN)
    return pd.DataFrame(results)


def evaluate_config(staffing):
    df = run_config(staffing)
    steady = df[df["arrival_time"] >= WARMUP_MIN].copy()

    if len(steady) == 0:
        return None

    triage_wait = steady["triage_start"] - steady["arrival_time"]
    req1_pct = (triage_wait <= 10).mean() * 100

    req2_results = {}
    for acuity, target in REQ2_TARGETS_MIN.items():
        subset = steady[steady["acuity"] == acuity]["wait_time_min"]
        req2_results[acuity] = (subset <= target).mean() * 100 if len(subset) else 0

    over = (steady["wait_time_min"] > REQ3_CEILING_MIN).sum()
    req3_pct_ok = (1 - over / len(steady)) * 100

    all_req2_pass = all(v >= 90 for v in req2_results.values())
    req1_pass = req1_pct >= 90
    req3_pass = over == 0
    all_pass = req1_pass and all_req2_pass and req3_pass

    cost = (staffing["triage_nurses"] * COST_WEIGHTS["triage_nurses"] +
            staffing["treatment_bays"] * COST_WEIGHTS["treatment_bays"] +
            staffing["physicians"] * COST_WEIGHTS["physicians"])

    return {
        "triage_nurses": staffing["triage_nurses"],
        "treatment_bays": staffing["treatment_bays"],
        "physicians": staffing["physicians"],
        "cost": cost,
        "patients_completed": len(steady),
        "req1_pct": round(req1_pct, 1),
        "req2_acuity1_pct": round(req2_results[1], 1),
        "req2_acuity2_pct": round(req2_results[2], 1),
        "req2_acuity3_pct": round(req2_results[3], 1),
        "req2_acuity4_pct": round(req2_results[4], 1),
        "req3_pct_within_ceiling": round(req3_pct_ok, 1),
        "avg_wait_min": round(steady["wait_time_min"].mean(), 1),
        "p90_wait_min": round(steady["wait_time_min"].quantile(0.9), 1),
        "all_requirements_pass": all_pass,
    }


if __name__ == "__main__":
    print(f"Evaluating {len(CANDIDATE_CONFIGS)} staffing configurations...")
    rows = []
    for i, config in enumerate(CANDIDATE_CONFIGS):
        result = evaluate_config(config)
        if result:
            rows.append(result)
        if (i + 1) % 10 == 0:
            print(f"  {i+1}/{len(CANDIDATE_CONFIGS)} done")

    trade_space = pd.DataFrame(rows).sort_values("cost")
    trade_space.to_csv("data/trade_space_results.csv", index=False)

    print(f"\nDone. Saved {len(trade_space)} configurations to data/trade_space_results.csv")

    passing = trade_space[trade_space["all_requirements_pass"]]
    print(f"\nConfigurations meeting ALL requirements: {len(passing)}")
    if len(passing) > 0:
        cheapest = passing.sort_values("cost").iloc[0]
        print("\nCheapest fully-passing configuration:")
        print(cheapest)
    else:
        print("No configuration in the search grid meets all requirements.")
        print("Closest by lowest p90 wait time:")
        print(trade_space.sort_values("p90_wait_min").iloc[0])