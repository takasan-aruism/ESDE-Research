# Qwen Code Setup Research

確認日: 2026-04-20 JST

目的: ESDE環境で Qwen Code を試すため、ローカル環境、インストール状況、認証方式、ローカルモデル候補を整理する。

## Local Environment

| Item | Observed |
|---|---|
| OS | Ubuntu 24.04.2 LTS |
| GPU | 2x NVIDIA GeForce RTX 5090, driver 570.158.01, CUDA 12.8 |
| Node.js | v22.22.2 |
| npm | 10.9.7 |
| Qwen Code | 0.14.5 installed |
| qwen path | `/home/takasan/.nvm/versions/node/v22.22.2/bin/qwen` |

Qwen Code requires Node.js >= 20. The local Node.js version satisfies this.

Install command used:

```bash
npm install -g @qwen-code/qwen-code@latest
```

Validation:

```bash
qwen --version
# 0.14.5
```

## Important Authentication Change

The Qwen Code GitHub README currently says Qwen OAuth free tier was discontinued on 2026-04-15. Do not plan around free Qwen OAuth.

Practical options:

| Option | Use |
|---|---|
| Alibaba Cloud ModelStudio / Coding Plan API key | Most direct Qwen Code hosted route |
| OpenRouter API key | Easy hosted test route if Qwen models are available there |
| Fireworks AI API key | Hosted route for supported Qwen models |
| Local OpenAI-compatible endpoint | Possible, but requires serving a suitable model separately |

Qwen Code supports `qwen auth` and OpenAI-compatible settings such as `--openai-api-key` and `--openai-base-url`.

## Web Search

Qwen Code has a `web_search` tool. Current docs list providers:

- DashScope
- Tavily
- Google Custom Search

Because Qwen OAuth free tier is no longer reliable, plan to use Tavily or Google Custom Search for web search unless a paid/working DashScope/Coding Plan route is configured.

CLI options visible locally:

```text
--tavily-api-key
--google-api-key
--google-search-engine-id
--web-search-default
```

## Hugging Face / Local Model Note

Qwen Code itself is not installed through Hugging Face. Hugging Face is relevant only if we want to download and serve a local Qwen3-Coder model behind an OpenAI-compatible endpoint.

Clarification for ESDE/QwQ replacement:

- `Qwen Code` = agentic coding CLI installed by npm.
- `Qwen3-Coder` = model family, same operational layer as current `QwQ-32B-AWQ`.
- To replace QwQ locally, download Qwen3-Coder weights, run a local OpenAI-compatible server, then point clients or Qwen Code at that endpoint.

Local candidate model family:

| Model | Fit |
|---|---|
| `Qwen/Qwen3-Coder-30B-A3B-Instruct` | Plausible local experiment on dual RTX 5090, but needs a serving stack |
| `Qwen/Qwen3-Coder-30B-A3B-Instruct-FP8` | More plausible local experiment if FP8 serving path works |
| `Qwen/Qwen3-Coder-480B-A35B-Instruct` | Not practical for this workstation |
| `Qwen/Qwen3-Coder-480B-A35B-Instruct-FP8` | Still not practical for this workstation |

The 30B-A3B model is MoE: about 30.5B total parameters and 3.3B activated. It supports 256K native context and is designed for agentic coding/tool use, but local serving must be validated separately.

HF API check for `Qwen/Qwen3-Coder-30B-A3B-Instruct-FP8`:

- `gated: false`
- architecture: `Qwen3MoeForCausalLM`
- `model_type: qwen3_moe`
- quantization: `fp8`
- files: 4 safetensor shards plus tokenizer/config files
- used storage: about 31.2GB

Recommended local model path:

```text
/storage/engine/qwen/Qwen3-Coder-30B-A3B-Instruct-FP8
```

The install flow is conceptually similar to QwQ:

1. Download source model from Hugging Face.
2. Serve it with a runtime that supports `qwen3_moe` and FP8.
3. Expose an OpenAI-compatible API.
4. Use that model name from ESDE or Qwen Code.

Difference from current QwQ:

- QwQ already has validated TensorRT-LLM engines.
- Qwen3-Coder is MoE (`qwen3_moe`), so TensorRT-LLM `1.1.0rc5` compatibility is not assumed.
- The official model card says FP8 can be used with `transformers`, `sglang`, and `vllm`; for this workstation, vLLM is likely the first local serving route to test before attempting TensorRT-LLM build.

## Local TensorRT-LLM FP4 Test

User requested 4-bit quantization. For TensorRT-LLM, prefer ModelOpt/NVFP4 over AWQ for Qwen3-MoE because TensorRT-LLM's Qwen3 support path lists NVFP4/FP4, while AWQ/GPTQ are not the main supported Qwen3 route.

Downloaded model:

```text
/storage/engine/qwen/Qwen3-Coder-30B-A3B-Instruct-FP4
```

HF model:

```text
NVFP4/Qwen3-Coder-30B-A3B-Instruct-FP4
```

Observed local size:

| Path | Size |
|---|---:|
| `/storage/engine/qwen/Qwen3-Coder-30B-A3B-Instruct-FP4` | 17G |
| `/storage/engine/qwen/Qwen3-Coder-30B-A3B-Instruct-FP8` | 30G |

