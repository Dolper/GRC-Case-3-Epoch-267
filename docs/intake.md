# GRC Case Intake Form

Internal GRC form for opening or validating a restitution case. This file follows the structure of `gonkalabs/GRC-intake-form` and is filled with currently known epoch 267 facts.

## 1. Case Basics

| Field | Answer |
| --- | --- |
| Case ID | Case #3 / epoch 267 |
| Short title | Epoch 267 confirmation PoC failure for `gonka1j7x6...vzj6` |
| Reporter / proposer | Votkon / Mike thread context, validator: Demian |
| Date opened (UTC) | TBD |
| Related links | Gonka release `v0.2.13`: `https://github.com/gonka-ai/gonka/releases/tag/release/v0.2.13` |
| Affected epoch(s) / block range | Epoch `267`, blocks `4120752..4136542`; target exclusion at `4122552` |
| Affected software version(s) | Pre-fix behavior, fixed or mitigated in `v0.2.13`; chain node metadata currently reports `v0.2.13` / `c716df26cb8802e341a007f79b445352c53a3bee` |
| Fix / patch reference | `https://github.com/gonka-ai/gonka/compare/release/v0.2.12...release/v0.2.13` |

## 2. Short Summary

| Question | Answer |
| --- | --- |
| What happened? | Address `gonka1j7x6dv42xehe9e5au4ku3wvzwtqlegfjhlvzj6` was excluded in epoch `267` with reason `failed_confirmation_poc`. |
| Why might restitution be needed? | The operator claims the node behaved normally and failed only because guardian validation shortfall plus preserved high-weight Kimi nodes caused a rare confirmation PoC failure. |
| Who may be affected? | At minimum the target address; full affected set is still TBD. `excluded_participants/267` contains three excluded addresses. |
| What is already confirmed? | Three independent public API endpoints return identical `epoch_group_data/267`, `excluded_participants/267`, and params digests. |
| What is still uncertain? | Whether preserved-node state and guardian validation behavior can be reconstructed from public chain state alone; reward amount and eligibility policy are still TBD. |

## 3. Timeline

| Event | Epoch | Block | Time (UTC) | Source / link | Notes |
| --- | --- | --- | --- | --- | --- |
| PoC starts | 267 | 4120752 | TBD | `epoch_group_data/267` | `poc_start_block_height` |
| Epoch effective | 267 | 4121152 | TBD | `epoch_group_data/267` | `effective_block_height` |
| Target excluded | 267 | 4122552 | 2026-05-17T20:52:06.027275595Z | `/chain-rpc/block?height=4122552`, `excluded_participants/267` | `failed_confirmation_poc` |
| Epoch ends | 267 | 4136542 | TBD | `epoch_group_data/267` | `last_block_height` |
| Fix or mitigation available | TBD | TBD | 2026-05-20T20:38:43Z | GitHub release `v0.2.13` | Release publication time |

## 4. Initial Technical Claim

| Question | Answer |
| --- | --- |
| What should have happened? | If the participant was otherwise healthy, confirmation PoC should not have reduced its confirmation weight below the passing threshold because of inconsistent model/preserved weight handling. |
| What actually happened? | Target address had root weight `19518` and confirmation weight `343`, a ratio of about `1.76%`, and was excluded with `failed_confirmation_poc`. |
| What component caused or may have caused it? | Confirmation PoC model-set / preserved-weight snapshot logic during multi-model bootstrap. |
| What commit, release, config, or migration is involved? | Release `v0.2.13`, commit `c716df26cb8802e341a007f79b445352c53a3bee`. |
| Is the issue fixed? | Release notes say `v0.2.13` stores one epoch snapshot of confirmable models and weight-scale factors for confirmation and reward calculations. |

## 5. Affected Scope

| Question | Answer |
| --- | --- |
| Affected participant type(s) | Miners / participants subject to confirmation PoC in epoch `267`. |
| Affected reward stream(s) | Epoch rewards, exact reward endpoint/method TBD. |
| Affected model / subgroup, if relevant | Epoch subgroup models: `Qwen/Qwen3-235B-A22B-Instruct-2507-FP8`, `moonshotai/Kimi-K2.6`. |
| Affected rounds, CPoCs, or epochs | Currently epoch `267`; specific CPoC round reconstruction TBD. |
| Baseline state to compare against | Adjacent epochs and expected confirmation behavior under fixed snapshot logic. |
| Estimated affected count | TBD. Chain exclusion list has three excluded participants; only one is currently claimed here. |
| Estimated restitution exposure | TBD. |

## 6. Eligibility Draft

### Include Participants Who

| Rule | Reason / source |
| --- | --- |
| Were excluded in epoch `267` with `failed_confirmation_poc` and can show otherwise normal node behavior | Matches claimed consensus-failure scenario rather than ordinary downtime or statistical invalidation. |
| Had materially low confirmation weight caused by the preserved/model snapshot bug rather than local operator failure | Aligns with `v0.2.13` release-note fix. |

### Exclude Participants Who

| Rule | Reason / source |
| --- | --- |
| Were excluded for `statistical_invalidations` | Different failure mode; `excluded_participants/267` contains one such address. |
| Cannot be tied to the preserved/model snapshot issue | Avoids expanding compensation to unrelated epoch 267 failures. |

### Needs Manual Review

