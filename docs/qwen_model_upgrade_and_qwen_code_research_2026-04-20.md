# Qwen Model Upgrade and Qwen Code Research

確認日: 2026-04-20 JST

目的: 現在使っている `Qwen/QwQ-32B-AWQ` と、比較的新しい Qwen 系モデル、Qwen Code、WEB検索機能の関係を整理する。

## Current Local Model

現在の実運用モデル:

- Source model: `Qwen/QwQ-32B-AWQ`
- Local source/tokenizer: `/storage/engine/qwen/QwQ-32B-AWQ`
- Runtime engine: `/storage/engines/qwq32b_tp2_fp16_8k_b8`
- Runtime container: `qwq_tp2_srv`
- Serving stack: TensorRT-LLM `1.1.0rc5`, TP=2, max sequence 8192
- Product identity: released `QwQ-32B` AWQ 4-bit model, not `QwQ-32B-Preview`

Important point:

- `QwQ-32B-AWQ` is a local model only. It has no built-in web browsing or web search capability by itself.
- Web access would need to be supplied by an external agent/tool layer.

## Newer Local Upgrade Candidate Already Present

This machine already has Qwen3 assets:

- Source model: `/storage/engine/qwen/Qwen3-32B-AWQ`
- TensorRT engine: `/storage/engines/qwen3_32b_tp2_int4_64k`
- Engine size from inventory: about 20G

Local `Qwen3-32B-AWQ/config.json`:

- `architectures`: `Qwen3ForCausalLM`
- `model_type`: `qwen3`
- Quantization: AWQ 4-bit
- `torch_dtype`: `float16`
- `transformers_version`: `4.51.3`
- `max_position_embeddings`: `40960`

Local TensorRT engine `/storage/engines/qwen3_32b_tp2_int4_64k/config.json`:

- TensorRT-LLM version: `1.1.0rc5`
- Architecture: `Qwen3ForCausalLM`
- Quantization: `W4A16`
- TP size: `2`
- Build max input length: `65536`
- Build max sequence length: `65536`
- Max batch size: `1`
- RoPE scaling: YaRN factor `2.0`, original max position embeddings `32768`

Initial read:

- This is the most practical local upgrade candidate because it is already downloaded and already has a TensorRT engine.
- It should be tested separately before replacing `qwq_tp2_srv`.
- It is likely better for general chat, instruction following, tool use, and optional thinking/non-thinking control than QwQ-32B.
- It is not a dedicated coding model like Qwen3-Coder.

## Current vs Qwen3-32B-AWQ

| Item | Current: QwQ-32B-AWQ | Candidate: Qwen3-32B-AWQ |
|---|---|---|
| HF repo | `Qwen/QwQ-32B-AWQ` | `Qwen/Qwen3-32B-AWQ` |
| Local source | `/storage/engine/qwen/QwQ-32B-AWQ` | `/storage/engine/qwen/Qwen3-32B-AWQ` |
| Architecture | `Qwen2ForCausalLM` | `Qwen3ForCausalLM` |
| Family | Qwen2.5-based reasoning model | Qwen3 general/reasoning/instruction model |
| Parameters | 32.5B | 32.8B |
| Quantization | AWQ 4-bit source, TRT engine `W4A16_GPTQ` | AWQ 4-bit source, TRT engine `W4A16` |
| Thinking behavior | Always reasoning-oriented QwQ behavior | Has thinking and non-thinking modes |
| Official context | 131,072 with YaRN guidance; current TRT engine serves 8192 | 32,768 native, 131,072 with YaRN; local TRT engine built for 65,536 |
| WEB search | No built-in web search | No built-in web search |
| Best local role | Reasoning model already validated | Likely upgrade for general ESDE/local assistant if engine starts cleanly |

## Qwen Code

Qwen Code is not just a model. It is an open-source terminal coding agent, similar in role to Claude Code/Gemini CLI style tooling.

Official repository:

- `QwenLM/qwen-code`
- Package: `@qwen-code/qwen-code`
- Requires Node.js 20+
- Current official README notes Qwen OAuth free tier was discontinued on 2026-04-15; use API key, Alibaba Cloud Coding Plan, OpenRouter, Fireworks AI, or compatible providers.

Important capabilities:

