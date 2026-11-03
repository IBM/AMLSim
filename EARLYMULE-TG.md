# EarlyMule-TG changes to AMLSim

This fork of [IBM/AMLSim](https://github.com/IBM/AMLSim) generates the synthetic dataset for the EarlyMule-TG thesis (early money-mule detection on temporal transaction graphs). The thesis needs four things from the simulator: a laundering flow that spans several days, mule accounts that behave normally before they launder, money that moves through a cycle in time order, and mule typologies in which an intermediary both receives and forwards illicit money. The original code broke the first three and lacks the fourth, so it was changed as described below.

- **Base:** upstream commit `7338a4b` (2022-02-14, last upstream commit)
- **Branch:** `earlymule-fixes`
- **All changes at a glance:** [compare `7338a4b...earlymule-fixes`](https://github.com/Verzol/AMLSim/compare/7338a4b...earlymule-fixes)
- **License:** Apache License 2.0, unchanged. Modified source files carry a "Modified by EarlyMule-TG" header and an `EarlyMule-TG:` comment at each changed block.

## Summary

| # | Problem in the original output | Change | Before | After |
|---|---|---|---|---|
| 1 | Fan-in/fan-out alerts stretched over most of the simulation | Two lines removed in `FanInTypology.java`, `FanOutTypology.java` | median span 363 / 195 days | 9 / 8 days |
| 2 | Alert members often had no normal transactions at all | Member sampling in `scripts/transaction_graph_generator.py` | 41.2% of mule-like accounts had normal activity before the alert | 98.1% |
| 3 | Cycle relays sent money before receiving it | Parameter only: `schedule_id` 2 → 1 for cycle rows | 112 of 249 relays out of order | 0 of 266 |
| 4 | No typology where a hub both receives and forwards; fan-in/fan-out hubs are one-sided | New `LayeredMuleTypology.java` and four generator typologies (M1–M4) | 0 two-sided hubs outside cycles | 163 of 163 planned mules two-sided, 0 out of order (10K smoke run, with #5) |
| 5 | Accounts that send on several normal models run out of money mid-simulation and cannot take part in an alert | Optional initial-balance boost in the generator | 62–99% of accounts main of 2+ models drained | 0% |

Numbers come from the 10K configuration (12,043 accounts, 100 alerts), original vs. patched, same random seed.

## 1. Fan-in / fan-out start step

**Problem.** The generator gives every alert a window `[startStep, endStep]` of 5–20 days placed at a random point in the simulation. `FanInTypology` and `FanOutTypology` then overwrote `startStep` with a random step close to 0 but kept `endStep`. A fan-in alert planned for days 400–410 therefore ran from about day 0 to day 410. The median fan-in alert started on day 0 and lasted 363 days, so there was no early phase to detect.

**Before** (`FanInTypology.java`; `FanOutTypology.java` is the same with `numBenes`)
```java
int totalStep = (int)(endStep - startStep + 1);
int defaultInterval = Math.max(totalStep / numOrigs, 1);
this.startStep = generateStartStep(defaultInterval);  //  decentralize the first transaction step
```

**After**
```java
// EarlyMule-TG: removed `this.startStep = generateStartStep(defaultInterval)`.
// ...
```

**Why this is a bug and not a design choice.** `CycleTypology`, which uses the same "decentralize" idea, moves the whole window (`startStep` and `endStep` together). Only the fan classes move the start alone.

## 2. Alert members drawn from active accounts

**Problem.** `add_aml_typology()` picked alert members with `random.sample()` from all accounts in a bank. In the 10K run only 4,672 of 12,043 accounts make any transaction (many have a normal model that never fires), so 53.4% of alert accounts had no normal activity at all. That has two effects. A mule has no "normal → mule" transition to learn. And "has no normal transactions" alone almost reveals the label.

**Change.** Two helper methods were added, and all 17 `random.sample(self.bank_to_accts[...], k)` calls in `add_aml_typology()` now call `_sample_active_members(...)` instead:

```python
def _sample_active_members(self, candidates, num):
    pool = sorted(candidates)
    active = [a for a in pool if self._has_reliable_normal_activity(a)]
    if len(active) >= num:
        return random.sample(active, num)
    # fallback: take all active accounts, fill up with the rest
    ...

def _has_reliable_normal_activity(self, acct):
    for nm in self.g.node[acct].get('normal_models', []):
        if nm.is_main(acct) or nm.type not in ("fan_in", "fan_out"):
            return True
    return False
```

**Why this rule.** Measured on the original 10K run, an account transacts in about 99% of cases if it is the main account of any normal model or a member of a single, forward, mutual or periodical model. It transacts in only about 39% of cases if it is only a non-main member of a fan-in or fan-out normal model, because the Java fan-out model sends to the account's beneficiary list, not to the model members.

**Side effect to keep in mind.** After the change, alert accounts have *more* normal transactions than the average active account (median 123 vs. 4). The thesis therefore evaluates only on accounts with regular normal activity, where the gap disappears (median 115–120 vs. 107).

## 3. Cycle transactions in time order

**Problem.** Cycle alerts in the sample parameter files use `schedule_id = 2` (`UNORDERED`): each hop gets a random day, so a relay can send money before it has received it.

**Change.** No code change. In `paramFiles/*-earlymule*/alertPatterns.csv` the cycle rows use `schedule_id = 1` (`RANDOM_INTERVAL`). `CycleTypology.setParameters` uses the same code path for both values but sorts the steps only for `1`.

## 4. Layered mule typologies (M1–M4)

**Problem.** The thesis plan needs four mule typologies: fan-in then fan-out (M1), a relay chain (M2), collection to a single exit (M3) and collection, relay and dispersal (M4). The original fan-in and fan-out models only generate one side at the hub, `stack` never sends from its middle layer (only the main account triggers transactions) and its transfers are not marked as SAR, and `gather_scatter` holds the money until the window midpoint.

**Change.** One generic Java model, `LayeredMuleTypology` (model ID 9), and four generator typology names that only differ in layer sizes (`LAYER_SIZES` in the generator):

| Name | Layers for n accounts | Plan |
|---|---|---|
| `mule_fan_in_out` | ⌊(n−1)/2⌋ sources → 1 mule → the rest as exits | M1 |
| `mule_relay_chain` | 1 source → n−2 mules in a chain → 1 exit | M2 |
| `mule_collect_exit` | n−2 sources → 1 collector → 1 exit | M3 |
| `mule_collect_disperse` | s sources → 1 collector → k relays → k exits, k = max(2, ⌊(n−1)/3⌋) | M4 |

Consecutive layers are linked all-to-all when either has one account, otherwise one-to-one by position. The generator writes three new columns to `alert_members.csv`: `layer` (−1 for the original typologies), `minDwell`, `maxDwell`. `alertPatterns.csv` may carry `min_dwell` / `max_dwell`; the original typologies ignore them.

**Simulation rules.**
- Sources send `[min_amount, max_amount]` on a random day of the source window (`period`). A source with less than `min_amount` waits a day until the window closes.
- A mule forwards only after all its planned inflows have fired, so no mule sends before it receives. Each outgoing transfer waits a dwell drawn from `[min_dwell, max_dwell]` days; 0 means the same day.
- A mule forwards the illicit amount it received minus `margin_ratio`, split with random weights, never more than its balance. Unlike `CycleTypology`, which sizes each hop from the sender's balance, the mule does not pass on its own normal funds, and no transfer exceeds the sender's balance, so the balance columns of `tx_log.csv` do not reveal illicit transfers.
- The generator reserves `max_dwell` days per mule layer after the source window, so every hop stays inside `[startStep, endStep]`.

**Checks.** `conf_10K-earlymule-mule.json` (20 alerts per new typology, plus 20 cycle, 10 fan_in, 10 fan_out; balance boost of section 5 on):
- 0 illicit transfers outside the planned edges; 0 mules with an outflow before their first inflow; 38 of 163 forward on the day they receive.
- 163 of 163 planned mules have both an illicit inflow and an outflow, each passing on exactly 90% of what it received. 1 of 229 sources never reaches `min_amount` in its window.
- Without the boost, 148 of 163: the other 15 sat on drained accounts (section 5).
- Two runs with the same seed give byte-identical outputs. No account belongs to two alerts.
- Re-running `conf_10K_earlymule.json` gives byte-identical `tx_log.csv`, `transactions.csv` and `alert_transactions.csv`; `alert_members.csv` only gains the three columns.

## 5. Initial balance of accounts with several normal models

**Problem.** Every normal model sends from its main account, sized from the balance. An account that is main of several models sends on several schedules and runs out of money. In `conf_10K_earlymule.json`, accounts main of 2, 3 and 4 models fall below a balance of 100 in 85%, 62% and 99% of cases, at a median of day 527, 494 and 321; accounts main of one model do so in 4% of cases, mostly after day 600. An alert member on a drained account cannot pass on money (the 3 silent fan_out alerts of the 80K run, and 15 of 163 layered mules before this change).

**Change.** Optional `graph_generator.boost_balance_min_main_models` in `conf.json`. When set to `k`, every account that is main of at least `k` normal models gets its initial balance multiplied by `n_main + 1` (`boost_drain_prone_balances()`, called after the normal models are built). The multiplier covers the 90th percentile of the measured burn rate over 720 days with a 25% margin.

**Why not exclude these accounts from alerts instead.** That was tried first. It completes every alert, but mules then never come from accounts that send a lot, and among accounts with at least 20 normal transactions the normal outgoing count separates mules with ROC-AUC 0.67 (0.53 before). The boost applies to every account, alert member or not, and leaves those scores at 0.47–0.55.

**Side effect.** The initial balance now tracks how many normal models an account sends on, so it correlates with activity: over all accounts its ROC-AUC against mule candidates rises from 0.51 to 0.64. Among accounts with at least 20 normal transactions it stays at 0.49. Activity counts alone already reach 0.92 over all accounts, so the evaluation population has to be restricted either way.

## Configurations added

| File | Accounts | Alerts | Notes |
|---|---:|---:|---|
| `conf_10K.json` | 12,043 | 100 | Original `paramFiles/10K`; the copy inside that folder lacks `normal_models`, `sar_interval`, `sar_balance_ratio` |
| `conf_10K_earlymule.json` | 12,043 | 100 | `paramFiles/10K-earlymule`, cycle `schedule_id = 1` |
| `conf_80K-earlymule-a100.json` | 96,344 | 100 | 10K-earlymule accounts and normal models ×8 |
| `conf_80K-earlymule-a200.json` | 96,344 | 200 | Same, 200 alerts; the configuration used in the thesis |
| `conf_10K-earlymule-mule.json` | 12,043 | 120 | 10K-earlymule accounts; smoke test of the layered mule typologies, balance boost on (`k = 2`) |

Alert mix in the 10K-earlymule and 80K sets: 30% fan_in, 30% fan_out, 40% cycle.

## Run

Environment and build steps are in the EarlyMule-TG repository (`docs/setup.md`). With the environment ready:

```bash
python scripts/transaction_graph_generator.py conf_80K-earlymule-a200.json
bash scripts/run_AMLSim.sh conf_80K-earlymule-a200.json
python scripts/convert_logs.py conf_80K-earlymule-a200.json
```