| Case type | Why it is ambiguous |
| --- | --- |
| Failed confirmation PoC participants other than the target address | Need to distinguish same root cause from independent node/operator issues. |
| Delegated or incoming-weight claims | Current public epoch group data reports validation weights by participant address; separate recipient attribution may need additional data. |

## 7. Evidence Needed

| Evidence | Location / command / endpoint | Status |
| --- | --- | --- |
| Chain data source | `python3 scripts/collect_epoch267.py` | Collected from three public nodes |
| Historical query method | `/chain-api/productscience/inference/inference/epoch_group_data/267` and `/excluded_participants/267` | Working |
| Relevant code / commits | Gonka `v0.2.13` release and compare link | Initial release-note evidence found |
| Release or deployment timestamps | GitHub release API | Release published `2026-05-20T20:38:43Z` |
| Operator reports, if any | Chat excerpts supplied by Demian | Partial |
| Existing scripts, CSVs, or JSON files | `scripts/collect_epoch267.py`, `data/raw/`, `data/derived/` | Started |
| cPoC commits and validations | `scripts/build_cpoc_matrix.py` | Raw cPoC matrix collected |
| Historical model voting-power snapshot | `/poc_validation_snapshot/{trigger_height}` | Not available from queried public nodes after cleanup/pruning |
| Preserved node state | `/preserved_nodes_snapshot` at historical height | Not available from queried public nodes after pruning |
| Reward distribution | Per-participant `epoch_performance_summary/267/{participant}` | Collected and cross-checked |

## 8. Draft Restitution Method

| Question | Answer |
| --- | --- |
| What baseline will be used? | TBD; likely expected epoch 267 reward share using validated root weight if the exclusion is deemed protocol-caused. |
| Why is that baseline fair? | TBD; must avoid copying earlier stuck-pw formulas unless GRC explicitly adopts them for this failure mode. |
| What denominator will be used? | Validated: epoch `267` total weight `541415`. |
| Should actual rewards already received be subtracted? | Yes. Endpoint validation confirms target `rewarded_coins = 0`. |
| Should partial payouts stay eligible? | TBD by GRC policy. |
| Should downtime, misses, invalidation, or slashing affect eligibility? | Yes for eligibility, if evidence shows local operator failure rather than protocol-caused confirmation failure. |
| Should the calculation include only fixed rewards or other losses too? | TBD by GRC policy. |

Formula draft:

```text
validated_loss = counterfactual_effective_weight / epoch_total_weight * fixed_epoch_reward - actual_rewarded_coins
```

Validated inputs:

| Item | Value |
| --- | --- |
| `counterfactual_effective_weight` | `19518` |
| `epoch_total_weight` | `541415` |
| `fixed_epoch_reward` | `284661946392227` |
| `actual_rewarded_coins` | `0` |
| Validated net compensation | `10262057515368` chain integer units |

Cross-check: `node2`, `node1`, and `gonka.spv.re` all reproduce the same candidate net compensation.

Units and rounding:

| Item | Answer |
| --- | --- |
| Internal unit | chain integer reward units, TBD exact denom |
| Display unit | TBD |
| Rounding rule | TBD |
| Final payout precision | TBD |

## 9. Required Investigator Output

- README with short summary and run instructions.
- Reproducible script or notebook.
- Machine-readable output, preferably CSV and JSON.
- Per-participant restitution table.
- List of excluded and manual-review cases.
- Narrative report with caveats.
- At least one raw-data sanity check.

## 10. Required Validator Checks

- Re-run the calculation or independently reproduce the totals.
- Check the root cause against code, release, or deployment evidence.
- Check inclusion and exclusion rules against raw data.
- Spot-check the largest payout.
- Spot-check several smaller payouts.
- Spot-check excluded or manual-review cases.
- Check formula, denominator, units, and rounding.
- Confirm final report matches the GRC policy decision.

## 11. GRC Policy Questions

| Question | Decision / link |
| --- | --- |
| Should this epoch 267 failure be handled as the Case #3 restitution scope? | Yes, pending GRC approval. |
| Should participants with `failed_confirmation_poc` in epoch 267 be included only after root-cause proof? | TBD |
| Should `statistical_invalidations` in the same epoch be excluded? | Draft: yes |
| Which loss types are in scope? | TBD |
| Should restitution use approximation or full recomputation? | TBD |
| Is raw cPoC evidence sufficient for eligibility if historical `PoCValidationSnapshot` is unavailable? | TBD |

## 12. Conflict Check

| Question | Answer |
| --- | --- |
| Does the proposed investigator benefit from the case? | TBD |
| Does the proposed validator benefit from the case? | TBD |
| Did either person work on the faulty component? | TBD |
| Are any conflicts disclosed and accepted by GRC? | TBD |

## 13. Ready For Assignment

- [x] Case basics are partially filled.
- [x] Time window is clear.
- [x] Initial technical claim is written.
- [x] Affected scope is described.
- [x] Eligibility draft is written.
- [x] Evidence sources are listed.
- [ ] Draft restitution method is final.
- [x] Open policy questions are listed.
- [ ] Conflict check is complete.
- [ ] GRC agrees the case is ready to assign.

## 14. Assignment

| Role | Name / handle | Date (UTC) | Notes |
| --- | --- | --- | --- |
| Investigator | @mikenosov | TBD | Case investigator |
| Validator | Demian | TBD | Current role in supplied context |

Expected completion date: TBD