- Reads and edits codebases.
- Runs shell commands.
- Supports OpenAI/Anthropic/Gemini-compatible providers.
- Supports IDE integration.
- Supports Skills, SubAgents, MCP, and other agent workflow features.
- Has WEB features through tools, not through the base LLM itself.

## Qwen Code WEB Search

Qwen Code has a `web_search` tool.

Official docs say `web_search`:

- Performs internet search.
- Supports multiple providers.
- Returns concise answers with source citations when available.
- Providers: DashScope, Tavily, Google Custom Search.
- Can be disabled via `tools.exclude: ["web_search"]`.

Important 2026-04 caveat:

- Older docs say DashScope is automatically available for Qwen OAuth users.
- The Qwen Code GitHub README says Qwen OAuth free tier was discontinued on 2026-04-15.
- Therefore, for this machine, assume Qwen Code WEB search will need explicit provider setup unless the chosen Qwen Code authentication path supplies it.

Practical setup options:

- Tavily API key: easiest independent search provider for agentic research.
- Google Custom Search API key + search engine ID: useful for Google-backed search but more setup.
- DashScope: likely tied to Alibaba/Qwen account/API setup; verify at install time.

## Qwen3-Coder and Qwen Code

Qwen Code is optimized for Qwen3-Coder models.

Relevant official/local-upgrade candidates:

- `Qwen/Qwen3-Coder-30B-A3B-Instruct`
  - 30.5B total parameters, 3.3B activated.
  - MoE model.
  - Native 262,144 context.
  - Non-thinking only; does not emit `<think>` blocks.
  - Designed for agentic coding and repository-scale work.
  - More relevant to Qwen Code than `Qwen3-32B-AWQ`.
- `Qwen/Qwen3-Coder-30B-A3B-Instruct-FP8`
  - Official FP8 variant.
  - Better local-serving candidate than BF16 if runtime support is good.
- `Qwen/Qwen3-Coder-480B-A35B-Instruct`
  - Much stronger but not practical for local dual RTX 5090 serving.
  - Better accessed through hosted API/provider.

Initial local judgment:

- For Qwen Code, use a hosted provider first. It avoids spending days on local MoE serving and gives better agent quality.
- For local ESDE LLM, test the already-present `Qwen3-32B-AWQ` TensorRT engine before downloading Qwen3-Coder.
- If local coding model is desired later, evaluate Qwen3-Coder-30B-A3B quantized/FP8 serving with vLLM or SGLang first; TensorRT-LLM compatibility and memory behavior need separate verification.

## Hosted Latest: Qwen3.6-Plus

Qwen Code README reports:

- 2026-04-02: `Qwen3.6-Plus` is live via Alibaba Cloud ModelStudio OpenAI-compatible API.
- Qwen Code examples use model id `qwen3.6-plus`.

Initial read:

- This is a hosted frontier/agentic model path, not a local open-weight replacement for `QwQ-32B-AWQ`.
- It is likely the best candidate for Qwen Code if API access is acceptable.
- It should be treated separately from local model upgrade.

## Recommendation

Recommended path:

1. Keep `Qwen/QwQ-32B-AWQ` as known-good fallback.
2. Test local `Qwen3-32B-AWQ` TensorRT engine:
   - create or start a separate container on another port, e.g. `8003`
   - verify `/v1/models`
   - verify chat completion in thinking and non-thinking style if supported by serving layer
   - compare latency, VRAM, output quality, Japanese behavior, and ESDE integration behavior
3. Install Qwen Code separately as an agent tool.
4. For Qwen Code, prefer hosted `qwen3.6-plus` or Qwen3-Coder provider first.
5. Configure WEB search explicitly in Qwen Code:
   - Tavily or Google Custom Search if using non-Qwen OAuth/API-key auth
   - DashScope only if the chosen Alibaba/Qwen auth path makes it available
6. Only after Qwen Code hosted usage is understood, decide whether local Qwen3-Coder is worth the storage/build cost.

## Local Qwen3 32B Startup Test on 2026-04-20

User memory: Qwen3-32B-AWQ previously produced unreadable/garbled output. Investigation shows there are two separate issues:

- The model/engine can start in the current environment.
- Strict structured output is unreliable without post-processing, and Qwen3 often emits empty `<think></think>` blocks plus Markdown fences.

### Tested Runtime

Base Docker image:

- `nvcr.io/nvidia/tensorrt-llm/release:1.1.0rc5`
- Host driver: NVIDIA `570.158.01`, CUDA runtime reported by host as `12.8`
- Container warns that it was built with CUDA `12.9` and is running in CUDA minor-version compatibility mode.

