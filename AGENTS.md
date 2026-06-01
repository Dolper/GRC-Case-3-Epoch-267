# Project Agent Instructions

This repository is a local, reproducible validation workspace for Gonka GRC case #3 / epoch 267.

## Scope

- Primary incident epoch: `267`
- Primary address: `gonka1j7x6dv42xehe9e5au4ku3wvzwtqlegfjhlvzj6`
- Primary question: whether the epoch 267 `failed_confirmation_poc` exclusion is supported by chain facts and whether it should be treated separately from the epoch 249-253 stuck `poc_weight` case.

## Sources

Use public Gonka nodes as independent sources where possible:

- `http://node2.gonka.ai:8000/chain-rpc`
- `http://node1.gonka.ai:8000/chain-rpc`
- `http://gonka.spv.re:8000/chain-rpc`

For API queries, replace `/chain-rpc` with `/chain-api`.

## Verification Commands

- Collect and compare epoch 267 facts:
  - `python3 scripts/collect_epoch267.py`

## Data Rules

- Keep raw API responses under `data/raw/`.
- Keep derived summaries under `data/derived/`.
- Do not edit raw JSON by hand; regenerate it with the collection script.
- Documentation may quote only the small fields needed to justify conclusions.

## Delivery Mode

`no-deploy`: this is a local investigation repository with no production deployment surface.
