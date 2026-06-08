#!/usr/bin/env python3
"""Scan epochs for case #3-style Kimi/Qwen cPoC restitution candidates."""

from __future__ import annotations

import argparse
import json
import os
import urllib.error
import time
import urllib.parse
import urllib.request
from collections import Counter
from decimal import Decimal, ROUND_DOWN, getcontext
from pathlib import Path
from typing import Any


getcontext().prec = 50

BASE_URLS = (
    "http://node2.gonka.ai:8000",
    "http://node1.gonka.ai:8000",
    "http://gonka.spv.re:8000",
)
RAW_DIR = Path("data/raw/case3_scan")
ARCHIVE_STATE_DIR = Path("data/raw/archive_state")
OUT_PATH = Path("data/derived/case3_epoch_scan_265_280.json")
HISTORICAL_COEFFICIENTS = Path("data/derived/historical_model_coefficients.json")
ARCHIVE_QUERY_OFFSET = 281

KIMI = "moonshotai/Kimi-K2.6"
QWEN = "Qwen/Qwen3-235B-A22B-Instruct-2507-FP8"
MODELS = (QWEN, KIMI)
GUARDIANS = {
    "gonka1y2a9p56kv044327uycmqdexl7zs82fs5ryv5le",
    "gonka1dkl4mah5erqggvhqkpc8j3qs5tyuetgdy552cp",
    "gonka1kx9mca3xm8u8ypzfuhmxey66u0ufxhs7nm6wc5",
}


def load_dotenv() -> None:
    env_path = Path(".env")
    if not env_path.exists():
        return
    for line in env_path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        os.environ.setdefault(key.strip(), value.strip().strip("'\""))


def archive_api_base() -> str | None:
    base = os.environ.get("GONKA_ARCHIVE_API_BASE", "").strip().rstrip("/")
    return base or None


def safe_name(value: str) -> str:
    return "".join(ch if ch.isalnum() else "_" for ch in value).strip("_")


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        json.dump(payload, handle, indent=2, sort_keys=True)
        handle.write("\n")


def fetch_json(path: str, params: dict[str, Any] | None = None, cache: bool = True) -> Any:
    query = f"?{urllib.parse.urlencode(params)}" if params else ""
    cache_path = RAW_DIR / f"{safe_name(path + query)}.json"
    if cache and cache_path.exists():
        with cache_path.open("r", encoding="utf-8") as handle:
            return json.load(handle)

    last_error: Exception | None = None
    for attempt in range(1, 7):
        for base_url in BASE_URLS:
            url = f"{base_url}{path}{query}"
            try:
                req = urllib.request.Request(
                    url,
                    headers={"User-Agent": "gonka-grc-case3-range-scan/1.0"},
                )
                with urllib.request.urlopen(req, timeout=30) as response:
                    payload = json.load(response)
                break
            except (urllib.error.HTTPError, urllib.error.URLError, TimeoutError, json.JSONDecodeError) as exc:
                last_error = exc
                continue
        else:
            time.sleep(min(10, attempt * 1.5))
            continue
        break
    else:
        raise RuntimeError(f"failed to fetch {path}{query}: {last_error}") from last_error
    if cache:
        write_json(cache_path, payload)
    return payload


def fetch_archive_json_with_height(path: str, height: int) -> Any:
    base = archive_api_base()
    if not base:
        raise RuntimeError("GONKA_ARCHIVE_API_BASE is required when historical snapshot cache is missing")
    req = urllib.request.Request(
        f"{base}{path}",
        headers={
            "User-Agent": "gonka-grc-case3-range-scan/1.0",
            "x-cosmos-block-height": str(height),
        },
    )
    with urllib.request.urlopen(req, timeout=30) as response:
        return json.load(response)


def decimal_param(value: dict[str, Any] | None) -> Decimal:
    if not value:
        return Decimal(0)
    return Decimal(str(value.get("value") or "0")) * (Decimal(10) ** int(value.get("exponent") or 0))


def int_of(value: Any) -> int:
    try:
        return int(value or 0)
    except (TypeError, ValueError):
        return 0


def params() -> dict[str, Any]:
    return fetch_json("/chain-api/productscience/inference/inference/params")["params"]


def model_coefficients(chain_params: dict[str, Any]) -> dict[str, Decimal]:
    out: dict[str, Decimal] = {}
    for config in chain_params["poc_params"].get("models") or []:
        model_id = config.get("model_id")
        if model_id:
            out[model_id] = decimal_param(config.get("weight_scale_factor"))
    return out


def historical_model_coefficients(epoch: int) -> dict[str, Decimal] | None:
    if not HISTORICAL_COEFFICIENTS.exists():
        return None
    historical = read_json(HISTORICAL_COEFFICIENTS).get("epochs", {}).get(str(epoch))
    if not historical:
        return None
    return {model_id: Decimal(str(value)) for model_id, value in historical.items()}