Official compatibility context:

- NVIDIA TensorRT-LLM release notes for 1.0 say dense Qwen3 TensorRT-engine support was added.
- Older TensorRT-LLM 0.19 era reports show `Qwen3ForCausalLM` was not recognized.
- Current installed image `1.1.0rc5` is new enough to load the existing TensorRT Qwen3 engines.
- Newer TensorRT-LLM releases have broader Qwen3 support, but current local image can at least serve these prebuilt engines.

### TP1 8k Engine Test

Engine:

- `/storage/engines/qwen3_32b_tp1_int4_8k`
- Source/tokenizer: `/storage/engine/qwen/Qwen3-32B-AWQ`
- Runtime command used:

```bash
docker run -d \
  --name qwen3_tp1_8k_test \
  --gpus all \
  --network host \
  --ipc host \
  --shm-size 8g \
  -e CUDA_VISIBLE_DEVICES=0 \
  -v /storage:/storage \
  nvcr.io/nvidia/tensorrt-llm/release:1.1.0rc5 \
  trtllm-serve serve /storage/engines/qwen3_32b_tp1_int4_8k \
    --backend trt \
    --tokenizer /storage/engine/qwen/Qwen3-32B-AWQ \
    --tp_size 1 \
    --host 0.0.0.0 \
    --port 8003 \
    --max_batch_size 8 \
    --max_num_tokens 8192 \
    --max_seq_len 8192 \
    --log_level info
```

Result:

- `/v1/models` returned `qwen3_32b_tp1_int4_8k`.
- Short Japanese completion worked.
- Simple JSON prompt returned valid JSON content but wrapped in `<think></think>` and Markdown code fences.
- CSV prompt produced readable Japanese, but schema was not strictly followed.
- No unreadable mojibake was observed in short tests.
- GPU0 memory use after startup: about 31GB, leaving little headroom.

Observed response shape:

```text
<think>

</think>

...
```

### TP2 64k Engine Test

Engine:

- `/storage/engines/qwen3_32b_tp2_int4_64k`
- Source/tokenizer: `/storage/engine/qwen/Qwen3-32B-AWQ`
- Runtime command used:

```bash
docker run -d \
  --name qwen3_tp2_64k_test \
  --gpus all \
  --network host \
  --ipc host \
  --shm-size 8g \
  -e CUDA_VISIBLE_DEVICES=0,1 \
  -v /storage:/storage \
  nvcr.io/nvidia/tensorrt-llm/release:1.1.0rc5 \
  trtllm-serve serve /storage/engines/qwen3_32b_tp2_int4_64k \
    --backend trt \
    --tokenizer /storage/engine/qwen/Qwen3-32B-AWQ \
    --tp_size 2 \
    --host 0.0.0.0 \
    --port 8004 \
    --max_batch_size 1 \
    --max_num_tokens 65536 \
    --max_seq_len 65536 \
    --log_level info
```

Result:

- `/v1/models` returned `qwen3_32b_tp2_int4_64k`.
- Short Japanese completion worked.
- Simple JSON prompt returned valid JSON content but wrapped in `<think></think>` and Markdown code fences.
- CSV prompt was readable but malformed: it used a fenced block and merged the second data row into the first row.
- No unreadable mojibake was observed in short tests.
- GPU0/GPU1 memory use after startup: about 30GB each.
- Startup log included:
  - `Using an engine plan file across different models of devices is not supported and is likely to affect performance or even cause errors or deadlock.`
  - This warning should be treated seriously if the engine was built on a different RTX 5090/driver/TensorRT context.

### Unsupported `response_format`

`response_format: {"type":"json_object"}` was tested against the TP2 64k server.

Result:

- Request failed with HTTP 400.
- Error: `Request is specified with GuidedDecodingParams, but GuidedDecoder is not setup.`
- Therefore, this TensorRT-LLM server cannot be relied on for OpenAI-style JSON mode unless the server is recreated with a valid guided decoding configuration.

### Past Garbling Evidence

Existing Aruism output files show Qwen3-AWQ generated:

- Chinese explanatory text despite Japanese-oriented tasks.
- Broken JSON/schema snippets.
- Repeated `<|...|>`-style special-token fragments.
- Examples like malformed keys or corrupted text in generated JSON.

