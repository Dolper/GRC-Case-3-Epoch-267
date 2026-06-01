#!/usr/bin/env python3
"""Collect and compare public chain facts for Gonka epoch 267."""

from __future__ import annotations

import hashlib
import json
import sys
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any


EPOCH = "267"
TARGET_ADDRESS = "gonka1j7x6dv42xehe9e5au4ku3wvzwtqlegfjhlvzj6"

SOURCES = {
    "node2": "http://node2.gonka.ai:8000",
    "node1": "http://node1.gonka.ai:8000",
    "spv": "http://gonka.spv.re:8000",
}

API_PATHS = {
    "node_info": "/chain-api/cosmos/base/tendermint/v1beta1/node_info",
    "params": "/chain-api/productscience/inference/inference/params",
    "epoch_group_data": f"/chain-api/productscience/inference/inference/epoch_group_data/{EPOCH}",
    "excluded_participants": f"/chain-api/productscience/inference/inference/excluded_participants/{EPOCH}",
}

RPC_PATHS = {
    "status": "/chain-rpc/status",
    "exclusion_block": "/chain-rpc/block?height=4122552",
}

RAW_DIR = Path("data/raw")
DERIVED_DIR = Path("data/derived")


def fetch_json(url: str) -> Any:
    req = urllib.request.Request(url, headers={"User-Agent": "gonka-grc-epoch267-validation/1.0"})
    with urllib.request.urlopen(req, timeout=30) as response:
        return json.load(response)


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        json.dump(payload, handle, indent=2, sort_keys=True)
        handle.write("\n")


def stable_digest(payload: Any) -> str:
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def get_epoch_group(data: dict[str, Any]) -> dict[str, Any]:
    return data.get("epoch_group_data", {})


def find_member(epoch_group: dict[str, Any], address: str) -> dict[str, Any] | None:
    for member in epoch_group.get("validation_weights", []):
        if member.get("member_address") == address:
            return member
    return None


def find_exclusion(excluded_data: dict[str, Any], address: str) -> dict[str, Any] | None:
    for item in excluded_data.get("items", []):
        if item.get("address") == address:
            return item
    return None


def decimal_param(value: dict[str, Any] | None) -> float | None:
    if not value:
        return None
    try:
        return int(value["value"]) * (10 ** int(value["exponent"]))
    except (KeyError, TypeError, ValueError):
        return None


def summarize_source(source: str, raw: dict[str, Any]) -> dict[str, Any]:
    epoch_group = get_epoch_group(raw["epoch_group_data"])
    member = find_member(epoch_group, TARGET_ADDRESS)
    exclusion = find_exclusion(raw["excluded_participants"], TARGET_ADDRESS)
    params = raw.get("params", {}).get("params", {})
    poc_models = params.get("poc_params", {}).get("models", [])

    summary: dict[str, Any] = {
        "source": source,
        "status_height": raw.get("status", {}).get("result", {}).get("sync_info", {}).get("latest_block_height"),
        "application_version": raw.get("node_info", {}).get("application_version", {}).get("version"),
        "application_commit": raw.get("node_info", {}).get("application_version", {}).get("git_commit"),
        "epoch_index": epoch_group.get("epoch_index"),
        "epoch_group_id": epoch_group.get("epoch_group_id"),
        "poc_start_block_height": epoch_group.get("poc_start_block_height"),
        "effective_block_height": epoch_group.get("effective_block_height"),
        "last_block_height": epoch_group.get("last_block_height"),
        "total_weight": epoch_group.get("total_weight"),
        "number_of_requests": epoch_group.get("number_of_requests"),
        "sub_group_models": epoch_group.get("sub_group_models"),
        "confirmation_weight_scales": epoch_group.get("confirmation_weight_scales"),
        "validation_weight_count": len(epoch_group.get("validation_weights", [])),
        "excluded_count": len(raw.get("excluded_participants", {}).get("items", [])),
        "target_exclusion": exclusion,
        "target_member": member,
        "poc_models": [
            {
                "model_id": model.get("model_id"),
                "penalty_start_epoch": model.get("penalty_start_epoch"),
                "weight_scale_factor": decimal_param(model.get("weight_scale_factor")),
            }
            for model in poc_models
        ],
        "digests": {
            key: stable_digest(raw[key])
            for key in ["node_info", "params", "epoch_group_data", "excluded_participants", "status"]
            if key in raw
        },
    }

    if member:
        weight = int(member.get("weight", "0"))
        confirmation_weight = int(member.get("confirmation_weight", "0"))
        summary["target_confirmation_ratio"] = confirmation_weight / weight if weight else None

    return summary


def collect() -> tuple[dict[str, Any], list[str]]:
    all_raw: dict[str, Any] = {}
    errors: list[str] = []

    for source, base_url in SOURCES.items():
        source_raw: dict[str, Any] = {}
        for name, path in {**API_PATHS, **RPC_PATHS}.items():
            url = f"{base_url}{path}"
            try:
                payload = fetch_json(url)
            except (urllib.error.URLError, TimeoutError, json.JSONDecodeError) as exc:
                errors.append(f"{source} {name}: {exc}")
                continue
            source_raw[name] = payload
            write_json(RAW_DIR / f"{source}_{name}.json", payload)
        all_raw[source] = source_raw

    return all_raw, errors


def main() -> int:
    raw_by_source, errors = collect()
    summaries = []
    for source, raw in raw_by_source.items():
        required = {"status", "node_info", "params", "epoch_group_data", "excluded_participants"}
        missing = sorted(required - raw.keys())
        if missing:
            errors.append(f"{source}: missing required responses: {', '.join(missing)}")
            continue
        summaries.append(summarize_source(source, raw))

    result = {
        "epoch": EPOCH,
        "target_address": TARGET_ADDRESS,
        "summaries": summaries,
        "errors": errors,
    }
    write_json(DERIVED_DIR / "epoch267_summary.json", result)

    print(json.dumps(result, indent=2, sort_keys=True))
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())
