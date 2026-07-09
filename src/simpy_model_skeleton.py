"""
Day 4: SimPy model skeleton -- entities and resources.

Structure matches the system architecture diagram:
  Patient arrivals -> Triage -> Treatment bay -> Physician -> Disposition

Resources are the "mechanisms" in the diagram; staffing levels below are
the "control" inputs that Days 10-12 will vary in the trade-space study.
"""

import simpy
import json

# ---- Load calibrated data from Day 3 ----
with open("data/arrival_mix.json") as f:
    ARRIVAL_MIX = json.load(f)  # {"1": 15.0, "2": 27.0, ...}

with open("data/service_time_distributions.json") as f:
    SERVICE_TIMES = json.load(f)  # lognormal params by acuity level

# ---- Staffing configuration (the control variable) ----
# This is what Days 10-12 will systematically vary.
STAFFING = {
    "triage_nurses": 2,
    "treatment_bays": 8,
    "physicians": 3,
}


class ERSystem:
    """Wraps the SimPy resources so they're easy to pass around and swap
    staffing configurations without rewriting the patient flow logic."""

    def __init__(self, env, staffing=STAFFING):
        self.env = env
        self.triage_nurse = simpy.Resource(env, capacity=staffing["triage_nurses"])
        self.treatment_bay = simpy.PriorityResource(env, capacity=staffing["treatment_bays"])
        self.physician = simpy.Resource(env, capacity=staffing["physicians"])


def patient(env, name, acuity, er: ERSystem, results: list):
    """One patient's journey through the ER. Records timestamps at each
    stage so we can compute wait times and total time-in-system later."""

    arrival_time = env.now
    record = {"name": name, "acuity": acuity, "arrival_time": arrival_time}

    # ---- Triage ----
    with er.triage_nurse.request() as req:
        yield req
        record["triage_start"] = env.now
        yield env.timeout(5)  # placeholder fixed triage duration; refine later
        record["triage_end"] = env.now

    # ---- Treatment bay (priority by acuity: lower number = seen first) ----
    with er.treatment_bay.request(priority=acuity) as req:
        yield req
        record["bay_start"] = env.now
        wait_min = record["bay_start"] - record["triage_end"]
        record["wait_time_min"] = wait_min

        # ---- Physician ----
        with er.physician.request() as phys_req:
            yield phys_req
            record["physician_start"] = env.now

            treat_params = SERVICE_TIMES[str(acuity)]["treatment_time_lognormal"]
            treatment_min = max(5, env_rng.lognormal(
                mean=treat_params["mu"], sigma=treat_params["sigma"]
            ))
            yield env.timeout(treatment_min)
            record["treatment_time_min"] = treatment_min

    record["departure_time"] = env.now
    record["total_time_min"] = record["departure_time"] - arrival_time
    results.append(record)


# NOTE: this is the Day 4 skeleton -- arrival process generator and the
# random number generator (env_rng) still need to be added in Day 5-6,
# along with running the simulation and computing summary statistics.