This looks less like UTF-8 terminal mojibake and more like generation/control failure:

- Prompt asks for strict structure, but the model drifts into analysis/explanation.
- Thinking blocks and Markdown fences are present.
- Some outputs mix Japanese, Chinese, English, and special token residue.
- Greedy or low-temperature settings may worsen repetition; Qwen3 docs recommend non-greedy sampling.

### Generation Settings Notes

Official Qwen3 guidance:

- Thinking mode: `temperature=0.6`, `top_p=0.95`, `top_k=20`.
- Non-thinking mode: `temperature=0.7`, `top_p=0.8`, `top_k=20`.
- Greedy decoding is discouraged.

Current ESDE defaults in `language/lexicon/mapper_a1.py`:

- `temperature=0.3`
- `top_p` and `top_k` constants exist but are not sent in the payload.

For Qwen3 testing, use:

- `temperature=0.7`
- `top_p=0.8`
- prompt prefix `/no_think`
- post-process by removing `<think>...</think>` and Markdown fences

### Practical Conclusion

In this environment, the actually bootable local Qwen3 32B candidates are:

1. `qwen3_32b_tp1_int4_8k`
   - Boots on GPU0.
   - Better for short-context local tests.
   - Uses nearly all of one RTX 5090.
   - Batch-capable (`max_batch_size=8`).
   - Output still needs cleanup.
2. `qwen3_32b_tp2_int4_64k`
   - Boots on GPU0+GPU1.
   - Better for long-context experiments.
   - Uses nearly all memory on both GPUs.
   - `max_batch_size=1`.
   - Has engine/device warning; treat as experimental.
   - Output still needs cleanup.

For production ESDE replacement, do not switch directly from QwQ to Qwen3 yet. Recommended next step is a controlled A/B harness:

- Run QwQ on port `8001` and Qwen3 TP1 on port `8003` or Qwen3 TP2 on port `8004`.
- Use the same mapper/auditor prompts.
- Apply Qwen3-specific sampling and cleanup.
- Measure JSON parse rate, Japanese-only compliance, schema compliance, latency, and VRAM.
- Promote only if parse rate and semantic quality beat the current QwQ fallback.

After testing, both temporary containers were stopped and removed:

- `qwen3_tp1_8k_test`
- `qwen3_tp2_64k_test`

GPU memory was released.

## Qwen3 Removal Decision

2026-04-20 update:

- Decision: do not use Qwen3 locally for ESDE production.
- Reason: QwQ-32B-AWQ is already stable enough for the current local runtime, while Qwen3 adds operational complexity and structured-output risk.
- Removed:
  - `/storage/engine/qwen/Qwen3-32B-AWQ`
  - `/storage/engine/qwen/Qwen3-32B`
- Reclaimed: about 81G.
- Still present and delete-pending due to root ownership:
  - `/storage/models/qwen3`
  - `/storage/engines/qwen3_32b_tp2_int4_64k`
  - `/storage/engines/qwen3_32b_tp1_int4_8k`

Interactive sudo command needed to finish deletion:

```bash
sudo rm -r /storage/models/qwen3 \
  /storage/engines/qwen3_32b_tp2_int4_64k \
  /storage/engines/qwen3_32b_tp1_int4_8k
```

## Sources

- QwQ-32B-AWQ: https://huggingface.co/Qwen/QwQ-32B-AWQ
- Qwen3-32B-AWQ: https://huggingface.co/Qwen/Qwen3-32B-AWQ
- Qwen Code GitHub: https://github.com/QwenLM/qwen-code
- Qwen Code overview: https://qwenlm.github.io/qwen-code-docs/en/users/overview/
- Qwen Code web search docs: https://qwenlm.github.io/qwen-code-docs/en/developers/tools/web-search/
- Qwen Code web fetch docs: https://qwenlm.github.io/qwen-code-docs/en/tools/web-fetch/
- Qwen3-Coder-30B-A3B-Instruct: https://huggingface.co/Qwen/Qwen3-Coder-30B-A3B-Instruct
- Qwen3-Coder-30B-A3B-Instruct-FP8: https://huggingface.co/Qwen/Qwen3-Coder-30B-A3B-Instruct-FP8
- Qwen3-Coder-480B-A35B-Instruct: https://huggingface.co/Qwen/Qwen3-Coder-480B-A35B-Instruct
