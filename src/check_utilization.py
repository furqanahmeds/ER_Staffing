"""
Tracks resource utilization to figure out which resource -- triage
nurse, treatment bay, or physician -- is the actual bottleneck rather
than just guessing from wait times alone.

Same model as simpy_model_skeleton.py, with busy-time tracking added on
top without touching the patient flow logic. Run this instead of that
file's main block to get utilization numbers alongside the baseline results.
"""

import simpy
import numpy as np
import json
import pandas as pd

RANDOM_SEED = 12345

with open("data/arrival_mix.json") as f:
    ARRIVAL_MIX = json.load(f)
with open("data/arrival_rate.json") as f:
    ARRIVAL_RATE = json.load(f)
with open("data/service_time_distributions.json") as f:
    SERVICE_TIMES = json.load(f)

ACUITY_LEVELS = [int(k) for k in ARRIVAL_MIX.keys()]
ACUITY_WEIGHTS = [ARRIVAL_MIX[str(a)] for a in ACUITY_LEVELS]

STAFFING = {"triage_nurses": 2, "treatment_bays": 16, "physicians": 4}
PHYSICIAN_CONTACT_FRACTION = 0.2
SIM_DURATION_MIN = 60 * 24 * 7
WARMUP_MIN = 60 * 24


class ERSystem:
    def __init__(self, env, staffing=STAFFING):
        self.env = env
        self.triage_nurse = simpy.Resource(env, capacity=staffing["triage_nurses"])
        self.treatment_bay = simpy.PriorityResource(env, capacity=staffing["treatment_bays"])
        self.physician = simpy.Resource(env, capacity=staffing["physicians"])
        # busy-time accumulators
        self.busy_time = {"triage_nurse": 0.0, "treatment_bay": 0.0, "physician": 0.0}
        self.capacity = staffing


def track_busy(env, er, resource_name, duration):
    er.busy_time[resource_name] += duration


def patient(env, patient_id, acuity, er: ERSystem, rng, results: list):
    arrival_time = env.now
    record = {"patient_id": patient_id, "acuity": acuity, "arrival_time": arrival_time}

    with er.triage_nurse.request() as req:
        yield req
        record["triage_start"] = env.now
        triage_duration = max(1, rng.lognormal(mean=1.6, sigma=0.4))
        yield env.timeout(triage_duration)
        record["triage_end"] = env.now
        track_busy(env, er, "triage_nurse", triage_duration)

    with er.treatment_bay.request(priority=acuity) as req:
        yield req
        record["bay_start"] = env.now
        record["wait_time_min"] = record["bay_start"] - record["triage_end"]

        treat_params = SERVICE_TIMES[str(acuity)]["treatment_time_lognormal"]
        treatment_min = max(5, rng.lognormal(mean=treat_params["mu"], sigma=treat_params["sigma"]))
        record["treatment_time_min"] = treatment_min
        physician_contact_min = max(2, treatment_min * PHYSICIAN_CONTACT_FRACTION)

        with er.physician.request() as phys_req:
            yield phys_req
            record["physician_start"] = env.now
            yield env.timeout(physician_contact_min)
            track_busy(env, er, "physician", physician_contact_min)

        remaining_bay_min = treatment_min - physician_contact_min
        if remaining_bay_min > 0:
            yield env.timeout(remaining_bay_min)
        track_busy(env, er, "treatment_bay", treatment_min)

    record["departure_time"] = env.now
    record["total_time_min"] = record["departure_time"] - arrival_time
    results.append(record)


def arrival_process(env, er: ERSystem, rng, results: list):
    patient_id = 0
    avg_per_day = ARRIVAL_RATE["avg_arrivals_per_day"]
    hourly_fraction = ARRIVAL_RATE["hourly_fraction"]

    while True:
        current_hour = int((env.now // 60) % 24)
        hour_frac = hourly_fraction[str(current_hour)]
        expected_per_hour = avg_per_day * hour_frac
        rate_per_min = max(expected_per_hour / 60, 0.001)
        interarrival = rng.exponential(1 / rate_per_min)
        yield env.timeout(interarrival)

        patient_id += 1
        acuity = rng.choice(ACUITY_LEVELS, p=np.array(ACUITY_WEIGHTS) / sum(ACUITY_WEIGHTS))
        env.process(patient(env, patient_id, int(acuity), er, rng, results))


def run_simulation(staffing=STAFFING, sim_duration=SIM_DURATION_MIN, seed=RANDOM_SEED):
    rng = np.random.default_rng(seed)
    env = simpy.Environment()
    er = ERSystem(env, staffing=staffing)
    results = []
    env.process(arrival_process(env, er, rng, results))
    env.run(until=sim_duration)
    return pd.DataFrame(results), er


if __name__ == "__main__":
    df, er = run_simulation()

    print("=== Resource utilization over full simulation ===")
    for resource, busy in er.busy_time.items():
        capacity_key = {"triage_nurse": "triage_nurses", "treatment_bay": "treatment_bays",
                         "physician": "physicians"}[resource]
        capacity = er.capacity[capacity_key]
        total_available = capacity * SIM_DURATION_MIN
        utilization = busy / total_available * 100
        print(f"{resource:15s} capacity={capacity:2d}  utilization={utilization:5.1f}%")
