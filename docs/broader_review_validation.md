# BROADER_REVIEW Validation

This note validates the external `gonkalabs/GRC-e267-kimi_shortfall` `BROADER_REVIEW.md` figures against the local chain-style reconstruction.

Reproduce this comparison with:

```bash
python3 scripts/validate_broader_review_amounts.py
```

The historical coefficient overrides used by the validation scripts are stored in `data/derived/historical_model_coefficients.json`; it contains only model coefficients, not the archive endpoint.

## Scope

The recommended validation scope remains Kimi-only:

- epoch `267` strict Case 3 validated row;
- epoch `265` same-address Kimi candidate only if GRC explicitly extends Case 3 scope.

The epoch `265` Qwen row is compared because it appears in the external broader report, but it is not included in the recommended Kimi-only restitution scope.

## Historical Coefficients

Historical params at epoch `265` and epoch `267` cPoC/settlement heights show:

```text
Qwen weight_scale_factor = 0.3593
Kimi weight_scale_factor = 1.2620856201975851
```

Those are the coefficients used for the validation below. The earlier local draft that used latest public params undercounted epoch `265`.

## Corrected Amounts

| row | external report | local validation |
| --- | ---: | ---: |
| Epoch 267 Kimi | 10,262.057515369 GNK | 10,262.057515368 GNK |
| Epoch 265 Kimi | 20,896.527179100 GNK | 20,894.006146127 GNK |
| Kimi-only total | 31,158.584694469 GNK | 31,156.063661495 GNK |
| Epoch 265 Qwen broader comparison only | 4,154.662338515 GNK | 4,154.662338514 GNK |
| Broader total including Qwen comparison only | 35,313.247032984 GNK | 35,310.726000009 GNK |

## Difference

The scope classification mostly matches the external report:

- strict epoch `267` has one direct Kimi-shortfall victim;
- epoch `265` is one same-address Kimi extension candidate;
- epoch `265` Qwen is broader-scope only and is not part of the Kimi-only recommendation.

The material arithmetic difference is epoch `265` Kimi:

```text
participant root weight = 66311
parent confirmation_weight = 323
Kimi raw subgroup PoC weight = 52279
Qwen raw subgroup PoC weight = 923
Kimi scaled = floor(52279 * 1.2620856201975851) = 65980
Qwen scaled = floor(923 * 0.3593) = 331
counterfactual confirmation_weight = 323 + 65980 = 66303
scaled model total = 65980 + 331 = 66311
effective payout weight = 66303
```

The external epoch `265` Kimi amount uses full root weight `66311` as the payout numerator:

```text
floor(66311 * 284932503735690 / 904177)
= 20896527179100 nGNK
= 20896.527179100 GNK
```

The chain-style reconstruction uses effective payout weight `66303`:

```text
floor(66303 * 284932503735690 / 904177)
= 20894006146127 nGNK
= 20894.006146127 GNK
```

So the Kimi-only total is lower by `2.521032974 GNK`.

## cPoC Denominator Note

For epoch `265` cPoC trigger height `4102890`, the historical `PoCValidationSnapshot.total_network_weight` is `732828`, so the strict `>2/3` weight threshold is `488553`.

The external report displays Kimi valid weight as `256727 / 904177`. The pass/fail conclusion is unchanged because `256727` is below either denominator's two-thirds threshold, but the cPoC ratio should use the state snapshot denominator, not the root reward denominator.
