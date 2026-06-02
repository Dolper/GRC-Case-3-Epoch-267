# Gonka GRC Case #3 / Epoch 267 Validation

Independent validation workspace for the epoch 267 `failed_confirmation_poc` incident involving:

```text
gonka1j7x6dv42xehe9e5au4ku3wvzwtqlegfjhlvzj6
```

The chain facts point to an epoch 267 confirmation PoC / consensus failure rather than the earlier epoch 249-253 stuck `0.35x` `poc_weight` case.

## Current Known Facts

- Epoch: `267`
- Target address: `gonka1j7x6dv42xehe9e5au4ku3wvzwtqlegfjhlvzj6`
- Exclusion reason: `failed_confirmation_poc`
- Exclusion block height: `4122552`
- Epoch PoC start block: `4120752`
- Epoch effective block: `4121152`
- Epoch last block: `4136542`
- Root weight: `19518`
- Root confirmation weight: `343`
- Confirmation ratio: about `1.76%`
- Rewarded coins: `0` by `epoch_performance_summary/267/{address}`.

## Reproduction

Run:

```bash
python3 scripts/collect_epoch267.py
python3 scripts/calculate_candidate_compensation.py
```

The scripts fetch raw JSON from the configured Gonka nodes, write raw responses to `data/raw/`, and write normalized summaries to `data/derived/`.

## Candidate Compensation

If GRC accepts the reward-share formula for this epoch 267 confirmation PoC failure:

```text
candidate_loss = counterfactual_effective_weight / epoch_total_weight * fixed_epoch_reward - actual_rewarded_coins
```

then the current candidate amount is:

```text
10,262,057,515,368 chain integer units
```

Inputs:

- `counterfactual_effective_weight = 19518`
- `epoch_total_weight = 541415`
- `fixed_epoch_reward = 284661946392227`
- `actual_rewarded_coins = 0`

The same amount is reproduced from all three configured public sources: `node2`, `node1`, and `gonka.spv.re`.

The numerator is derived from chain subgroup data using the release/v0.2.12 settlement logic:

- Kimi raw subgroup PoC weight: `51822`, scale factor `0.78`, scaled weight `40421`
- Qwen raw subgroup PoC weight: `873`, scale factor `0.3593`, scaled weight `313`
- Actual effective weight from damaged parent confirmation weight `343`: `164`
- Counterfactual effective weight after adding the missing Kimi scaled weight and applying the parent root-weight cap: `19518`

## cPoC Matrix

Run:

```bash
python3 scripts/build_cpoc_matrix.py
```

This builds `data/derived/epoch267_cpoc_matrix.json` from chain-only cPoC endpoints:

- `confirmation_poc_events/267`
- `all_poc_v2_store_commits/{trigger_height}`
- `poc_v2_validations_for_stage/{trigger_height}`
- `all_mlnode_weight_distributions/{trigger_height}`

Independent findings for the target address:

- cPoC #1 at trigger `4122271`: target submitted both Qwen and Kimi.
- cPoC #1 Kimi raw validation weight sum was below the raw two-thirds model-weight reference.
- cPoC #1 Qwen raw validation weight sum was also below the raw two-thirds model-weight reference.
- cPoC #2, #3, and #4: target submitted Kimi rows and had positive guardian validation signals.

Important limitation: code-level pass/fail is not determined from raw `validated_weight` sums. The Gonka code uses `PoCValidationSnapshot.ModelVotingPowers` for voting power and then applies guardian tiebreaking after filtering validations to validators with model voting power. The queried public nodes no longer expose the historical `PoCValidationSnapshot` for trigger `4122271`, so the matrix records raw chain evidence and does not claim to fully replay `PoCWeightCalculator`.

## Key External Reference

Gonka release `v0.2.13` was published on 2026-05-20 and includes a confirmation PoC fix. The release notes say confirmation PoC previously used different model sets for measured weight, preserved weight, and reward rescaling during new-model bootstrap; v0.2.13 stores one epoch snapshot of confirmable models and weight-scale factors for confirmation and reward calculations.

Release:

```text
https://github.com/gonka-ai/gonka/releases/tag/release/v0.2.13
```

Comparison:

```text
https://github.com/gonka-ai/gonka/compare/release/v0.2.12...release/v0.2.13
```