def fixed_epoch_reward(chain_params: dict[str, Any], epoch: int) -> int:
    br = chain_params["bitcoin_reward_params"]
    initial = int(br["initial_epoch_reward"])
    decay = decimal_param(br["decay_rate"])
    genesis = int(br.get("genesis_epoch") or "1")
    elapsed = max(0, epoch - genesis)
    return int(Decimal(initial) * (decay * Decimal(elapsed)).exp())


def epoch_group(epoch: int, model_id: str | None = None) -> dict[str, Any]:
    query = {"model_id": model_id} if model_id else None
    return fetch_json(
        f"/chain-api/productscience/inference/inference/epoch_group_data/{epoch}",
        query,
    ).get("epoch_group_data") or {}


def performance(epoch: int, address: str) -> dict[str, Any]:
    return fetch_json(
        f"/chain-api/productscience/inference/inference/epoch_performance_summary/{epoch}/{address}"
    ).get("epochPerformanceSummary") or {}


def cpoc_events(epoch: int) -> list[dict[str, Any]]:
    return sorted(
        fetch_json(f"/chain-api/productscience/inference/inference/confirmation_poc_events/{epoch}").get("events") or [],
        key=lambda item: int_of(item.get("event_sequence")),
    )


def stage_commits(height: str) -> dict[tuple[str, str], int]:
    payload = fetch_json(f"/chain-api/productscience/inference/inference/all_poc_v2_store_commits/{height}")
    out: dict[tuple[str, str], int] = {}
    for row in payload.get("commits") or []:
        out[(row.get("participant_address", ""), row.get("model_id", ""))] = int_of(row.get("count"))
    return out


def stage_validations(height: str) -> dict[tuple[str, str], list[dict[str, Any]]]:
    payload = fetch_json(f"/chain-api/productscience/inference/inference/poc_v2_validations_for_stage/{height}")
    out: dict[tuple[str, str], list[dict[str, Any]]] = {}
    for group in payload.get("poc_validation") or []:
        key = (group.get("participant", ""), group.get("model_id", ""))
        out[key] = group.get("poc_validation") or []
    return out


def stage_snapshot(height: str) -> dict[str, Any] | None:
    matches = sorted(ARCHIVE_STATE_DIR.glob(f"poc_validation_snapshot_{height}_at_*.json"))
    if not matches:
        query_height = int(height) + ARCHIVE_QUERY_OFFSET
        payload = fetch_archive_json_with_height(
            f"/productscience/inference/inference/poc_validation_snapshot/{height}",
            query_height,
        )
        write_json(ARCHIVE_STATE_DIR / f"poc_validation_snapshot_{height}_at_{query_height}.json", payload)
        matches = sorted(ARCHIVE_STATE_DIR.glob(f"poc_validation_snapshot_{height}_at_*.json"))
    payload = json.load(matches[-1].open("r", encoding="utf-8"))
    if not payload.get("found"):
        return None
    return payload.get("snapshot")


def snapshot_model_maps(snapshot: dict[str, Any] | None) -> tuple[int, dict[str, dict[str, int]]]:
    if not snapshot:
        return 0, {}
    total_network_weight = int_of(snapshot.get("total_network_weight"))
    by_model: dict[str, dict[str, int]] = {}
    for model in snapshot.get("model_voting_powers") or []:
        by_model[model["model_id"]] = {
            item["address"]: int_of(item.get("voting_power"))
            for item in model.get("voting_powers") or []
        }
    return total_network_weight, by_model


def voting_power_map(model_group: dict[str, Any]) -> dict[str, int]:
    return {
        item["member_address"]: int_of(item.get("voting_power"))
        for item in model_group.get("validation_weights") or []
        if item.get("member_address")
    }


def raw_model_weight(model_group: dict[str, Any], address: str) -> int:
    for item in model_group.get("validation_weights") or []:
        if item.get("member_address") == address:
            return sum(int_of(node.get("poc_weight")) for node in item.get("ml_nodes") or [])
    return 0


def scaled_model_weight(raw_weight: int, coefficient: Decimal) -> int:
    return int((Decimal(raw_weight) * coefficient).to_integral_value(rounding=ROUND_DOWN))


def chain_effective_weight(confirmation_weight: int, full_weight: int, scaled_model_total: int) -> int:
    effective = max(0, confirmation_weight)
    if scaled_model_total > 0 and full_weight < scaled_model_total:
        effective = (effective * full_weight) // scaled_model_total
    return min(effective, full_weight)


