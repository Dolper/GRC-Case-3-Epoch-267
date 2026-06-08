#!/usr/bin/env python3
"""Recompute BROADER_REVIEW comparison amounts from fixed chain inputs."""

from __future__ import annotations

from decimal import Decimal, ROUND_DOWN, getcontext


getcontext().prec = 80

NANO = 10**9
KIMI_HISTORICAL_SCALE = Decimal("1.2620856201975851")
QWEN_HISTORICAL_SCALE = Decimal("0.3593")


def floor_scaled(raw_weight: int, scale: Decimal) -> int:
    return int((Decimal(raw_weight) * scale).to_integral_value(rounding=ROUND_DOWN))


def chain_effective_weight(confirmation_weight: int, root_weight: int, scaled_total: int) -> int:
    effective = max(0, confirmation_weight)
    if scaled_total > 0 and root_weight < scaled_total:
        effective = (effective * root_weight) // scaled_total
    return min(effective, root_weight)


def reward_amount(effective_weight: int, fixed_epoch_reward: int, root_total_weight: int) -> int:
    return (effective_weight * fixed_epoch_reward) // root_total_weight


def format_gnk(amount: int) -> str:
    return f"{amount // NANO}.{amount % NANO:09d}"


def main() -> int:
    epoch_267 = {
        "root_weight": 19518,
        "parent_confirmation_weight": 343,
        "kimi_raw": 51822,
        "qwen_raw": 873,
        "fixed_epoch_reward": 284661946392227,
        "root_total_weight": 541415,
        "external_report_amount": 10262057515369,
    }
    epoch_265 = {
        "root_weight": 66311,
        "parent_confirmation_weight": 323,
        "kimi_raw": 52279,
        "qwen_raw": 923,
        "fixed_epoch_reward": 284932503735690,
        "root_total_weight": 904177,
        "external_report_amount": 20896527179100,
    }
    epoch_265_qwen_broader = {
        "effective_weight": 13184,
        "fixed_epoch_reward": 284932503735690,
        "root_total_weight": 904177,
        "external_report_amount": 4154662338515,
    }

    e267_kimi_scaled = floor_scaled(epoch_267["kimi_raw"], KIMI_HISTORICAL_SCALE)
    e267_qwen_scaled = floor_scaled(epoch_267["qwen_raw"], QWEN_HISTORICAL_SCALE)
    e267_counterfactual = epoch_267["parent_confirmation_weight"] + e267_kimi_scaled
    e267_effective = chain_effective_weight(
        e267_counterfactual,
        epoch_267["root_weight"],
        e267_kimi_scaled + e267_qwen_scaled,
    )
    e267_amount = reward_amount(
        e267_effective,
        epoch_267["fixed_epoch_reward"],
        epoch_267["root_total_weight"],
    )

    e265_kimi_scaled = floor_scaled(epoch_265["kimi_raw"], KIMI_HISTORICAL_SCALE)
    e265_qwen_scaled = floor_scaled(epoch_265["qwen_raw"], QWEN_HISTORICAL_SCALE)
    e265_counterfactual = epoch_265["parent_confirmation_weight"] + e265_kimi_scaled
    e265_effective = chain_effective_weight(
        e265_counterfactual,
        epoch_265["root_weight"],
        e265_kimi_scaled + e265_qwen_scaled,
    )
    e265_amount = reward_amount(
        e265_effective,
        epoch_265["fixed_epoch_reward"],
        epoch_265["root_total_weight"],
    )

    qwen_amount = reward_amount(
        epoch_265_qwen_broader["effective_weight"],
        epoch_265_qwen_broader["fixed_epoch_reward"],
        epoch_265_qwen_broader["root_total_weight"],
    )

    kimi_only_total = e267_amount + e265_amount
    broader_total = kimi_only_total + qwen_amount

    rows = [
        ("Epoch 267 Kimi", epoch_267["external_report_amount"], e267_amount),
        ("Epoch 265 Kimi", epoch_265["external_report_amount"], e265_amount),
        (
            "Kimi-only total",
            epoch_267["external_report_amount"] + epoch_265["external_report_amount"],
            kimi_only_total,
        ),
        ("Epoch 265 Qwen broader comparison only", epoch_265_qwen_broader["external_report_amount"], qwen_amount),
        (
            "Broader total including Qwen comparison only",
            epoch_267["external_report_amount"] + epoch_265["external_report_amount"] + epoch_265_qwen_broader["external_report_amount"],
            broader_total,
        ),
    ]

    print("| row | external report | local validation | delta |")
    print("| --- | ---: | ---: | ---: |")
    for label, external, local in rows:
        print(f"| {label} | {format_gnk(external)} GNK | {format_gnk(local)} GNK | {format_gnk(external - local)} GNK |")

    print()
    print("Epoch 265 Kimi effective weight details:")
    print(f"Kimi scaled = {e265_kimi_scaled}")
    print(f"Qwen scaled = {e265_qwen_scaled}")
    print(f"counterfactual confirmation_weight = {e265_counterfactual}")
    print(f"effective payout weight = {e265_effective}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
