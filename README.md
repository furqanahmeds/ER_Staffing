# ER Staffing Simulation

A discrete-event simulation of ER patient flow, built to identify staffing
bottlenecks and find a cost-effective staffing configuration that meets
wait-time requirements — including under a demand surge. Applies a
systems engineering approach: formal requirements, architecture modeling,
and verification/validation (V&V).

**Full methodology, findings, and recommendation:** see [WRITEUP.md](WRITEUP.md)

## Headline Result

| | Baseline | Recommended |
|---|---|---|
| Staffing | 2 nurses, 16 bays, 4 physicians | 2 nurses, 24 bays, 5 physicians |
| 90th percentile wait | ~21 hours | 1.8 minutes |
| Meets all requirements | No | Yes |
| Staffing cost | — | +34% |

The recommended configuration is the *cheapest* of 75 tested staffing
combinations that meets every requirement — not the most aggressive one.
Full trade-space chart: `data/trade_space_chart.png`.

## How to Run

```bash
pip install simpy numpy pandas matplotlib

# 1. Generate acuity-mapped ED encounter data (requires Synthea output in data/)
python src/build_acuity_mapping.py

# 2. Calibrate service-time and arrival distributions against NHAMCS
python src/calibrate_nhamcs.py
python src/finalize_arrival_mix.py
python src/compute_arrival_rate.py

# 3. Run baseline simulation
python src/simpy_model_skeleton.py
python src/check_requirements.py
python src/check_utilization.py

# 4. Surge test (REQ-4)
python src/stress_test.py

# 5. Trade-space search + chart
python src/trade_space_search.py
python src/trade_space_chart.py
```

## Data Sources

- **Synthea** (synthetic patient data) — arrival timing shape
- **NHAMCS** (CDC national ED survey) — acuity mix, service-time
  distributions, arrival volume benchmark

Why two sources, and the data issues found along the way, are explained
in [WRITEUP.md](WRITEUP.md#3-data-sources--modeling-decisions).

## Reproducibility

- Synthea commit: `2b0a55bab0ab9ae22204320c80f5880ceb8925aa`
- Random seed: `12345`
- Population size: 5,000
