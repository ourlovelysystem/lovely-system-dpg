# Bedrock model reference (us-east-1)

Snapshot taken 2026-09-19 by actually invoking each candidate via
`bedrock-runtime:Converse` with a trivial prompt — not just checking whether
Bedrock lists it. "Functional" means the account can invoke it today; it does
not mean quality, cost, or suitability have been evaluated. This is a
point-in-time snapshot, not a live check — Bedrock's catalog and this
account's access change over time. `backend/lambda_function.py`'s `MODELS`
constant is the copy actually served to the personality-creation page; update
both together if this is ever refreshed.

Candidate models were drawn from `bedrock:ListFoundationModels` filtered to
models with `TEXT` in both input and output modalities, excluding rerankers
and provisioned-throughput-only capacity variants (e.g. `amazon.nova-pro-v1:0:24k`,
which duplicates the on-demand `amazon.nova-pro-v1:0` entry but requires a
purchased provisioned-throughput commitment to invoke at all).

Models requiring `INFERENCE_PROFILE` are invoked via their `us.` cross-region
profile ID, not the bare model ID — that's the `invoke_id` column below.

## Functional (68) — offered in the personality-creation dropdown

| Provider | Model | invoke_id |
|---|---|---|
| AI21 Labs | *(none functional — see excluded)* | |
| Amazon | Nova Pro | `amazon.nova-pro-v1:0` |
| Amazon | Nova Lite | `amazon.nova-lite-v1:0` |
| Amazon | Nova Micro | `amazon.nova-micro-v1:0` |
| Amazon | Nova 2 Lite | `us.amazon.nova-2-lite-v1:0` |
| Anthropic | Claude Haiku 4.5 | `us.anthropic.claude-haiku-4-5-20251001-v1:0` |
| Anthropic | Claude Sonnet 4.5 | `us.anthropic.claude-sonnet-4-5-20250929-v1:0` |
| Anthropic | Claude Sonnet 4.6 | `us.anthropic.claude-sonnet-4-6` |
| Anthropic | Claude Sonnet 5 | `us.anthropic.claude-sonnet-5` |
| Anthropic | Claude Opus 4.5 | `us.anthropic.claude-opus-4-5-20251101-v1:0` |
| Anthropic | Claude Opus 4.6 | `us.anthropic.claude-opus-4-6-v1` |
| Anthropic | Claude Opus 4.7 | `us.anthropic.claude-opus-4-7` |
| Anthropic | Claude Opus 4.8 | `us.anthropic.claude-opus-4-8` |
| Anthropic | Claude Opus 5 | `us.anthropic.claude-opus-5` |
| DeepSeek | DeepSeek V3.2 | `deepseek.v3.2` |
| DeepSeek | DeepSeek-R1 | `us.deepseek.r1-v1:0` |
| Google | Gemma 3 4B IT | `google.gemma-3-4b-it` |
| Google | Gemma 3 12B IT | `google.gemma-3-12b-it` |
| Google | Gemma 3 27B PT | `google.gemma-3-27b-it` |
| Meta | Llama 3 8B Instruct | `meta.llama3-8b-instruct-v1:0` |
| Meta | Llama 3 70B Instruct | `meta.llama3-70b-instruct-v1:0` |
| Meta | Llama 3.1 8B Instruct | `us.meta.llama3-1-8b-instruct-v1:0` |
| Meta | Llama 3.1 70B Instruct | `us.meta.llama3-1-70b-instruct-v1:0` |
| Meta | Llama 3.3 70B Instruct | `us.meta.llama3-3-70b-instruct-v1:0` |
| Meta | Llama 4 Scout 17B Instruct | `us.meta.llama4-scout-17b-instruct-v1:0` |
| Meta | Llama 4 Maverick 17B Instruct | `us.meta.llama4-maverick-17b-instruct-v1:0` |
| MiniMax | MiniMax M2 | `minimax.minimax-m2` |
| MiniMax | MiniMax M2.1 | `minimax.minimax-m2.1` |
| MiniMax | MiniMax M2.5 | `minimax.minimax-m2.5` |
| Mistral AI | Mistral 7B Instruct | `mistral.mistral-7b-instruct-v0:2` |
| Mistral AI | Mixtral 8x7B Instruct | `mistral.mixtral-8x7b-instruct-v0:1` |
| Mistral AI | Mistral Small (24.02) | `mistral.mistral-small-2402-v1:0` |
| Mistral AI | Mistral Large (24.02) | `mistral.mistral-large-2402-v1:0` |
| Mistral AI | Ministral 3B | `mistral.ministral-3-3b-instruct` |
| Mistral AI | Ministral 3 8B | `mistral.ministral-3-8b-instruct` |
| Mistral AI | Ministral 14B 3.0 | `mistral.ministral-3-14b-instruct` |
| Mistral AI | Magistral Small 2509 | `mistral.magistral-small-2509` |
| Mistral AI | Devstral 2 123B | `mistral.devstral-2-123b` |
| Mistral AI | Mistral Large 3 | `mistral.mistral-large-3-675b-instruct` |
| Mistral AI | Pixtral Large (25.02) | `us.mistral.pixtral-large-2502-v1:0` |
| Mistral AI | Voxtral Mini 3B 2507 | `mistral.voxtral-mini-3b-2507` |
| Mistral AI | Voxtral Small 24B 2507 | `mistral.voxtral-small-24b-2507` |
| Moonshot AI | Kimi K2.5 | `moonshotai.kimi-k2.5` |
| Moonshot AI | Kimi K2 Thinking | `moonshot.kimi-k2-thinking` |
| Moonshot AI | Kimi K3 | `us.moonshotai.kimi-k3` |
| NVIDIA | NVIDIA Nemotron Nano 9B v2 | `nvidia.nemotron-nano-9b-v2` |
| NVIDIA | NVIDIA Nemotron Nano 12B v2 VL BF16 | `nvidia.nemotron-nano-12b-v2` |
| NVIDIA | Nemotron Nano 3 30B | `nvidia.nemotron-nano-3-30b` |
| NVIDIA | NVIDIA Nemotron 3 Super 120B A12B | `nvidia.nemotron-super-3-120b` |
| OpenAI | gpt-oss-20b | `openai.gpt-oss-20b-1:0` |
| OpenAI | gpt-oss-120b | `openai.gpt-oss-120b-1:0` |
| OpenAI | GPT OSS Safeguard 20B | `openai.gpt-oss-safeguard-20b` |
| OpenAI | GPT OSS Safeguard 120B | `openai.gpt-oss-safeguard-120b` |
| OpenAI | GPT-5.6 Terra | `us.openai.gpt-5.6-terra` |
| OpenAI | GPT-5.6 Luna | `us.openai.gpt-5.6-luna` |
| OpenAI | GPT-5.6 Sol | `us.openai.gpt-5.6-sol` |
| OpenAI | GPT-6 Astra | `us.openai.gpt-6-astra` |
| Qwen | Qwen3 32B (dense) | `qwen.qwen3-32b-v1:0` |
| Qwen | Qwen3 Coder Next | `qwen.qwen3-coder-next` |
| Qwen | Qwen3-Coder-30B-A3B-Instruct | `qwen.qwen3-coder-30b-a3b-v1:0` |
| Qwen | Qwen3 Next 80B A3B | `qwen.qwen3-next-80b-a3b` |
| Qwen | Qwen3 VL 235B A22B | `qwen.qwen3-vl-235b-a22b` |
| Writer | Writer Palmyra Vision 7B | `writer.palmyra-vision-7b` |
| Writer | Palmyra X4 | `us.writer.palmyra-x4-v1:0` |
| Writer | Palmyra X5 | `us.writer.palmyra-x5-v1:0` |
| xAI | Grok 4.6 | `us.xai.grok-4.6` |
| Z.AI | GLM 4.7 | `zai.glm-4.7` |
| Z.AI | GLM 4.7 Flash | `zai.glm-4.7-flash` |
| Z.AI | GLM 5 | `zai.glm-5` |

