# apv_core

The model core of **AgriPV Lab**. It turns pre-computed district physics, crop shade-response parameters and finance inputs into a **GCR sweep (0.00–0.50)**: farm and energy income per acre, yield retention against the draft policy limit, LER, and PM-KUSUM A or land-lease finance. Every result comes as a pessimistic / central / optimistic range.

- Pure Python + numpy. No file, network or environment access, so it stays small enough for Vercel's Python runtime.
- The offline pipeline produces the physics. The FastAPI layer wraps `run_sweep`.
- Specification: [`docs/superpowers/specs/2026-11-06-agripv-lab-product-spec.md`](../docs/superpowers/specs/2026-11-06-agripv-lab-product-spec.md) §12.

## Install and test

```bash
pip install -e "apv_core[dev]"
pytest apv_core && ruff check apv_core
```

## Usage

```python
from apv_core import BusinessModel, SweepInputs, run_sweep

# Synthetic builders from apv_core/tests/fixtures.py. Real inputs come from the pipeline.
result = run_sweep(SweepInputs(
    physics=synthetic_physics(),
    structure=elevated_structure(),
    rotation=(soybean_kharif(), onion_rabi()),
    finance=finance_defaults(),
    business_model=BusinessModel.KUSUM_A,
    policy_limit=0.80,          # draft policy: yield >= 80% of open field
))

result.gcr                       # (0.0, 0.05, ..., 0.5)
result.allowed_gcr.central       # highest GCR that keeps every season >= limit, or None
result.metrics["ler"][6]         # Range(pessimistic=..., central=..., optimistic=...) at GCR 0.30
result.notices                   # low evidence, outside policy limit, KUSUM size, ...
```

## What the ranges mean

`Range.pessimistic / central / optimistic` are the outputs of three **scenario cases**, not a sorted min/max:

- **pessimistic:** pessimistic crop shade-response parameters, tariff −10%, CAPEX +10%
- **central:** central parameters and the inputs as given
- **optimistic:** the reverse of pessimistic

For a cost-like metric such as payback, the pessimistic case is the *larger* number.

## Provisional policy definition

Yield retention is defined in one place, `apv_core.retention.retention()`, as `a_farm × Y_rel` (per acre of land), and it is checked **per season**. These are the defaults for open questions Q-02 and Q-03 in the spec. If the final policy defines it differently, change that function and its tests.

## Module map

| Module | Responsibility |
|---|---|
| `constants` | GCR grid, seasons, units, defaults |
| `ranges` | `Case`, `Range` |
| `crops` | shade-response curve, season light, evidence grades |
| `physics` | `PhysicsTable`, `Structure`, kWp per acre |
| `retention` | retention, policy flags, allowed GCR |
| `farm`, `ler` | farm income, revenue weights, LER, economic ratio |
| `cashflow` | NPV, IRR, payback, annuities |
| `finance` | KUSUM-A, lease, maximum affordable lease |
| `sweep`, `notices` | `run_sweep`, `SweepResult`, notices |
