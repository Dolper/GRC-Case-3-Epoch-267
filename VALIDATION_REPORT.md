# GRC Epoch 267 Validation Report

## Summary

Validator: Demian
Case investigator: @mikenosov
Epoch: 267
Address: `gonka1j7x6dv42xehe9e5au4ku3wvzwtqlegfjhlvzj6`

Independent validation supports epoch `267` as the validated restitution row for the `failed_confirmation_poc` incident.

Validated restitution amount:

```text
10262057515368 nGNK
10262.057515368 GNK
```

If committee display precision is 6 decimals, this is:

```text
10262.057515 GNK
```

## Chain Facts

- Exclusion reason: `failed_confirmation_poc`
- Exclusion block height: `4122552`
- Epoch PoC start block: `4120752`
- Epoch effective block: `4121152`
- Epoch last block: `4136542`
- Root epoch total weight: `541415`
- Participant root weight: `19518`
- Participant confirmation weight: `343`
- Participant confirmation ratio: about `1.76%`
- Kimi subgroup raw PoC weight: `51822`
- Kimi historical weight scale factor: `1.2620856201975851`
- Qwen subgroup raw PoC weight: `873`
- Qwen weight scale factor: `0.3593`
- Participant actual rewarded coins: `0`

The same core values were reproduced from `node2`, `node1`, and `gonka.spv.re`.

## Calculation

The primary restitution calculation follows the protocol Bitcoin reward logic: use `fixed_epoch_reward` as the epoch reward pool and the full root epoch weight as the denominator. The numerator is the counterfactual effective weight derived from chain subgroup data using the release/v0.2.12 settlement logic.

Effective-weight reconstruction:

```text
Kimi scaled weight = floor(51822 * 1.2620856201975851) = 65403
Qwen scaled weight = floor(873 * 0.3593) = 313
scaled model total = 65716

actual effective weight =
  floor(343 * 19518 / 65716) = 101

counterfactual confirmation weight =
  actual parent confirmation_weight + missing Kimi scaled weight
  = 343 + 65403
  = 65746

counterfactual effective weight =
  min(19518, floor(65746 * 19518 / 65716))
  = 19518
```

The actual distributed `rewarded_coins` sum is lower because invalid/CPoC-reduced/unclaimed shares are not redistributed to other participants; they become governance remainder.

Formula:

```text
validated_loss = floor(counterfactual_effective_weight * fixed_epoch_reward / epoch_total_weight) - actual_rewarded_coins
```

Inputs:

```text
counterfactual_effective_weight = 19518
fixed_epoch_reward = 284661946392227 nGNK
epoch_total_weight = 541415
actual_rewarded_coins = 0
```

Result:

```text
floor(19518 * 284661946392227 / 541415) - 0
= 10262057515368 nGNK
= 10262.057515368 GNK
```

## Investigator Report Check

The latest reviewer comment asks to derive payout weight from model subgroup chain data rather than hardcode the root weight. This validation now does that: the release/v0.2.12-style counterfactual effective weight caps back to `19518`, so the proposed payout remains `10262.057515 GNK`.

The only material numeric difference found is a 1 nGNK rounding edge in the chain integer representation. This validation floors the protocol integer calculation to `10262057515368 nGNK`. The investigator report appears to present `10262057515369 nGNK` / `10,262.057515 GONKA`, which is equivalent at 6 decimal GNK display precision but differs by 1 nGNK at raw integer precision.

## Epoch 265 Candidate For Scope Addition

The extended timeline scan for epochs `265..280` found one related epoch `265` signal for the same participant. This is a candidate for adding to scope, not a validated payout under the current strict Case #3 rule:

```text
epoch = 265
address = gonka1j7x6dv42xehe9e5au4ku3wvzwtqlegfjhlvzj6
exclusion reason = failed_confirmation_poc
actual reward = 0
indicative amount if included = 20894.006146127 GNK
```

