#!/usr/bin/env python3
"""Build an independent cPoC event matrix for epoch 267."""

from __future__ import annotations

import json
import os
import sys
import urllib.request
from collections import defaultdict
from decimal import Decimal, getcontext
from pathlib import Path
from typing import Any


getcontext().prec = 50

EPOCH = "267"
TARGET_ADDRESS = "gonka1j7x6dv42xehe9e5au4ku3wvzwtqlegfjhlvzj6"
BASE_URL = "http://node2.gonka.ai:8000"
RAW_DIR = Path("data/raw/cpoc")
ARCHIVE_STATE_DIR = Path("data/raw/archive_state")
DERIVED = Path("data/derived/epoch267_cpoc_matrix.json")
ARCHIVE_QUERY_OFFSET = 281

GUARDIAN_PARTICIPANTS = {
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


def fetch_json(url: str) -> Any:
    req = urllib.request.Request(url, headers={"User-Agent": "gonka-grc-epoch267-validation/1.0"})
    with urllib.request.urlopen(req, timeout=30) as response:
        return json.load(response)


def fetch_json_with_height(url: str, height: int) -> Any:
    req = urllib.request.Request(
        url,
        headers={
            "User-Agent": "gonka-grc-epoch267-validation/1.0",
            "x-cosmos-block-height": str(height),
        },
    )
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


def fetch_endpoint(name: str, path: str) -> Any:
    cached_path = RAW_DIR / f"{name}.json"
    if cached_path.exists():
        return read_json(cached_path)
    payload = fetch_json(f"{BASE_URL}{path}")
    write_json(cached_path, payload)
    return payload


def validation_weight_map() -> dict[str, int]:
    epoch_group = read_json(Path("data/raw/node2_epoch_group_data.json"))["epoch_group_data"]
    return {item["member_address"]: int(item["weight"]) for item in epoch_group["validation_weights"]}


def load_snapshot(stage_height: str) -> dict[str, Any] | None:
    matches = sorted(ARCHIVE_STATE_DIR.glob(f"poc_validation_snapshot_{stage_height}_at_*.json"))
    if not matches:
        base = archive_api_base()
        if not base:
            return None
        query_height = int(stage_height) + ARCHIVE_QUERY_OFFSET
        path = f"/productscience/inference/inference/poc_validation_snapshot/{stage_height}"
        payload = fetch_json_with_height(f"{base}{path}", query_height)
        write_json(
            ARCHIVE_STATE_DIR / f"poc_validation_snapshot_{stage_height}_at_{query_height}.json",
            payload,
        )
        matches = sorted(ARCHIVE_STATE_DIR.glob(f"poc_validation_snapshot_{stage_height}_at_*.json"))
    payload = read_json(matches[-1])
    if not payload.get("found"):
        return None
    return payload.get("snapshot")


def snapshot_model_maps(snapshot: dict[str, Any] | None) -> tuple[int, dict[str, dict[str, int]]]:
    if not snapshot:
        return 0, {}
    total_network_weight = int(snapshot.get("total_network_weight") or 0)
    by_model: dict[str, dict[str, int]] = {}
    for model in snapshot.get("model_voting_powers") or []:
        model_id = model["model_id"]
        by_model[model_id] = {
            item["address"]: int(item["voting_power"])
            for item in model.get("voting_powers") or []
        }
    return total_network_weight, by_model


def load_events() -> list[dict[str, Any]]:
    return fetch_endpoint(
        "confirmation_poc_events_267",
        f"/chain-api/productscience/inference/inference/confirmation_poc_events/{EPOCH}",
    )["events"]


def load_stage(stage_height: str) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    commits = fetch_endpoint(
        f"all_poc_v2_store_commits_{stage_height}",
        f"/chain-api/productscience/inference/inference/all_poc_v2_store_commits/{stage_height}",
    )["commits"]
    validations = fetch_endpoint(
        f"poc_v2_validations_for_stage_{stage_height}",
        f"/chain-api/productscience/inference/inference/poc_v2_validations_for_stage/{stage_height}",
    )["poc_validation"]
    return commits, validations


def summarize_validations(validations: list[dict[str, Any]]) -> dict[tuple[str, str], dict[str, Any]]:
    by_key: dict[tuple[str, str], dict[str, Any]] = {}
    for row in validations:
        participant = row["participant"]
        model_id = row.get("model_id", "")
        vals = row.get("poc_validation", [])
        raw_validated_weight_sum = 0
        invalid_count = 0
        raw_guardian_valid = 0
        raw_guardian_invalid = 0
        validators = []
        for item in vals:
            validator = item["validator_participant_address"]
            weight = int(item["validated_weight"])
            validators.append(
                {
                    "validator": validator,
                    "validated_weight": weight,
                    "is_guardian": validator in GUARDIAN_PARTICIPANTS,
                }
            )
            if weight > 0:
                raw_validated_weight_sum += weight
                if validator in GUARDIAN_PARTICIPANTS:
                    raw_guardian_valid += 1
            else:
                invalid_count += 1
                if validator in GUARDIAN_PARTICIPANTS:
                    raw_guardian_invalid += 1
        by_key[(participant, model_id)] = {
            "validation_rows": len(vals),
            "raw_validated_weight_sum": raw_validated_weight_sum,
            "invalid_count": invalid_count,
            "raw_guardian_valid": raw_guardian_valid,
            "raw_guardian_invalid": raw_guardian_invalid,
            "validators": validators,
        }
    return by_key


def stage_matrix(event: dict[str, Any], weights: dict[str, int]) -> dict[str, Any]:
    stage_height = event["trigger_height"]
    snapshot = load_snapshot(stage_height)
    snapshot_total_network_weight, snapshot_model_voting_powers = snapshot_model_maps(snapshot)
    commits, validations = load_stage(stage_height)
    validation_by_key = summarize_validations(validations)
    commit_by_key = {
        (item["participant_address"], item["model_id"]): item for item in commits
    }
    models = sorted({item["model_id"] for item in commits} | {key[1] for key in validation_by_key})
    direct_committers_by_model = defaultdict(set)
    for participant, model_id in commit_by_key:
        direct_committers_by_model[model_id].add(participant)

    model_total_weight: dict[str, int] = {}
    for model_id in models:
        participants = {participant for participant, model in commit_by_key if model == model_id}
        participants.update({participant for participant, model in validation_by_key if model == model_id})
        model_total_weight[model_id] = sum(weights.get(participant, 0) for participant in participants)

    rows = []
    for key in sorted(set(commit_by_key) | set(validation_by_key)):
        participant, model_id = key
        commit = commit_by_key.get(key)
        validation = validation_by_key.get(
            key,
            {
                "validation_rows": 0,
                "raw_validated_weight_sum": 0,
                "invalid_count": 0,
                "raw_guardian_valid": 0,
                "raw_guardian_invalid": 0,
                "validators": [],
            },
        )
        total = model_total_weight.get(model_id, 0)
        raw_threshold = Decimal(2) * Decimal(total) / Decimal(3) if total else Decimal(0)
        snapshot_total = snapshot_total_network_weight or total
        state_threshold = Decimal(2) * Decimal(snapshot_total) / Decimal(3) if snapshot_total else Decimal(0)
        model_voting_powers = snapshot_model_voting_powers.get(model_id, {})
        state_valid_voting_power_sum = 0
        state_invalid_voting_power_sum = 0
        state_guardian_valid = 0
        state_guardian_invalid = 0
        state_validator_addresses = set()
        for validator in validation["validators"]:
            address = validator["validator"]
            voting_power = model_voting_powers.get(address)
            if voting_power is None:
                continue
            state_validator_addresses.add(address)
            if validator["validated_weight"] > 0:
                state_valid_voting_power_sum += voting_power
                if address in GUARDIAN_PARTICIPANTS:
                    state_guardian_valid += 1
            else:
                state_invalid_voting_power_sum += voting_power
                if address in GUARDIAN_PARTICIPANTS:
                    state_guardian_invalid += 1
        state_guardian_no_vote = sum(
            1
            for address in GUARDIAN_PARTICIPANTS
            if address in model_voting_powers and address not in state_validator_addresses
        )
        state_pass_by_weight = Decimal(state_valid_voting_power_sum) > state_threshold if snapshot_total else False
        state_pass_by_guardian = state_guardian_valid > 0 and state_guardian_invalid == 0
        if state_pass_by_weight:
            state_result = "pass_weight"
        elif state_pass_by_guardian:
            state_result = "pass_guardian"
        elif state_invalid_voting_power_sum > state_threshold:
            state_result = "invalid_weight_majority"
        else:
            state_result = "weight_and_guardian_shortfall"
        direct_model_validator_set = direct_committers_by_model[model_id]
        filtered_guardian_valid = 0
        filtered_guardian_invalid = 0
        for validator in validation["validators"]:
            if validator["validator"] not in direct_model_validator_set:
                continue
            if not validator["is_guardian"]:
                continue
            if validator["validated_weight"] > 0:
                filtered_guardian_valid += 1
            else:
                filtered_guardian_invalid += 1
        rows.append(
            {
                "participant": participant,
                "model_id": model_id,
                "submitted": commit is not None,
                "commit_count": commit.get("count") if commit else 0,
                "participant_weight": weights.get(participant, 0),
                "model_total_weight": str(total),
                "two_thirds_raw_model_weight": str(raw_threshold),
                "raw_validated_weight_sum": validation["raw_validated_weight_sum"],
                "invalid_count": validation["invalid_count"],
                "raw_guardian_valid": validation["raw_guardian_valid"],
                "raw_guardian_invalid": validation["raw_guardian_invalid"],
                "direct_model_guardian_valid": filtered_guardian_valid,
                "direct_model_guardian_invalid": filtered_guardian_invalid,
                "state_snapshot_found": snapshot is not None,
                "state_total_network_weight": str(snapshot_total) if snapshot_total else "0",
                "state_two_thirds_total_network_weight": str(state_threshold),
                "state_valid_voting_power_sum": state_valid_voting_power_sum,
                "state_invalid_voting_power_sum": state_invalid_voting_power_sum,
                "state_guardian_valid": state_guardian_valid,
                "state_guardian_invalid": state_guardian_invalid,
                "state_guardian_no_vote": state_guardian_no_vote,
                "state_result": state_result if snapshot is not None else "snapshot_missing",
                "state_passed": state_pass_by_weight or state_pass_by_guardian,
            }
        )

    target_rows = [
        row for row in rows
        if row["participant"] == TARGET_ADDRESS
    ]

    return {
        "event": event,
        "stage_height": stage_height,
        "commit_count": len(commits),
        "validation_subject_count": len(validation_by_key),
        "snapshot": {
            "found": snapshot is not None,
            "poc_stage_start_height": snapshot.get("poc_stage_start_height") if snapshot else None,
            "snapshot_height": snapshot.get("snapshot_height") if snapshot else None,
            "total_network_weight": snapshot.get("total_network_weight") if snapshot else None,
            "model_voting_power_counts": {
                model_id: len(items)
                for model_id, items in snapshot_model_voting_powers.items()
            },
            "model_voting_power_sums": {
                model_id: str(sum(items.values()))
                for model_id, items in snapshot_model_voting_powers.items()
            },
        },
        "model_total_weight": {k: str(v) for k, v in model_total_weight.items()},
        "direct_committers_by_model": {
            model_id: sorted(participants)
            for model_id, participants in direct_committers_by_model.items()
        },
        "target_rows": target_rows,
        "rows": rows,
    }


def main() -> int:
    load_dotenv()
    weights = validation_weight_map()
    events = load_events()
    stages = [stage_matrix(event, weights) for event in events]

    target_stage_status = [
        {
            "event_sequence": stage["event"]["event_sequence"],
            "trigger_height": stage["stage_height"],
            "target_rows": stage["target_rows"],
        }
        for stage in stages
    ]
    result = {
        "epoch": EPOCH,
        "target_address": TARGET_ADDRESS,
        "guardian_participants": sorted(GUARDIAN_PARTICIPANTS),
        "code_pass_rule": "Non-slot mode passes if model-voting-power valid votes exceed 2/3 of total network weight; if no majority, guardian tiebreaker is evaluated only after filtering validations to validators with voting power for that model.",
        "snapshot_source": "Cached historical PoCValidationSnapshot responses stored in data/raw/archive_state/.",
        "target_stage_status": target_stage_status,
        "stages": stages,
    }
    write_json(DERIVED, result)
    print(json.dumps(result["target_stage_status"], indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    sys.exit(main())