## Excluded from testing entirely

- **Rerankers** (`cohere.rerank-v3-5:0`) — not a generative chat model.
- **Provisioned-throughput-only variants** (e.g. `amazon.nova-pro-v1:0:24k`,
  `:300k`, `amazon.nova-lite-v1:0:24k`/`:300k`, `amazon.nova-micro-v1:0:24k`/`:128k`) —
  require a purchased provisioned-throughput commitment; the on-demand
  variant of the same model is already listed above.
- **No text input** (`amazon.nova-2-sonic-v1:0`) — audio-only input.

## Tested but not functional (7)

| Provider | Model | invoke_id tried | Why it failed |
|---|---|---|---|
| Anthropic | Claude Sonnet 4 | `us.anthropic.claude-sonnet-4-20250514-v1:0` | Access denied — marked Legacy by provider, no use in last 30 days |
| Anthropic | Claude Opus 4.1 | `us.anthropic.claude-opus-4-1-20250805-v1:0` | Same — Legacy, inactive 30+ days |
| Anthropic | Claude Fable 5 | `us.anthropic.claude-fable-5` | `data retention mode 'default' is not available for this model` |
| Anthropic | Claude Fable 5.1 | `us.anthropic.claude-fable-5-1` | Same data-retention-mode error |
| AI21 Labs | Jamba 1.5 Large | `ai21.jamba-1-5-large-v1:0` | Access denied — Legacy, inactive 30+ days |
| AI21 Labs | Jamba 1.5 Mini | `ai21.jamba-1-5-mini-v1:0` | Access denied — Legacy, inactive 30+ days |
| TwelveLabs | Pegasus v1.2 | `twelvelabs.pegasus-1-2-v1:0` | Not a supported chat/text model for Converse |

The Claude Fable 5/5.1 failure looks fixable (a data-retention configuration
issue, not an access/entitlement problem) but wasn't chased further here —
flagging rather than debugging, since it's outside this pass's scope.
