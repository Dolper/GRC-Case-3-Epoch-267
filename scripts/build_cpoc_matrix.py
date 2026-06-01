#!/usr/bin/env python3
"""Build an independent cPoC event matrix for epoch 267."""

from __future__ import annotations

import json
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
DERIVED = Path("data/derived/epoch267_cpoc_matrix.json")

GUARDIAN_PARTICIPANTS = {
    "gonka1y2a9p56kv044327uycmqdexl7zs82fs5ryv5le",
    "gonka1dkl4mah5erqggvhqkpc8j3qs5tyuetgdy552cp",
    "gonka1kx9mca3xm8u8ypzfuhmxey66u0ufxhs7nm6wc5",
}


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


def fetch_endpoint(name: str, path: str) -> Any:
    payload = fetch_json(f"{BASE_URL}{path}")
    write_json(RAW_DIR / f"{name}.json", payload)
    return payload


def validation_weight_map() -> dict[str, int]:
    epoch_group = read_json(Path("data/raw/node2_epoch_group_data.json"))["epoch_group_data"]
    return {item["member_address"]: int(item["weight"]) for item in epoch_group["validation_weights"]}


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
                "code_level_pass_unresolved": True,
                "unresolved_reason": "Historical PoCValidationSnapshot.ModelVotingPowers is not available from the queried nodes; code-level pass uses voting powers, not raw validated_weight sums.",
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
        "model_total_weight": {k: str(v) for k, v in model_total_weight.items()},
        "direct_committers_by_model": {
            model_id: sorted(participants)
            for model_id, participants in direct_committers_by_model.items()
        },
        "target_rows": target_rows,
        "rows": rows,
    }


def main() -> int:
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
        "snapshot_limitation": "The queried nodes no longer expose the historical PoCValidationSnapshot for trigger 4122271, so this matrix records raw cPoC evidence and does not assert code-level pass/fail from raw validated_weight fields.",
        "target_stage_status": target_stage_status,
        "stages": stages,
    }
    write_json(DERIVED, result)
    print(json.dumps(result["target_stage_status"], indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    sys.exit(main())
