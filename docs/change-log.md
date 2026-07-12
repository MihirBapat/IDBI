# Change-Advisory-Board (CAB) control — config as product

**DHS-CL-001 · v1.0 · 2026-07-12** · How advice logic changes are governed. Companions:
[compliance-gate.md](compliance-gate.md), [model-card.md](model-card.md).

## The control

The advice-shaping logic lives in **versioned YAML**, treated as product, not code:

| File | Owns | Change is… |
|---|---|---|
| `backend/app/data/strategy_library.yaml` | the 10 manager playbooks (triggers, allocations, principles) | a reviewable diff |
| `backend/app/data/product_shelf.yaml` | IDBI FD/MF/SIP/insurance shelf + rates | a reviewable diff |
| `backend/app/data/suitability_rules.yaml` | equity caps, age thresholds, amount limits | a reviewable diff |
| `backend/app/data/category_map.yaml` | closed merchant→category vocabulary | a reviewable diff |

Every recommendation's `reasoning_trace` pins the **content hash** of the shelf and the
strategy library (`sha256(file bytes)[:12]`). So any advice can be traced to the exact
config that produced it, and any config change is visible in the trace and in CI.

## Current pinned versions (as of this commit)

| Config | `@sha` |
|---|---|
| `product_shelf.yaml` | `ca5f3e3c0df1` |
| `strategy_library.yaml` | `6dcdc5bea3d6` |
| `suitability_rules.yaml` | `e74243ab77ae` |
| `category_map.yaml` | `33e0fb149784` |

*(Regenerate/verify: `python -c "from app.config import file_sha; print(file_sha('product_shelf.yaml'))"` from `backend/`.)*

## Maker–checker workflow (the CAB)

1. **Maker** proposes a config edit (e.g. an FD rate change) as a PR.
2. **CI reveals the impact**: golden advice fixtures (`tests/golden/{persona}.json`) change
   — a rate edit is a *failing test diff*, reviewed like code, never a silent runtime shift.
   Regenerate intentionally with `python scripts/build_goldens.py`.
3. **Checker** reviews the golden diff + the new `@sha` and approves.
4. On merge, the new `@sha` is pinned into every subsequent trace and audit row.

> Prototype note: the maker–checker *workflow tooling* (approvals UI, segregation of duties)
> is documented as a control here but not built in v1 — the GitOps diff + `@sha` pinning +
> golden fixtures are the enforceable mechanism that ships.

## Change history

| Date | Change | Config `@sha` after |
|---|---|---|
| 2026-07-12 | Initial shelf, strategy library, suitability rules, category map for prototype v1 | shelf `ca5f3e3c0df1` · strategy `6dcdc5bea3d6` · suitability `e74243ab77ae` · category `33e0fb149784` |
