#!/usr/bin/env python3
"""Calculate a candidate epoch 267 compensation amount from public summaries."""

from __future__ import annotations

import json
import sys
import time
import urllib.parse
import urllib.request
from decimal import Decimal, ROUND_DOWN, getcontext
from pathlib import Path
from typing import Any


getcontext().prec = 50

EPOCH = "267"
TARGET_ADDRESS = "gonka1j7x6dv42xehe9e5au4ku3wvzwtqlegfjhlvzj6"
KIMI = "moonshotai/Kimi-K2.6"
QWEN = "Qwen/Qwen3-235B-A22B-Instruct-2507-FP8"
MODEL_IDS = {"kimi": KIMI, "qwen": QWEN}
SOURCES = {
    "node2": "http://node2.gonka.ai:8000",
    "node1": "http://node1.gonka.ai:8000",
    "spv": "http://gonka.spv.re:8000",
}
RAW_EPOCH_GROUP = Path("data/raw/node2_epoch_group_data.json")
OUTPUT = Path("data/derived/epoch267_candidate_compensation.json")
HISTORICAL_COEFFICIENTS = Path("data/derived/historical_model_coefficients.json")


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


def fetch_model_groups(source: str, base_url: str) -> dict[str, dict[str, Any]]:
    groups: dict[str, dict[str, Any]] = {}
    for label, model_id in MODEL_IDS.items():
        query = urllib.parse.urlencode({"model_id": model_id})
        url = f"{base_url}/chain-api/productscience/inference/inference/epoch_group_data/{EPOCH}?{query}"
        data = fetch_json(url)
        write_json(Path(f"data/raw/{source}_epoch267_model_group_{label}.json"), data)
        groups[model_id] = data["epoch_group_data"]
    return groups


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


def model_coefficients() -> dict[str, Decimal]:
    if HISTORICAL_COEFFICIENTS.exists():
        historical = read_json(HISTORICAL_COEFFICIENTS).get("epochs", {}).get(EPOCH)
        if historical:
            return {model_id: Decimal(str(value)) for model_id, value in historical.items()}

    params = read_json(Path("data/raw/node2_params.json"))["params"]
    out: dict[str, Decimal] = {}
    for config in params["poc_params"].get("models") or []:
        model_id = config.get("model_id")
        if model_id:
            out[model_id] = decimal_param(config.get("weight_scale_factor"))
    return out


def model_raw_weight(model_group: dict[str, Any], address: str) -> int:
    for item in model_group.get("validation_weights") or []:
        if item.get("member_address") == address:
            return sum(int(node.get("poc_weight") or "0") for node in item.get("ml_nodes") or [])
    return 0


def scaled_model_weight(raw_weight: int, coefficient: Decimal) -> int:
    return int((Decimal(raw_weight) * coefficient).to_integral_value(rounding=ROUND_DOWN))


def chain_effective_weight(confirmation_weight: int, full_weight: int, scaled_model_total: int) -> int:
    effective = max(0, confirmation_weight)
    if scaled_model_total > 0 and full_weight < scaled_model_total:
        effective = (effective * full_weight) // scaled_model_total
    return min(effective, full_weight)


def calculate_for_source(
    source: str,
    performance: dict[str, Any],
    epoch_group: dict[str, Any],
    model_groups: dict[str, dict[str, Any]],
) -> dict[str, Any]:
    total_weight = int(epoch_group["total_weight"])
    target_weight_entry = next(
        item for item in epoch_group["validation_weights"] if item["member_address"] == TARGET_ADDRESS
    )
    target_weight = int(target_weight_entry["weight"])
    target_confirmation_weight = int(target_weight_entry["confirmation_weight"])
    target_perf = performance[TARGET_ADDRESS]["epochPerformanceSummary"]
    coefficients = model_coefficients()
    raw_model_weights = {
        model_id: model_raw_weight(model_group, TARGET_ADDRESS)
        for model_id, model_group in model_groups.items()
    }
    scaled_model_weights = {
        model_id: scaled_model_weight(raw_weight, coefficients.get(model_id, Decimal(1)))
        for model_id, raw_weight in raw_model_weights.items()
    }
    scaled_model_total = sum(scaled_model_weights.values())
    actual_effective_weight = chain_effective_weight(
        target_confirmation_weight,
        target_weight,
        scaled_model_total,
    )
    # Case-specific counterfactual: cPoC #1 Kimi should have contributed its
    # model-scaled subgroup PoC weight to the parent confirmation reading.
    counterfactual_confirmation_weight = target_confirmation_weight + scaled_model_weights.get(KIMI, 0)
    counterfactual_effective_weight = chain_effective_weight(
        counterfactual_confirmation_weight,
        target_weight,
        scaled_model_total,
    )

    protocol_epoch_reward = fixed_epoch_reward(epoch_group)
    candidate_fixed_reward_gross = (
        Decimal(counterfactual_effective_weight) * Decimal(protocol_epoch_reward)
    ) / Decimal(total_weight)
    actual_reward = Decimal(target_perf.get("rewarded_coins", "0"))
    candidate_fixed_reward_net = candidate_fixed_reward_gross - actual_reward

    return {
        "source": source,
        "primary_method": "validated_loss = counterfactual_effective_weight / epoch_total_weight * fixed_epoch_reward - actual_rewarded_coins",
        "participants_queried": len(performance),
        "epoch_total_weight": str(total_weight),
        "fixed_epoch_reward": str(protocol_epoch_reward),
        "target_weight": str(target_weight),
        "target_confirmation_weight": str(target_confirmation_weight),
        "target_confirmation_ratio": str(Decimal(target_confirmation_weight) / Decimal(target_weight)),
        "target_model_raw_weights": {model_id: str(value) for model_id, value in raw_model_weights.items()},
        "target_model_weight_scale_factors": {model_id: str(coefficients.get(model_id, Decimal(1))) for model_id in raw_model_weights},
        "target_model_scaled_weights": {model_id: str(value) for model_id, value in scaled_model_weights.items()},
        "target_scaled_model_total": str(scaled_model_total),
        "target_actual_effective_weight_v0_2_12": str(actual_effective_weight),
        "counterfactual_missing_model": KIMI,
        "counterfactual_confirmation_weight": str(counterfactual_confirmation_weight),
        "counterfactual_effective_weight_v0_2_12": str(counterfactual_effective_weight),
        "target_actual_earned_coins": target_perf.get("earned_coins", "0"),
        "target_actual_rewarded_coins": target_perf.get("rewarded_coins", "0"),
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
        model_groups = fetch_model_groups(source, base_url)
        summaries.append(calculate_for_source(source, performance, epoch_group, model_groups))

    result = {
        "epoch": EPOCH,
        "target_address": TARGET_ADDRESS,
        "notes": [
            "This is a candidate policy calculation, not a final GRC decision.",
            "The primary method follows the protocol Bitcoin reward calculation: fixed_epoch_reward is minted, invalid/CPoC-reduced shares are not redistributed, and the full root weight remains the denominator.",
            "The numerator is the chain-style release/v0.2.12 counterfactual effective weight, derived from parent confirmation_weight plus the missing Kimi model-scaled subgroup PoC weight, then capped by parent root weight.",
            "If GRC chooses a different reward pool, denominator, or treatment of excluded participants, the result must be recomputed.",
        ],
        "summaries": summaries,
    }
    write_json(OUTPUT, result)
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    sys.exit(main())