This is not the same narrow pattern as the validated epoch `267` Case 3 row.

Key difference:

- Epoch `267`: Kimi failed at cPoC event `0` with guardian no-votes; the next three Kimi cPoCs passed. This matches the current Case 3 mechanism and is included in the validated payout.
- Epoch `265`: Kimi failed at cPoC event `2`; guardians split `1` valid / `1` invalid, so guardian protection did not pass. This is a related Kimi confirmation-PoC failure, but it requires an explicit GRC scope-addition decision before adding restitution.

The detailed epoch `265` checklist is in `docs/epoch265_case3_like_review.md`. It confirms the participant was active, submitted Kimi at trigger height `4102890`, had a store commit/root hash on chain, missed the `>2/3` Kimi valid-weight threshold, and failed guardian fallback because one eligible guardian voted invalid.

If GRC extends Case 3 to include the epoch `265` candidate, the combined indicative payout for epochs `265` and `267` is:

```text
31156.063661495 GNK
```

The previous local draft used latest public params and therefore undercounted epoch `265`. Historical params at the epoch `265` cPoC/settlement heights show:

```text
Qwen weight_scale_factor = 0.3593
Kimi weight_scale_factor = 1.2620856201975851
```

Using those historical coefficients, the epoch `265` Kimi candidate reconstructs to effective payout weight `66303`, not the full root weight `66311`. This is why the corrected amount is slightly below the investigator's full-root figure of `20896.527179100 GNK`.

## Root-Cause Questions

This validation confirms the state-level cPoC outcome and payout amount, but the root-cause investigation should still answer:

- Were PoC nonces/challenges for the affected participant actually emitted for the failed Kimi cPoC?
- Which validators received or were expected to receive those nonces, and did they submit validations for the affected participant/model?
- For validators that did not validate, can chain state, logs, or DAPI records distinguish no-send, no-receive, no-submit, timeout, invalid response, or guardian filtering?
- Did the `2/3` validation rule behave as designed for this cPoC? The rule is: pass by weight only if valid model voting power is greater than two thirds of `total_network_weight`; otherwise guardian tiebreak can pass only when at least one model-voting guardian validates and no model-voting guardian invalidates.
- In epoch `267` event `0`, Kimi had `171571` valid voting power against a `360943.333...` threshold and `0/0/2` guardian valid/invalid/no-vote, so it did not pass either weight or guardian rule. Was that caused by preserved high-weight Kimi nodes, missing guardian validations, nonce delivery, validator behavior, or an interaction between those?
- What is the minimal root cause that explains why the same participant failed Kimi at cPoC event `0` but passed the next three Kimi cPoCs in the same epoch?

## Reproduction

Run from the repository root:

```bash
python3 scripts/collect_epoch267.py
python3 scripts/calculate_candidate_compensation.py
python3 scripts/build_cpoc_matrix.py
```

Main outputs:

- `data/derived/epoch267_candidate_compensation.json`
- `data/derived/epoch267_cpoc_matrix.json`
- `data/derived/epoch267_summary.json`

Raw chain API responses are stored under `data/raw/`.

## Limitation

The original public-node scan could only use raw cPoC evidence. The updated validation adds cached historical app-state and replays cPoC pass/fail using `PoCValidationSnapshot.ModelVotingPowers` plus the per-cPoC `total_network_weight`.

State replay confirms the mechanism:

- cPoC event `0`, trigger `4122271`: Qwen passed by guardian tiebreak; Kimi failed by weight and guardian shortfall.
- cPoC events `1..3`: Kimi passed by guardian tiebreak.

The historical snapshots are cached under `data/raw/archive_state/` and reflected in `data/derived/epoch267_cpoc_matrix.json`.

The extended `265..280` state scan also found historical snapshots for all `62/62` cPoC trigger heights in the range. Under the current strict Case 3 rule, it still confirms only the epoch `267` restitution row above.
