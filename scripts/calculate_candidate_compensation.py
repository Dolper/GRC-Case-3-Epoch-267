#!/usr/bin/env python3
"""Calculate a candidate epoch 267 compensation amount from public summaries."""

from __future__ import annotations

import json
import sys
import time
import urllib.request
from decimal import Decimal, ROUND_DOWN, getcontext
from pathlib import Path
from typing import Any


getcontext().prec = 50

EPOCH = "267"
TARGET_ADDRESS = "gonka1j7x6dv42xehe9e5au4ku3wvzwtqlegfjhlvzj6"
SOURCES = {
    "node2": "http://node2.gonka.ai:8000",
    "node1": "http://node1.gonka.ai:8000",
    "spv": "http://gonka.spv.re:8000",
}
RAW_EPOCH_GROUP = Path("data/raw/node2_epoch_group_data.json")
OUTPUT = Path("data/derived/epoch267_candidate_compensation.json")


def fetch_json(url: str) -> Any:
    req = urllib.request.Request(url, headers={"User-Agent": "gonka-grc-epoch267-validation/1.0"})
    with urllib.request.urlopen(req, timeout=30) as response:
        return json.load(response)


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        json.dump(payload, handle, indent=2, sort_keys=True)
        handle.write("\n")


def read_json(path: Path) -> Any:
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def load_epoch_group() -> dict[str, Any]:
    return read_json(RAW_EPOCH_GROUP)["epoch_group_data"]


def get_participant_addresses(epoch_group: dict[str, Any]) -> list[str]:
    return [item["member_address"] for item in epoch_group["validation_weights"]]


def fetch_performance(source: str, base_url: str, addresses: list[str]) -> dict[str, Any]:
    results: dict[str, Any] = {}
    for address in addresses:
        url = (
            f"{base_url}/chain-api/productscience/inference/inference/"
            f"epoch_performance_summary/{EPOCH}/{address}"
        )
        data = fetch_json(url)
        results[address] = data
        time.sleep(0.05)
    write_json(Path(f"data/raw/{source}_epoch267_performance_by_participant.json"), results)
    return results


def as_int(summary: dict[str, Any], key: str) -> int:
    return int(summary["epochPerformanceSummary"].get(key, "0"))


def decimal_param(value: dict[str, Any] | None) -> Decimal:
    if not value:
        return Decimal(0)
    return Decimal(str(value.get("value") or "0")) * (Decimal(10) ** int(value.get("exponent") or 0))


def fixed_epoch_reward(epoch_group: dict[str, Any]) -> int:
    params = read_json(Path("data/raw/node2_params.json"))["params"]
    br = params["bitcoin_reward_params"]
    initial = int(br["initial_epoch_reward"])
    decay = decimal_param(br["decay_rate"])
    genesis = int(br.get("genesis_epoch") or "1")
    elapsed = max(0, int(epoch_group["epoch_index"]) - genesis)
    return int(Decimal(initial) * (decay * Decimal(elapsed)).exp())


