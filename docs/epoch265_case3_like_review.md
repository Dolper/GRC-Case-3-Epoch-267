# Epoch 265 Scope-Addition Candidate

## Summary

Epoch `265` has one Case-3-like Kimi confirmation-PoC failure for the same participant as the validated epoch `267` row:

```text
gonka1j7x6dv42xehe9e5au4ku3wvzwtqlegfjhlvzj6
```

It is not the same strict pattern as the validated epoch `267` Case 3 row. The strict epoch `267` rule is cPoC event `0` Kimi failure, Qwen guardian rescue in the same event, and the next three Kimi cPoCs passing. Epoch `265` failed at cPoC event `2`, after earlier Kimi cPoCs had already passed, and the guardian outcome was split `1` valid / `1` invalid.

If GRC explicitly extends scope to include this related epoch `265` mechanism, the indicative compensation amount is:

```text
20894.006146127 GNK
```

If GRC keeps the current strict Case 3 scope, epoch `265` should remain a scope-addition candidate, not a validated restitution row.

## Participant Outcome

The participant was active before the failed cPoC:

```text
root weight = 66311
root confirmation_weight = 323
Kimi subgroup voting_power = 66311
Kimi raw PoC weight = 52279
Qwen raw PoC weight = 923
```

Kimi nodes on the participant:

| node | poc_weight | timeslot_allocation |
| --- | ---: | --- |
| `kimi30` | `13077` | `[true, false]` |
| `kimi31` | `13133` | `[true, false]` |
| `kimi32` | `13049` | `[true, false]` |
| `kimi33` | `13020` | `[true, false]` |

The outcome matches a loss signal:

```text
exclusion reason = failed_confirmation_poc
exclusion block height = 4103171
actual rewarded coins = 0
```

## Submission

The participant submitted Kimi in cPoC event `2`:

```text
cPoC trigger height = 4102890
model = moonshotai/Kimi-K2.6
submitted count = 52028
store commit/root hash = NoQ5db/7yBaDfk0+niLTTLeke56AsI6bJrvI0A1nLAk=
hex pubkey = 021173fcef5bd6bb75a30fe488b4158e320ce4fb6996c8c33f389195cef4708d93
```

So the chain-only evidence does not point to a missing participant submission. It shows a submitted Kimi cPoC that failed the validation pass rules.

## cPoC Timeline

| event | height | model | result | total network weight | valid voting power | invalid voting power | guardian valid | guardian invalid | guardian no-vote |
| ---: | ---: | --- | --- | ---: | ---: | ---: | ---: | ---: | ---: |
| 0 | `4095682` | Qwen | `pass_guardian` | `904177` | `509938` | `0` | `3` | `0` | `0` |
| 0 | `4095682` | Kimi | `pass_weight` | `904177` | `677518` | `0` | `2` | `0` | `0` |
| 1 | `4098879` | Qwen | `pass_guardian` | `742909` | `406730` | `0` | `3` | `0` | `0` |
| 1 | `4098879` | Kimi | `pass_weight` | `742909` | `535847` | `0` | `2` | `0` | `0` |
| 2 | `4102890` | Qwen | `pass_guardian` | `732828` | `35370` | `0` | `2` | `0` | `1` |
| 2 | `4102890` | Kimi | `weight_and_guardian_shortfall` | `732828` | `256727` | `187906` | `1` | `1` | `0` |

## 2/3 Rule Check

For epoch `265` cPoC event `2`, Kimi:

```text
total_network_weight = 732828
2/3 threshold = 488552
valid voting power = 256727
invalid voting power = 187906
```

The ordinary weight rule did not pass:

```text
256727 <= 488552
```

The guardian fallback also did not pass:

```text
guardian_valid = 1
guardian_invalid = 1
```

The pass rule is:

```text
valid_weight > 2/3 * total_network_weight
or guardian_valid > 0 and guardian_invalid == 0
```

Because one eligible guardian voted invalid, guardian fallback was blocked.

## Kimi Validation Ledger

Kimi event `2` model-voting snapshot:

```text
available Kimi model-voting addresses = 13
available Kimi model-voting power = 687984
valid voting power = 256727
invalid voting power = 187906
no-vote voting power = 243351
```

Per-validator model-voting result:

| validator | voting power | result |
| --- | ---: | --- |
| `gonka17pw6099q758qwzewtrqmqpf5c2lrhr97fwqexu` | `189884` | no-vote |
| `gonka1q5xt54wncgzk7dxv9x64uln68455g83wu9tugg` | `147538` | valid |
| `gonka1y2a9p56kv044327uycmqdexl7zs82fs5ryv5le` | `141664` | invalid / guardian |
| `gonka1j7x6dv42xehe9e5au4ku3wvzwtqlegfjhlvzj6` | `66311` | valid |
| `gonka17gpuntq09zsaqtmpe544gc32tk4424dwv5t34f` | `46242` | invalid |
| `gonka15munkmx6x7k6rqqeexjet4556p7at39ks9qgr5` | `33800` | valid |
| `gonka168rtjfkszuhcggg4dfyse4yh7xn9zwfglnkns2` | `13883` | no-vote |
| `gonka1830lqug50lse998x2lakk4pj5ypfumz5pasz0y` | `13490` | no-vote |
| `gonka1f0u3y2wneer8zhz3ypw4x54h38cpa0qsy8ts3e` | `11773` | no-vote |
| `gonka1wkgawwdzj623ss8eywayzdj6qcgr2llygactje` | `7264` | no-vote |
| `gonka19cjm4c5mt3j3qdr8vhytmm4hef3pnkvkm0x7m2` | `7057` | no-vote |
| `gonka1kx9mca3xm8u8ypzfuhmxey66u0ufxhs7nm6wc5` | `5411` | valid / guardian |
| `gonka15p7s7w2hx0y8095lddd4ummm2y0kwpwljk00aq` | `3667` | valid |

