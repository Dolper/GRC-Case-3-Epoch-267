# GRC Epoch 267 Validation Report

## Summary

Validator: Demian
Case investigator: @mikenosov
Epoch: 267
Address: `gonka1j7x6dv42xehe9e5au4ku3wvzwtqlegfjhlvzj6`

Independent validation supports one compensation candidate for the epoch 267 `failed_confirmation_poc` incident.

Recommended candidate amount:

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
- Kimi weight scale factor: `0.78`
- Qwen subgroup raw PoC weight: `873`
- Qwen weight scale factor: `0.3593`
- Participant actual rewarded coins: `0`

The same core values were reproduced from `node2`, `node1`, and `gonka.spv.re`.

## Calculation

The primary restitution calculation follows the protocol Bitcoin reward logic: use `fixed_epoch_reward` as the epoch reward pool and the full root epoch weight as the denominator. The numerator is the counterfactual effective weight derived from chain subgroup data using the release/v0.2.12 settlement logic.

Effective-weight reconstruction:

```text
Kimi scaled weight = floor(51822 * 0.78) = 40421
Qwen scaled weight = floor(873 * 0.3593) = 313
scaled model total = 40734

actual effective weight =
  floor(343 * 19518 / 40734) = 164

counterfactual confirmation weight =
  actual parent confirmation_weight + missing Kimi scaled weight
  = 343 + 40421
  = 40764

counterfactual effective weight =
  min(19518, floor(40764 * 19518 / 40734))
  = 19518
```

The actual distributed `rewarded_coins` sum is lower because invalid/CPoC-reduced/unclaimed shares are not redistributed to other participants; they become governance remainder.

Formula:

```text
candidate_loss = floor(counterfactual_effective_weight * fixed_epoch_reward / epoch_total_weight) - actual_rewarded_coins
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

The cPoC matrix records raw chain evidence, but it does not claim to fully replay `PoCWeightCalculator`. Public queried nodes do not expose the historical `PoCValidationSnapshot.ModelVotingPowers` needed for exact code-level pass/fail replay at the cPoC trigger height.
