# Case 3 Timeline Review: Epochs 265-280

## Summary

Range scanned: `265..280`

Historical cPoC state coverage: `62/62` trigger snapshots found.

Current strict Case 3 rule validates one restitution row:

| epoch | participant | amount |
| ---: | --- | ---: |
| 267 | `gonka1j7x6dv42xehe9e5au4ku3wvzwtqlegfjhlvzj6` | `10262.057515368 GNK` |

However, a timeline review also flags epoch `265` as a candidate for scope addition. It has the same participant, zero reward, `failed_confirmation_poc`, and a Kimi cPoC failure, but the timeline and guardian pattern differ from epoch `267`. See `docs/epoch265_case3_like_review.md` for the checklist-level review.

Candidate scope-addition row:

| epoch | participant | indicative amount | note |
| ---: | --- | ---: | --- |
| 265 | `gonka1j7x6dv42xehe9e5au4ku3wvzwtqlegfjhlvzj6` | `20894.006146127 GNK` | Kimi failure at cPoC event `2`, not cPoC event `0`; guardian split rather than guardian no-vote shortfall |

If GRC adds epoch `265` to scope alongside the validated epoch `267` row, the combined indicative payout is:

```text
31156.063661495 GNK
```

## Method

The scan uses direct chain API data, cached historical `PoCValidationSnapshot` state for every cPoC trigger, and release/v0.2.12-style payout weight reconstruction:

```text
effective_weight =
  min(parent_weight, floor(parent_confirmation_weight * parent_weight / scaled_model_total))

counterfactual_confirmation_weight =
  parent_confirmation_weight + missing_model_scaled_weight

missing_model_scaled_weight =
  floor(sum(subgroup ml_nodes.poc_weight) * model weight_scale_factor)
```

The validation pass rule used for timeline classification is:

```text
valid_weight > 2/3 * total_network_weight
or guardian_valid > 0 and guardian_invalid == 0
```

Votes are weighted by model subgroup `voting_power`; the threshold denominator is aggregate/root `epoch_group_data.total_weight`.

## Epoch 267 Validated Row

Epoch `267` root total weight:

```text
541415
2/3 threshold = 360943.333333...
```

The cPoC replay uses historical `PoCValidationSnapshot` state. After event `0`, the target is excluded, so later cPoC snapshots have lower `total_network_weight` than the epoch root total.

Participant:

```text
gonka1j7x6dv42xehe9e5au4ku3wvzwtqlegfjhlvzj6
exclusion reason = failed_confirmation_poc
actual reward = 0
```

cPoC timeline:

| event | height | model | result | total network weight | valid voting power | invalid voting power | guardian valid | guardian invalid | guardian no-vote |
| ---: | ---: | --- | --- | ---: | ---: | ---: | ---: | ---: | ---: |
| 0 | `4122271` | Qwen | `pass_guardian` | `541415` | `129251` | `0` | `1` | `0` | `2` |
| 0 | `4122271` | Kimi | `weight_and_guardian_shortfall` | `541415` | `171571` | `0` | `0` | `0` | `2` |
| 1 | `4130085` | Kimi | `pass_guardian` | `520773` | `219570` | `0` | `2` | `0` | `0` |
| 2 | `4133665` | Kimi | `pass_guardian` | `520773` | `283289` | `0` | `2` | `0` | `0` |
| 3 | `4134529` | Kimi | `pass_guardian` | `513873` | `285299` | `0` | `2` | `0` | `0` |

Payout weight reconstruction:

```text
Kimi raw subgroup PoC weight = 51822
Kimi historical scale factor = 1.2620856201975851
Kimi scaled weight = 65403

Qwen raw subgroup PoC weight = 873
Qwen scale factor = 0.3593
Qwen scaled weight = 313

scaled model total = 65716
parent confirmation_weight = 343
actual effective weight = floor(343 * 19518 / 65716) = 101

counterfactual confirmation_weight = 343 + 65403 = 65746
counterfactual effective weight = min(19518, floor(65746 * 19518 / 65716)) = 19518
```

Restitution:

```text
10262.057515368 GNK
```

## Epoch 265 Scope-Addition Candidate

Epoch `265` root total weight:

```text
904177
2/3 threshold = 602784.666666...
```

Participant:

```text
gonka1j7x6dv42xehe9e5au4ku3wvzwtqlegfjhlvzj6
exclusion reason = failed_confirmation_poc
actual reward = 0
```

cPoC timeline:

| event | height | model | result | valid weight | invalid weight | guardian valid | guardian invalid | guardian no-vote |
| ---: | ---: | --- | --- | ---: | ---: | ---: | ---: | ---: |
| 0 | `4095682` | Qwen | `pass_guardian` | `509938` | `0` | `3` | `0` | `0` |
| 0 | `4095682` | Kimi | `pass_weight` | `677518` | `0` | `2` | `0` | `0` |
| 1 | `4098879` | Qwen | `pass_guardian` | `406730` | `0` | `3` | `0` | `0` |
| 1 | `4098879` | Kimi | `pass_guardian` | `535847` | `0` | `2` | `0` | `0` |
| 2 | `4102890` | Qwen | `pass_guardian` | `35370` | `0` | `2` | `0` | `1` |
| 2 | `4102890` | Kimi | `weight_and_guardian_shortfall` | `256727` | `187906` | `1` | `1` | `0` |

For epoch `265` event `2` Kimi:

```text
valid weight 256727 < 602784.666...
invalid weight 187906 < 602784.666...
guardian valid = 1
guardian invalid = 1
guardian tiebreak does not pass
```

Payout weight reconstruction:

```text
Kimi raw subgroup PoC weight = 52279
Kimi historical scale factor = 1.2620856201975851
Kimi scaled weight = 65980

Qwen raw subgroup PoC weight = 923
Qwen scale factor = 0.3593
Qwen scaled weight = 331

scaled model total = 66311
parent confirmation_weight = 323
actual effective weight = 323

counterfactual confirmation_weight = 323 + 65980 = 66303
counterfactual effective weight = 66303
```

Indicative restitution if GRC adds this candidate to Case 3 scope:

```text
20894.006146127 GNK
```

## Range Scan Result

| epoch | zero-reward rows | validated by strict Case 3 rule |
| ---: | ---: | ---: |
| 265 | 14 | 0 |
| 266 | 8 | 0 |
| 267 | 3 | 1 |
| 268 | 14 | 0 |
| 269 | 12 | 0 |
| 270 | 5 | 0 |
| 271 | 7 | 0 |
| 272 | 14 | 0 |
| 273 | 11 | 0 |
| 274 | 15 | 0 |
| 275 | 7 | 0 |
| 276 | 15 | 0 |
| 277 | 6 | 0 |
| 278 | 13 | 0 |
| 279 | 8 | 0 |
| 280 | 2 | 0 |

Other zero-reward shortfall-like rows in the scan were Qwen-only, invalid-majority, no-submit, or had zero counterfactual effective payout weight under the Kimi-focused reconstruction.

The Kimi-focused validation does not include Qwen-only rows in the recommended restitution scope. Qwen-only rows may be listed for comparison with external broader-scope reports, but they require a separate GRC policy decision.

## Files

- `scripts/scan_case3_epochs.py`
- `data/derived/case3_epoch_scan_265_280.json`
- `docs/epoch265_case3_like_review.md`
- `data/raw/case3_scan/` local cache, ignored by git; regenerate by rerunning the scan