Guardian set:

```text
gonka1y2a9p56kv044327uycmqdexl7zs82fs5ryv5le = invalid
gonka1kx9mca3xm8u8ypzfuhmxey66u0ufxhs7nm6wc5 = valid
gonka1dkl4mah5erqggvhqkpc8j3qs5tyuetgdy552cp = not in Kimi model-voting snapshot for this cPoC
```

## Preserved / Available Weight Note

The chain state used here provides the cPoC `PoCValidationSnapshot` model-voting set. It is enough to verify the actual pass/fail decision, because the code-level rule uses model voting power in that snapshot.

For Kimi event `2`, the snapshot had enough available voting power in theory:

```text
available Kimi model-voting power = 687984
required valid power = 488552
```

But the actual valid power was only:

```text
256727
```

The epoch Kimi subgroup total voting power before this cPoC was larger:

```text
epoch Kimi subgroup voting_power sum = 842654
cPoC snapshot Kimi voting_power sum = 687984
difference = 154670
```

This report does not label that `154670` delta as preserved by itself. It records it as Kimi voting power present in the epoch subgroup but absent from the cPoC state snapshot. Mapping that delta to a precise root cause needs the implementation's preserved-node accounting and validator/DAPI logs.

## Difference From Epoch 267

| item | epoch 265 | epoch 267 |
| --- | --- | --- |
| affected participant | same address | same address |
| failed event | cPoC event `2` | cPoC event `0` |
| Kimi failure | valid weight shortfall plus guardian split | valid weight shortfall plus guardian no-votes |
| guardian pattern | `1` valid / `1` invalid / `0` no-vote | `0` valid / `0` invalid / `2` no-vote |
| Qwen in failed event | passed by guardian | passed by guardian |
| earlier/later Kimi behavior | events `0` and `1` passed first | next three Kimi cPoCs passed |
| strict Case 3 status | scope-addition candidate | validated |

## Indicative Payout If Included

Release/v0.2.12-style settlement has two separate weights:

```text
denominator = totalFullWeight
participantWeight = effective confirmation-capped weight
reward = floor(participantWeight * fixedEpochReward / totalFullWeight)
```

For epoch `265`, the denominator is the root epoch total:

```text
totalFullWeight = root epoch total_weight = 904177
```

The numerator is not automatically the participant's root weight. It follows the release/v0.2.12 settlement branch:

```text
effective = max(0, ConfirmationWeight)
if rawTotal > 0 and rootWeight < rawTotal:
  effective = floor(effective * rootWeight / rawTotal)
effective = min(effective, rootWeight)
```

For this participant:

```text
Kimi raw subgroup PoC weight = 52279
Kimi historical scale factor = 1.2620856201975851
Kimi scaled weight = floor(52279 * 1.2620856201975851) = 65980

Qwen raw subgroup PoC weight = 923
Qwen scale factor = 0.3593
Qwen scaled weight = floor(923 * 0.3593) = 331

counterfactual confirmation_weight = 323 + 65980 = 66303
rawTotal = 65980 + 331 = 66311
rootWeight = 66311
```

Because `rootWeight >= rawTotal`, the release/v0.2.12 guard skips the scale-down branch:

```text
effective counterfactual participantWeight = 66303
```

Epoch reward pool from chain params:

```text
initial_epoch_reward = 323000000000000 nGNK
decay_rate = -0.000475
genesis_epoch = 1
epoch = 265
fixedEpochReward = 284932503735690 nGNK
```

Indicative scope-extension amount:

```text
floor(66303 * 284932503735690 / 904177)
= 20894006146127 nGNK
= 20894.006146127 GNK
```

The `20896.527179100 GNK` figure should not be used for exact chain-style validation unless a different policy is intentionally adopted. It comes from the same epoch reward pool and the same root denominator, but uses the full root weight `66311` as the payout numerator:

```text
floor(66311 * 284932503735690 / 904177)
= 20896527179100 nGNK
= 20896.527179100 GNK
```

So the discrepancy is not caused by denominator or reward-pool choice. It is caused by numerator choice:

```text
chain-style effective numerator = 66303
full-root-weight numerator = 66311
```

Using `66311` is equivalent to assuming the failed Kimi confirmation PoC should restore the participant to full root epoch weight. The release/v0.2.12 settlement logic instead pays by the confirmation-capped effective participant weight.

## Root-Cause Status

Chain-only validation answers what happened at cPoC level:

- The participant was active before the failed cPoC.
- The participant submitted Kimi for event `2`.
- The Kimi submission had a store commit/root hash on chain.
- Kimi did not reach the `>2/3` valid-weight threshold.
- Guardian fallback did not pass because one eligible guardian voted invalid.

Chain-only validation does not fully answer why the large no-vote and invalid pattern happened. To identify root cause, the next evidence should be validator/DAPI logs around `4102890..4103171`, specifically:

- whether nonces/challenges were emitted to the affected participant and validators;
- which validators received them;
- which validators computed valid, invalid, timeout, or no-submit;
- why `gonka17pw6099q758qwzewtrqmqpf5c2lrhr97fwqexu` had no Kimi validation row despite `189884` model voting power;
- why guardian `gonka1y2a9p56kv044327uycmqdexl7zs82fs5ryv5le` voted invalid.