FP8 was downloaded first during investigation. It is not the requested target and can be removed if disk cleanup is preferred.

Model config highlights:

| Item | Value |
|---|---|
| architecture | `Qwen3MoeForCausalLM` |
| model_type | `qwen3_moe` |
| max_position_embeddings | 262144 |
| total experts | 128 |
| experts per token | 8 |
| quant_algo | `NVFP4` |
| KV cache quantization | FP8 |

Startup command used for the first working test:

```bash
docker run -d --name qwen3coder_fp4_srv \
  --gpus all \
  --ipc=host \
  --ulimit memlock=-1 \
  --ulimit stack=67108864 \
  -p 8003:8003 \
  -v /storage:/storage \
  nvcr.io/nvidia/tensorrt-llm/release:1.1.0rc5 \
  bash -lc "python3 -c \"p='/usr/local/lib/python3.12/dist-packages/tensorrt_llm/_torch/modules/fused_moe/quantization.py'; s=open(p).read(); s=s.replace('logger.warning(', 'trtllm_logger.logger.warning('); open(p,'w').write(s)\"; trtllm-serve serve /storage/engine/qwen/Qwen3-Coder-30B-A3B-Instruct-FP4 --backend pytorch --host 0.0.0.0 --port 8003 --max_batch_size 4 --max_num_tokens 4096 --max_seq_len 8192 --tp_size 1 --ep_size 1 --kv_cache_free_gpu_memory_fraction 0.75 --trust_remote_code --log_level info"
```

Important runtime note:

- First attempt failed with `NameError: name 'logger' is not defined` inside TensorRT-LLM `fused_moe/quantization.py`.
- The working command applies an in-container temporary patch that replaces `logger.warning(` with `trtllm_logger.logger.warning(`.
- This patch is not persisted to the host filesystem.

Working endpoint:

```text
http://127.0.0.1:8003/v1
```

Model API check:

```json
{"id":"Qwen3-Coder-30B-A3B-Instruct-FP4","owned_by":"tensorrt_llm"}
```

Observed GPU memory:

- GPU0: about 28.9GB used after startup
- GPU1: desktop only

This first run uses `tp_size=1` and `ep_size=1`. It proves the model works on one RTX 5090, but leaves little GPU0 memory headroom. A later tuning pass should test TP2/EP2 or lower KV/cache settings.

Smoke/performance test script:

```text
scripts/qwen3coder_fp4_smoke_eval.py
```

Smoke results:

| Test | Result |
|---|---|
| Japanese summary | OK, no mojibake |
| Code generation | OK, but returned Markdown fences despite "code only" |
| Bug fix | Mixed: found issue, but ignored "corrected version only" and hit token limit |
| Strict JSON | OK |
| `response_format: json_object` | OK for simple JSON |
| Tool call shape | Returned Qwen XML-style `<tool_call>` in content, not OpenAI `tool_calls` array |
| Throughput | about 130-160 completion tok/s on short prompts |

Initial read:

- The model is usable and fast enough for local coding experiments.
- It is better than QwQ as a coding-target model family, but prompt discipline still matters.
- OpenAI-compatible structured `tool_calls` may not be native in this TensorRT-LLM serving path; Qwen's XML tool-call convention appears in content.
- For ESDE replacement testing, use direct API calls first before wiring it into higher-level agents.

## Desktop Findings

The actual desktop path is:

```text
/home/takasan/デスクトップ
```

Notable files/directories:

- `rtx5090-tensor-parallel/`: old TensorRT/RTX5090 work area
- `setting_tensorrtllm.odt`: likely TensorRT-LLM notes
- a file whose name appears to contain a Hugging Face token

Do not paste passwords or tokens into chat. If Hugging Face access is needed, prefer:

```bash
huggingface-cli login
```

or set a token in a local shell session:

```bash
export HF_TOKEN='...'
```

Then run download commands from that shell.

## Recommended Next Step

Fastest Qwen Code trial:

1. Use the installed `qwen` CLI.
2. Configure a hosted OpenAI-compatible provider via `qwen auth` or settings.
3. Add Tavily or Google Custom Search if web search is required.
4. Test on ESDE with a read-only prompt first.

Local-model route should be a second phase:

1. Download `Qwen/Qwen3-Coder-30B-A3B-Instruct-FP8` or a validated quantization.
2. Serve it with an OpenAI-compatible API.
3. Point Qwen Code at that endpoint.
4. Validate tool calling, Japanese output, and code editing behavior.

## Sources

- Qwen Code GitHub README: https://github.com/QwenLM/qwen-code/blob/main/README.md
- Qwen Code npm package: https://www.npmjs.com/package/%40qwen-code/qwen-code
- Qwen Code web search docs: https://qwenlm.github.io/qwen-code-docs/en/developers/tools/web-search/
- Qwen3-Coder-30B-A3B-Instruct: https://huggingface.co/Qwen/Qwen3-Coder-30B-A3B-Instruct
- Qwen3-Coder-30B-A3B-Instruct-FP8: https://huggingface.co/Qwen/Qwen3-Coder-30B-A3B-Instruct-FP8
- Qwen3-Coder-480B-A35B-Instruct: https://huggingface.co/Qwen/Qwen3-Coder-480B-A35B-Instruct