def calculate_for_source(source: str, performance: dict[str, Any], epoch_group: dict[str, Any]) -> dict[str, Any]:
    total_weight = int(epoch_group["total_weight"])
    target_weight_entry = next(
        item for item in epoch_group["validation_weights"] if item["member_address"] == TARGET_ADDRESS
    )
    target_weight = int(target_weight_entry["weight"])
    target_confirmation_weight = int(target_weight_entry["confirmation_weight"])
    target_perf = performance[TARGET_ADDRESS]["epochPerformanceSummary"]

    earned_pool = sum(as_int(item, "earned_coins") for item in performance.values())
    rewarded_pool = sum(as_int(item, "rewarded_coins") for item in performance.values())
    burned_pool = sum(as_int(item, "burned_coins") for item in performance.values())

    candidate_reward_gross = (Decimal(target_weight) * Decimal(rewarded_pool)) / Decimal(total_weight)
    candidate_earned_gross = (Decimal(target_weight) * Decimal(earned_pool)) / Decimal(total_weight)
    protocol_epoch_reward = fixed_epoch_reward(epoch_group)
    candidate_fixed_reward_gross = (
        Decimal(target_weight) * Decimal(protocol_epoch_reward)
    ) / Decimal(total_weight)
    actual_reward = Decimal(target_perf.get("rewarded_coins", "0"))
    candidate_reward_net = candidate_reward_gross - actual_reward
    candidate_fixed_reward_net = candidate_fixed_reward_gross - actual_reward

    return {
        "source": source,
        "primary_method": "candidate_loss = target_weight / epoch_total_weight * fixed_epoch_reward - actual_rewarded_coins",
        "distributed_pool_reference_method": "target_weight / epoch_total_weight * sum(rewarded_coins across validation_weights participants)",
        "earned_pool_reference_method": "target_weight / epoch_total_weight * sum(earned_coins across validation_weights participants)",
        "participants_queried": len(performance),
        "epoch_total_weight": str(total_weight),
        "fixed_epoch_reward": str(protocol_epoch_reward),
        "target_weight": str(target_weight),
        "target_confirmation_weight": str(target_confirmation_weight),
        "target_confirmation_ratio": str(Decimal(target_confirmation_weight) / Decimal(target_weight)),
        "target_actual_earned_coins": target_perf.get("earned_coins", "0"),
        "target_actual_rewarded_coins": target_perf.get("rewarded_coins", "0"),
        "summed_earned_pool": str(earned_pool),
        "summed_rewarded_pool": str(rewarded_pool),
        "summed_burned_pool": str(burned_pool),
        "candidate_reward_gross_coins_decimal": str(candidate_reward_gross),
        "candidate_reward_gross_coins_floor": str(candidate_reward_gross.to_integral_value(rounding=ROUND_DOWN)),
        "candidate_reward_net_coins_decimal": str(candidate_reward_net),
        "candidate_reward_net_coins_floor": str(candidate_reward_net.to_integral_value(rounding=ROUND_DOWN)),
        "candidate_earned_pool_reference_decimal": str(candidate_earned_gross),
        "candidate_earned_pool_reference_floor": str(candidate_earned_gross.to_integral_value(rounding=ROUND_DOWN)),
        "candidate_fixed_reward_gross_coins_decimal": str(candidate_fixed_reward_gross),
        "candidate_fixed_reward_gross_coins_floor": str(candidate_fixed_reward_gross.to_integral_value(rounding=ROUND_DOWN)),
        "candidate_fixed_reward_net_coins_decimal": str(candidate_fixed_reward_net),
        "candidate_fixed_reward_net_coins_floor": str(candidate_fixed_reward_net.to_integral_value(rounding=ROUND_DOWN)),
    }


def main() -> int:
    epoch_group = load_epoch_group()
    addresses = get_participant_addresses(epoch_group)
    summaries = []
    for source, base_url in SOURCES.items():
        performance = fetch_performance(source, base_url, addresses)
        summaries.append(calculate_for_source(source, performance, epoch_group))

    result = {
        "epoch": EPOCH,
        "target_address": TARGET_ADDRESS,
        "notes": [
            "This is a candidate policy calculation, not a final GRC decision.",
            "The primary method follows the protocol Bitcoin reward calculation: fixed_epoch_reward is minted, invalid/CPoC-reduced shares are not redistributed, and the full root weight remains the denominator.",
            "The summed rewarded_coins pool is kept only as an actual-distributed-pool reference; using it for restitution would undercount shares that went undistributed/governance.",
            "The earned_coins pool is kept as a secondary reference because it appears to represent a different, much smaller pool.",
            "If GRC chooses a different reward pool, denominator, or treatment of excluded participants, the result must be recomputed.",
        ],
        "summaries": summaries,
    }
    write_json(OUTPUT, result)
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    sys.exit(main())
