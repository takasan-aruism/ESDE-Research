# QwQ/Qwen 32B TensorRT-LLM Docker Runtime Snapshot

確認日: 2026-04-20 12:35 JST

目的: ESDE から使うローカル 32B LLM の Docker/TensorRT-LLM 実行構成を、AI が再接続後に復元しやすい形で保存する。

## Current Status

- 2026-04-20 12:56 JST 頃に `docker start qwq_tp2_srv` で起動確認した。
- `127.0.0.1:8001/v1/models` は `qwq32b_tp2_fp16_8k_b8` を返した。
- `127.0.0.1:8001/v1/chat/completions` に短い生成リクエストを投げ、応答が返るところまで確認した。
- 起動後の `nvidia-smi` では GPU 0/1 がそれぞれ約 30GB 使用。`trtllm-serve` と MPI worker が各 GPU に載っている。
- 起動時は CPU を数コア分使う。観測時は `trtllm-serve` と MPI worker が 1-3 コア程度を使ったが、システム全体としては余裕あり。
- 別件で `v915s2_memory_readout.py --tag smoke` が CPU 1コア程度を継続使用していた。
- 停止済みログから、直近の主経路も `qwq_tp2_srv` で、2026-04-10 05:15 JST 頃まで `POST /v1/chat/completions` に応答していた。

Observed smoke test:

```bash
curl -sS --max-time 90 http://127.0.0.1:8001/v1/chat/completions \
  -H 'Content-Type: application/json' \
  -d '{"model":"qwq32b_tp2_fp16_8k_b8","messages":[{"role":"user","content":"日本語で一言だけ返答して。"}],"max_tokens":32,"temperature":0}'
```

Result: HTTP response returned successfully. The model began with reasoning-style English text despite the Japanese short-answer instruction, but API/server execution itself was confirmed.

## Main Runtime

現在の主候補は、停止済み Docker コンテナ `qwq_tp2_srv`。

| Item | Value |
|---|---|
| Container | `qwq_tp2_srv` |
| Image | `nvcr.io/nvidia/tensorrt-llm/release:1.1.0rc5` |
| Runtime | `trtllm-serve` |
| Backend | `trt` |
| Model engine | `/storage/engines/qwq32b_tp2_fp16_8k_b8` |
| Tokenizer | `/storage/engine/qwen/QwQ-32B-AWQ` |
| Tensor parallel | `--tp_size 2` |
| GPU visibility | `CUDA_VISIBLE_DEVICES=0,1` |
| Host/port | `0.0.0.0:8001` |
| API path | `/v1/chat/completions` |
| Max batch size | `8` |
| Max tokens | `8192` |
| Max sequence length | `8192` |
| Network mode | `host` |
| IPC mode | `host` |
| Shared memory | `8 GiB` |
| Bind mount | `/storage:/storage` |

Observed command:

```bash
trtllm-serve serve /storage/engines/qwq32b_tp2_fp16_8k_b8 \
  --backend trt \
  --tokenizer /storage/engine/qwen/QwQ-32B-AWQ \
  --tp_size 2 \
  --host 0.0.0.0 \
  --port 8001 \
  --max_batch_size 8 \
  --max_num_tokens 8192 \
  --max_seq_len 8192 \
  --log_level info
```

The container was created with all GPUs available to Docker, `CUDA_VISIBLE_DEVICES=0,1`, host networking, host IPC, and `/storage` mounted into the container.

## Model Identity

現在実際に使っているモデル本体の正しい表記:

- Hugging Face repo: `Qwen/QwQ-32B-AWQ`
- Local source/tokenizer path: `/storage/engine/qwen/QwQ-32B-AWQ`
- Local TensorRT-LLM engine path: `/storage/engines/qwq32b_tp2_fp16_8k_b8`
- Product/model name: `QwQ-32B-AWQ`
- Base lineage: `Qwen/Qwen2.5-32B` -> `Qwen/QwQ-32B` -> `Qwen/QwQ-32B-AWQ`
- This is the released `QwQ-32B` AWQ quantized model, not `QwQ-32B-Preview`.
- Local HF download metadata revision: `dc9f21221581580ccfa51b74077db6056b56cb69`
- Local metadata timestamp observed on `config.json`: 2025-07-11 14:29:54 JST

Local `config.json` facts:

- `architectures`: `Qwen2ForCausalLM`
- `model_type`: `qwen2`
- `max_position_embeddings`: `40960`
- `torch_dtype`: `float16`
- Quantization config: AWQ, 4-bit, group size 128, zero point enabled
- `transformers_version`: `4.47.1`

Official/local README facts:

- QwQ is the reasoning model in the Qwen series.
- `QwQ-32B-AWQ` is the AWQ 4-bit quantized variant of `QwQ-32B`.
- QwQ is based on Qwen2.5.
- Model size is 32.5B parameters, 31.0B non-embedding parameters.
- Full context length is 131,072 tokens, but prompts over 8,192 tokens require YaRN configuration.

TensorRT-LLM engine facts for the current served engine:

- Built with TensorRT-LLM `1.1.0rc5`
- Engine architecture: `Qwen2ForCausalLM`
- Engine dtype: `float16`
- Engine quantization: `W4A16_GPTQ`
- Tensor parallel size: `2`
- Served context: `max_seq_len=8192`
- Build limit: `max_input_len=1024`, `max_batch_size=8`, `max_num_tokens=8192`

Naming caution:

- `Qwen2ForCausalLM` / `model_type=qwen2` is the implementation architecture used by Qwen2.5-family models in Transformers. It does not mean the product is plain Qwen2.
- `QwQ` is a reasoning/post-trained model in the Qwen series.
- `AWQ` is the downloaded quantized weight format.
- The TensorRT-LLM engine converted that AWQ source into a TensorRT engine whose config labels the runtime quantization as `W4A16_GPTQ`; for day-to-day inventory, treat the source model as `Qwen/QwQ-32B-AWQ` and the deployed engine as `qwq32b_tp2_fp16_8k_b8`.

## Existing Containers

| Container | Status at check | Role |
|---|---|---|
| `qwq_tp2_srv` | Running after 2026-04-20 12:56 JST start test | Main TP2 FP16 8k batch-8 server on port 8001 |
| `qwq_srv_tp2` | Exited `1` | Older TP2 FP16 8k batch-4 attempt on port 8001 |
| `qwq_srv_gpu1` | Exited `0` | Single-GPU INT4/GPTQ 8k server on GPU 1, port 8002 |
| `qwq_srv_gpu0` | Exited `137` | Single-GPU INT4/GPTQ 8k server on GPU 0, port 8001 |

## Stored Model and Engine Paths

Relevant paths found under `/storage`:

```text
/storage/engine/qwen/QwQ-32B-AWQ
/storage/engine/qwen/Qwen3-32B-AWQ
/storage/engine/qwen/Qwen3-32B
/storage/engine/qwq-fp8-optimized
/storage/models/qwq
/storage/models/qwen3

/storage/engines/qwq32b_tp2_fp16_8k_b8
/storage/engines/qwq32b_tp2_fp16_8k_b4
/storage/engines/qwq32b_tp2_64k
/storage/engines/qwq32b_tp2_128k
/storage/engines/qwq32b_tp2_int4gptq_8k
/storage/engines/qwq32b_tp1_int4gptq_8k
/storage/engines/qwq32b_tp1_short8k
/storage/engines/qwq32b_tp1_short8k_rc5
/storage/engines/qwen3_32b_tp2_int4_64k
/storage/engines/qwen3_32b_tp1_int4_8k
```

## ESDE Connection Points

ESDE code and docs commonly expect an OpenAI-compatible endpoint:

```text
http://100.107.6.119:8001/v1
```

Important files:

- `language/sensor/molecule_generator_live.py`: default `DEFAULT_LLM_HOST = "http://100.107.6.119:8001/v1"`
- `language/sensor/test_phase8_integration.py`: live integration test expects the same endpoint
- `language/lexicon/mapper_a1.py`: uses `LLM_HOST` env var, defaulting to the same endpoint
- `language/lexicon/auditor_a1.py`: calls `{LLM_HOST}/chat/completions`
- `docs/ESDE language/ESDE_Module_Reference_Lexicon_v2.md`: documents QwQ-32B endpoint as TP2 dual GPU

## Restart Notes

Fast restart of the existing main container:

```bash
docker start qwq_tp2_srv
docker logs -f qwq_tp2_srv
```

After restart, verify:

```bash
curl http://127.0.0.1:8001/v1/models
curl http://100.107.6.119:8001/v1/models
```

If the existing container must be recreated, preserve these runtime assumptions:

- Use `nvcr.io/nvidia/tensorrt-llm/release:1.1.0rc5` unless intentionally upgrading.
- Use `--gpus all`, `--network host`, `--ipc host`, and `--shm-size 8g`.
- Mount `/storage:/storage`.
- Set `CUDA_VISIBLE_DEVICES=0,1` for the TP2 server.
- Serve `/storage/engines/qwq32b_tp2_fp16_8k_b8` with tokenizer `/storage/engine/qwen/QwQ-32B-AWQ`.

Equivalent recreate command:

```bash
docker run -d \
  --name qwq_tp2_srv \
  --gpus all \
  --network host \
  --ipc host \
  --shm-size 8g \
  -e CUDA_VISIBLE_DEVICES=0,1 \
  -v /storage:/storage \
  nvcr.io/nvidia/tensorrt-llm/release:1.1.0rc5 \
  trtllm-serve serve /storage/engines/qwq32b_tp2_fp16_8k_b8 \
    --backend trt \
    --tokenizer /storage/engine/qwen/QwQ-32B-AWQ \
    --tp_size 2 \
    --host 0.0.0.0 \
    --port 8001 \
    --max_batch_size 8 \
    --max_num_tokens 8192 \
    --max_seq_len 8192 \
    --log_level info
```

## Related Project

`/home/takasan/Aruism-AI-Local` contains related Docker and app files, but the visible `docker-compose.yml` is for Neo4j and an app container, not the TensorRT-LLM QwQ server itself.

Important caution: `/home/takasan/Aruism-AI-Local/.env` contains credentials and a Hugging Face token. Do not copy those values into docs or chat logs.