def model_status(
    *,
    address: str,
    model_id: str,
    commits: dict[tuple[str, str], int],
    validations: dict[tuple[str, str], list[dict[str, Any]]],
    voting_powers: dict[str, int],
    total_network_weight: int,
    snapshot_found: bool,
) -> dict[str, Any]:
    count = commits.get((address, model_id), 0)
    vals = validations.get((address, model_id), [])
    valid_weight = 0
    invalid_weight = 0
    guardian_valid = 0
    guardian_invalid = 0
    guardian_no_vote = 0
    voted_guardians = set()
    for row in vals:
        validator = row.get("validator_participant_address")
        if validator not in voting_powers:
            continue
        value = int_of(row.get("validated_weight"))
        if value > 0:
            valid_weight += voting_powers[validator]
            if validator in GUARDIANS:
                guardian_valid += 1
                voted_guardians.add(validator)
        else:
            invalid_weight += voting_powers[validator]
            if validator in GUARDIANS:
                guardian_invalid += 1
                voted_guardians.add(validator)
    for guardian in GUARDIANS:
        if guardian in voting_powers and guardian not in voted_guardians:
            guardian_no_vote += 1

    threshold = Decimal(2) * Decimal(total_network_weight) / Decimal(3) if total_network_weight else Decimal(0)
    if count <= 0:
        reason = "no_submit"
        passed = False
    elif Decimal(valid_weight) > threshold:
        reason = "pass_weight"
        passed = True
    elif Decimal(invalid_weight) > threshold:
        reason = "invalid_weight_majority"
        passed = False
    elif guardian_valid > 0 and guardian_invalid == 0:
        reason = "pass_guardian"
        passed = True
    elif guardian_invalid > 0 and guardian_valid == 0:
        reason = "guardian_invalid"
        passed = False
    else:
        reason = "weight_and_guardian_shortfall"
        passed = False

    return {
        "model_id": model_id,
        "submitted": count > 0,
        "commit_count": count,
        "passed": passed,
        "reason": reason,
        "valid_weight": valid_weight,
        "invalid_weight": invalid_weight,
        "guardian_valid": guardian_valid,
        "guardian_invalid": guardian_invalid,
        "guardian_no_vote": guardian_no_vote,
        "snapshot_found": snapshot_found,
        "total_network_weight": total_network_weight,
        "two_thirds_total_network_weight": str(threshold),
    }


