# Sources

## Chain Nodes

Primary:

- RPC: `http://node2.gonka.ai:8000/chain-rpc`
- API: `http://node2.gonka.ai:8000/chain-api`

Cross-checks:

- RPC: `http://node1.gonka.ai:8000/chain-rpc`
- API: `http://node1.gonka.ai:8000/chain-api`
- RPC: `http://gonka.spv.re:8000/chain-rpc`
- API: `http://gonka.spv.re:8000/chain-api`

## Queried Chain API Paths

- `/cosmos/base/tendermint/v1beta1/node_info`
- `/productscience/inference/inference/params`
- `/productscience/inference/inference/epoch_group_data/267`
- `/productscience/inference/inference/excluded_participants/267`
- `/productscience/inference/inference/epoch_performance_summary/267/{participant}`
- `/productscience/inference/inference/confirmation_poc_events/267`
- `/productscience/inference/inference/all_poc_v2_store_commits/{trigger_height}`
- `/productscience/inference/inference/poc_v2_validations_for_stage/{trigger_height}`
- `/productscience/inference/inference/all_mlnode_weight_distributions/{trigger_height}`

## GitHub References

- Release `v0.2.13`: `https://github.com/gonka-ai/gonka/releases/tag/release/v0.2.13`
- Compare `v0.2.12...v0.2.13`: `https://github.com/gonka-ai/gonka/compare/release/v0.2.12...release/v0.2.13`
- Target commit observed in release/API metadata: `c716df26cb8802e341a007f79b445352c53a3bee`