def scan_epoch(epoch: int, chain_params: dict[str, Any], default_coefficients: dict[str, Decimal]) -> dict[str, Any]:
    coefficients = historical_model_coefficients(epoch) or default_coefficients
    aggregate = epoch_group(epoch)
    root_total_weight = int_of(aggregate.get("total_weight"))
    root_weights = {
        item["member_address"]: item
        for item in aggregate.get("validation_weights") or []
        if item.get("member_address")
    }
    model_groups = {model_id: epoch_group(epoch, model_id) for model_id in MODELS}
    voting_powers = {model_id: voting_power_map(group) for model_id, group in model_groups.items()}
    events = cpoc_events(epoch)
    stage_data = []
    for event in events:
        height = str(event.get("trigger_height"))
        snapshot = stage_snapshot(height)
        snapshot_total_network_weight, snapshot_voting_powers = snapshot_model_maps(snapshot)
        stage_data.append(
            {
                "event": event,
                "commits": stage_commits(height),
                "validations": stage_validations(height),
                "snapshot": {
                    "found": snapshot is not None,
                    "poc_stage_start_height": snapshot.get("poc_stage_start_height") if snapshot else None,
                    "snapshot_height": snapshot.get("snapshot_height") if snapshot else None,
                    "total_network_weight": snapshot.get("total_network_weight") if snapshot else None,
                    "model_voting_power_counts": {
                        model_id: len(items)
                        for model_id, items in snapshot_voting_powers.items()
                    },
                    "model_voting_power_sums": {
                        model_id: str(sum(items.values()))
                        for model_id, items in snapshot_voting_powers.items()
                    },
                },
                "snapshot_total_network_weight": snapshot_total_network_weight,
                "snapshot_voting_powers": snapshot_voting_powers,
            }
        )

    zero_reward_rows = []
    for address, root_item in sorted(root_weights.items()):
        perf = performance(epoch, address)
        actual_reward = int_of(perf.get("rewarded_coins"))
        if actual_reward != 0:
            continue

        statuses = []
        for stage in stage_data:
            model_statuses = [
                model_status(
                    address=address,
                    model_id=model_id,
                    commits=stage["commits"],
                    validations=stage["validations"],
                    voting_powers=stage["snapshot_voting_powers"].get(model_id) or voting_powers.get(model_id, {}),
                    total_network_weight=stage["snapshot_total_network_weight"] or root_total_weight,
                    snapshot_found=stage["snapshot"]["found"],
                )
                for model_id in MODELS
            ]
            statuses.append(
                {
                    "trigger_height": stage["event"].get("trigger_height"),
                    "event_sequence": stage["event"].get("event_sequence"),
                    "models": [item for item in model_statuses if item["submitted"]],
                    "submitted_model_count": sum(1 for item in model_statuses if item["submitted"]),
                }
            )

        full_weight = int_of(root_item.get("weight"))
        confirmation_weight = int_of(root_item.get("confirmation_weight"))
        scaled_weights = {
            model_id: scaled_model_weight(raw_model_weight(model_groups[model_id], address), coefficients.get(model_id, Decimal(1)))
            for model_id in MODELS
        }
        scaled_total = sum(scaled_weights.values())
        actual_effective_weight = chain_effective_weight(confirmation_weight, full_weight, scaled_total)
        counterfactual_effective_weight = chain_effective_weight(
            confirmation_weight + scaled_weights.get(KIMI, 0),
            full_weight,
            scaled_total,
        )

        cpoc1_models = statuses[0]["models"] if statuses else []
        cpoc1_kimi = next((item for item in cpoc1_models if item["model_id"] == KIMI), None)
        cpoc1_qwen = next((item for item in cpoc1_models if item["model_id"] == QWEN), None)
        later_statuses = statuses[1:4]
        later_all_pass = bool(
            len(later_statuses) == 3
            and all(any(model["model_id"] == KIMI and model["passed"] for model in stage["models"]) for stage in later_statuses)
        )
        affected = bool(
            cpoc1_kimi
            and cpoc1_kimi["reason"] == "weight_and_guardian_shortfall"
            and cpoc1_qwen
            and cpoc1_qwen["reason"] == "pass_guardian"
            and later_all_pass
        )
        epoch_reward = fixed_epoch_reward(chain_params, epoch)
        restitution = 0
        if affected and root_total_weight:
            restitution = int(
                (Decimal(counterfactual_effective_weight) * Decimal(epoch_reward) / Decimal(root_total_weight))
                .to_integral_value(rounding=ROUND_DOWN)
            )

        zero_reward_rows.append(
            {
                "address": address,
                "affected": affected,
                "why": "case3_pattern" if affected else "zero_reward_but_pattern_not_matched",
                "root_weight": full_weight,
                "parent_confirmation_weight": confirmation_weight,
                "actual_effective_weight_v0_2_12": actual_effective_weight,
                "counterfactual_effective_weight_v0_2_12": counterfactual_effective_weight,
                "scaled_model_weights": scaled_weights,
                "actual_rewarded_coins": actual_reward,
                "restitution_ngonka": restitution,
                "restitution_gonka": str(Decimal(restitution) / Decimal(1_000_000_000)),
                "statuses": statuses,
            }
        )
        time.sleep(0.03)

    return {
        "epoch": epoch,
        "participants": len(root_weights),
        "root_total_weight": root_total_weight,
        "cpoc_event_count": len(events),
        "cpoc_snapshots": [stage["snapshot"] for stage in stage_data],
        "zero_reward_count": len(zero_reward_rows),
        "affected_count": sum(1 for row in zero_reward_rows if row["affected"]),
        "affected": [row for row in zero_reward_rows if row["affected"]],
        "zero_reward_rows": zero_reward_rows,
        "cpoc1_reason_counts": dict(
            Counter(
                ";".join(f"{item['model_id'].split('/')[-1]}:{item['reason']}" for item in (row["statuses"][0]["models"] if row["statuses"] else []))
                or "no_submit"
                for row in zero_reward_rows
            )
        ),
    }


def main() -> int:
    load_dotenv()
    parser = argparse.ArgumentParser()
    parser.add_argument("--from-epoch", type=int, default=265)
    parser.add_argument("--to-epoch", type=int, default=280)
    args = parser.parse_args()

    chain_params = params()
    coefficients = model_coefficients(chain_params)
    epochs = []
    for epoch in range(args.from_epoch, args.to_epoch + 1):
        print(f"scan epoch {epoch}", flush=True)
        epochs.append(scan_epoch(epoch, chain_params, coefficients))

    result = {
        "sources": list(BASE_URLS),
        "from_epoch": args.from_epoch,
        "to_epoch": args.to_epoch,
        "model_ids": list(MODELS),
        "affected_total": sum(item["affected_count"] for item in epochs),
        "epochs": epochs,
    }
    write_json(OUT_PATH, result)
    print(json.dumps({
        "affected_total": result["affected_total"],
        "epochs": [
            {
                "epoch": item["epoch"],
                "zero_reward_count": item["zero_reward_count"],
                "affected_count": item["affected_count"],
                "affected": [
                    {
                        "address": row["address"],
                        "restitution_gonka": row["restitution_gonka"],
                    }
                    for row in item["affected"]
                ],
            }
            for item in epochs
        ],
    }, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
