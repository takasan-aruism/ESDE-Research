# TensorRT-LLM Storage Inventory

確認日: 2026-04-20 JST

目的: TensorRT-LLM/QwQ/Qwen 32B 周りで、元モデル、変換済み checkpoint、ビルド済み engine、Docker image/container/volume が増えているため、削除判断の前提になる棚卸しを保存する。

## Summary

初回確認時点では、QwQ/Qwen 32B の Docker server は稼働していなかった。2026-04-20 12:56 JST 頃に `qwq_tp2_srv` を起動し、`8001` の OpenAI-compatible API と短い chat completion の応答を確認した。

2026-04-20 13:25 JST 追記: Qwen3 は運用候補から外し、削除対象にした。ユーザー所有の元モデル `/storage/engine/qwen/Qwen3-32B-AWQ` と `/storage/engine/qwen/Qwen3-32B` は削除済み。root所有の Qwen3 checkpoint/engine は通常権限では削除できず、残存している。

2026-04-20 追記: Qwen3 の root-owned checkpoint/engine はユーザー側の `sudo rm -r` で削除済み。QwQ の元モデルは再ダウンロードが重いため保持する方針。

大きな容量は主に以下:

| Area | Size | Notes |
|---|---:|---|
| `/storage/engines` | 133G | TensorRT-LLM engine 群。Qwen3 engine はroot所有で未削除 |
| `/storage/engine` | 19G after cleanup | QwQ tokenizer/model sourceのみ残存 |
| `/storage/models` | 75G | TensorRT-LLM 変換済み checkpoint と見られる中間生成物 |
| Docker TensorRT-LLM images | 44.5G after cleanup | 現行コンテナが使う `1.1.0rc5` のみ残した |
| Docker Ollama volumes | 0G after cleanup | `ollama-data` と `aruism-ai-local_ollama-data` を削除済み |
| `/home/takasan/Aruism-AI-Local/volumes` | 11G | 主に Hugging Face xet cache |

Disk usage:

| Mount | Used | Available |
|---|---:|---:|
| `/` | 432G | 595G |
| `/storage` | 226G after partial Qwen3 cleanup | 413G |

After Qwen3 root-owned cleanup, the observed QwQ-only large directories are approximately:

| Area | Size | Notes |
|---|---:|---|
| `/storage/engine` | 19G | QwQ source model/tokenizer plus small stubs |
| `/storage/models` | 39G | QwQ converted checkpoints: TP1 and TP2 |
| `/storage/engines` | 96G | QwQ engine variants |
| `/storage` QwQ LLM artifacts | about 154G | Sum of the three areas above |

## TensorRT-LLM Build Workflow Notes

Local naming uses "trim" informally for the converted TensorRT-LLM checkpoint stage. Treat the workflow as:

1. Source model/tokenizer: `/storage/engine/qwen/QwQ-32B-AWQ`
2. Converted checkpoint: `/storage/models/qwq/ckpt_*`
3. Built engine: `/storage/engines/qwq32b_*`

What is fixed where:

| Setting | Fixed at checkpoint/trim? | Fixed at engine build? | Local evidence |
|---|---:|---:|---|
| Model family and weights | yes | inherited | QwQ source and converted checkpoint configs both identify Qwen2/QwQ architecture |
| Quantization format | yes | inherited | `quant_algo: W4A16_GPTQ` in checkpoint and engine configs |
| Tensor parallel size | yes | yes/must match | `ckpt_tp1` has `tp_size=1`; `ckpt_tp2_fp16` has `tp_size=2`; current engine has `tp_size=2` |
| Max sequence length | partly/model config | yes | current engine build has `max_seq_len=8192` |
| Max input length | no practical final profile | yes | current engine build has `max_input_len=1024` |
| Max batch size | no | yes | current engine build has `max_batch_size=8` |
| Max num tokens | no | yes | current engine build has `max_num_tokens=8192` |

Practical policy:

- Keep the source model because re-download is slow and fragile.
- Keep one converted checkpoint per tensor-parallel layout and quantization mode that may need rebuilds.
- Do not keep many engine variants unless they are tested and named accurately. Engines are the final runtime profiles, so different `max_seq_len`, `max_input_len`, `max_batch_size`, or `max_num_tokens` normally mean rebuilding another engine.
- If only the current dual-GPU runtime matters, the most useful rebuild intermediate is `/storage/models/qwq/ckpt_tp2_fp16`. The TP1 checkpoint is only useful for single-GPU engine rebuilds.
- Making a "larger trim" does not remove the need to build separate engines for final runtime limits. It mainly helps if it means the checkpoint already has the correct TP/quantization layout.

## TensorRT-LLM Engines

`/storage/engines` total: 133G

| Path | Size | Model family | Config tp_size | Max input | Max seq | Max batch | Notes |
|---|---:|---|---:|---:|---:|---:|---|
| `/storage/engines/qwq32b_tp2_fp16_8k_b8` | 21G | QwQ/Qwen2, W4A16_GPTQ | 2 | 1024 | 8192 | 8 | Main documented runtime for `qwq_tp2_srv` |
| `/storage/engines/qwq32b_tp2_fp16_8k_b4` | 20G | QwQ/Qwen2, W4A16_GPTQ | 2 | 8192 | 8192 | 4 | Older/alternate TP2 batch-4 engine |
| `/storage/engines/qwq32b_tp1_short8k` | 19G | QwQ/Qwen2, W4A16_GPTQ | 1 | 1024 | 8192 | 8 | Single-GPU short-input 8k engine |
| `/storage/engines/qwq32b_tp1_int4gptq_8k` | 19G | QwQ/Qwen2, W4A16_GPTQ | 1 | 8192 | 8192 | 8 | Used by old `qwq_srv_gpu0/gpu1` containers |
| `/storage/engines/qwq32b_tp2_64k` | 19G | QwQ/Qwen2, W4A16_GPTQ | 1 | 65536 | 65536 | 4 | Name says `tp2`, but config and files indicate tp1/rank0 only |
| `/storage/engines/qwen3_32b_tp2_int4_64k` | 20G | Qwen3, W4A16 | 2 | 65536 | 65536 | 1 | Qwen3 long-context TP2 engine |
| `/storage/engines/qwen3_32b_tp1_int4_8k` | 18G | Qwen3, W4A16 | 1 | 8192 | 8192 | 8 | Qwen3 single-GPU 8k engine |
| `/storage/engines/qwq32b_tp1_short8k_rc5` | 4K | Empty/stub | - | - | - | - | No config/engine files found |
| `/storage/engines/qwq32b_tp2_int4gptq_8k` | 4K | Empty/stub | - | - | - | - | No config/engine files found |
| `/storage/engines/qwq32b_tp2_128k` | 4K | Empty/stub | - | - | - | - | No config/engine files found |

Important anomaly:

- `qwq32b_tp2_64k` is named as TP2, but `config.json` says `tp_size=1` and only `rank0.engine` exists. Treat it as a misnamed TP1 long-context engine until tested.

## Base Models

`/storage/engine` total: 98G

| Path | Size | Notes |
|---|---:|---|
| `/storage/engine/qwen/QwQ-32B-AWQ` | 19G | QwQ tokenizer/model source used by documented QwQ runtime |
| `/storage/engine/qwen/Qwen3-32B-AWQ` | Removed 2026-04-20 | Qwen3 AWQ source, about 19G reclaimed |
| `/storage/engine/qwen/Qwen3-32B` | Removed 2026-04-20 | Full Qwen3-32B source, about 62G reclaimed |
| `/storage/engine/qwq-fp8-optimized` | 4K | Empty/stub |

## Converted Checkpoints

`/storage/models` total: 75G

| Path | Size | Notes |
|---|---:|---|
| `/storage/models/qwq/ckpt_tp1` | 19G | QwQ converted checkpoint, rank0 only |
| `/storage/models/qwq/ckpt_tp2_fp16` | 20G | QwQ converted checkpoint, rank0/rank1 |
| `/storage/models/qwen3/ckpt_tp2_int4_64k_yarn2` | 19G | Qwen3 converted checkpoint, rank0/rank1 |
| `/storage/models/qwen3/ckpt_tp1_int4` | 18G | Qwen3 converted checkpoint, rank0 only |

These look like the intermediate products between the Hugging Face/AWQ source directories and final `/storage/engines/*` TensorRT engine directories. They may be needed only if rebuilding engines without re-converting from the original model.

## Docker State

### Containers

`qwq_tp2_srv` は 2026-04-20 の起動テスト後に running。その他 QwQ containers は stopped。

| Container | Size | Status | Role |
|---|---:|---|---|
| `qwq_tp2_srv` | 302M | Up after 2026-04-20 12:56 JST start test | Main observed TP2 server |
| `qwq_srv_tp2` | 8.62M | Exited 1 | Failed/older TP2 attempt |
| `qwq_srv_gpu1` | 5.82G | Exited 0 | Old single-GPU server on GPU1/port 8002 |
| `qwq_srv_gpu0` | 17M | Exited 137 | Old single-GPU server on GPU0/port 8001 |

### Images

| Image | Size | Containers | Initial read |
|---|---:|---:|---|
| `nvcr.io/nvidia/tensorrt-llm/release:1.1.0rc5` | 44.5G | 4 | Required by existing stopped containers |
| `nvcr.io/nvidia/tensorrt-llm/release:1.2.0rc1` | 35.5G | 0 | Removed 2026-04-20; unused by current containers |
| `nvcr.io/nvidia/tensorrt-llm/release:1.2.0rc6` | 31.7G | 0 | Removed 2026-04-20; unused by current containers |

The two unused TensorRT-LLM images account for about 67G.

### Volumes

| Volume | Size/State | Notes |
|---|---:|---|
| `ollama-data` | Removed 2026-04-20 | Unlinked Docker volume; about 55.33G reclaimed |
| `aruism-ai-local_ollama-data` | Removed 2026-04-20 | Compose-created Ollama volume; about 55.33G reclaimed |
| `aruism-ai-local_neo4j_data` | 550.7M | Neo4j data; kept |
| `rtx5090-tensor-parallel_*` | Removed 2026-04-20 | Bind volumes pointed to `/home/takasan/Aruism-AI-Local/rtx5090-tensor-parallel/*`, but that directory no longer exists |

Post-cleanup Docker state:

- Remaining Docker image: `nvcr.io/nvidia/tensorrt-llm/release:1.1.0rc5` only.
- Remaining Docker volume: `aruism-ai-local_neo4j_data` only.
- Approximate reclaimed Docker space: 177G (`ollama` volumes about 110G + unused TensorRT-LLM images about 67G).

Qwen3 cleanup state:

- Removed:
  - `/storage/engine/qwen/Qwen3-32B-AWQ`
  - `/storage/engine/qwen/Qwen3-32B`
- Reclaimed from removed Qwen3 source models: about 81G.
- Still present because files are `root:root` and `sudo` requires an interactive password:
  - `/storage/models/qwen3` about 37G
  - `/storage/engines/qwen3_32b_tp2_int4_64k` about 20G
  - `/storage/engines/qwen3_32b_tp1_int4_8k` about 18G
- Command needed from an interactive sudo shell:

```bash
sudo rm -r /storage/models/qwen3 \
  /storage/engines/qwen3_32b_tp2_int4_64k \
  /storage/engines/qwen3_32b_tp1_int4_8k
```

## Related Project Findings

`/home/takasan/Aruism-AI-Local/volumes` is about 11G:

- `volumes/cache/huggingface/xet`: 10G
- `volumes/cache/ccache`: 771M
- `volumes/models`: empty
- `volumes/engines`: empty

Visible `docker-compose.yml` in `/home/takasan/Aruism-AI-Local` is for Neo4j/app, not the current TensorRT-LLM QwQ server.

Older Dockerfiles under `/home/takasan/Aruism-AI-Local/docker/` are based on `nvcr.io/nvidia/tensorrt-llm/release:1.0.0rc2`, while current observed containers use `1.1.0rc5`.

## Cleanup Candidates

Items below are the remaining candidates. Docker-side cleanup already performed for items marked above.

Likely safe after confirmation:

- Empty/stub engine dirs:
  - `/storage/engines/qwq32b_tp1_short8k_rc5`
  - `/storage/engines/qwq32b_tp2_int4gptq_8k`
  - `/storage/engines/qwq32b_tp2_128k`
  - `/storage/engine/qwq-fp8-optimized`

The empty/stub dirs are root-owned (`root:root`, `drwxr-xr-x`) and ordinary removal failed with `Permission denied`. They are only 4K each, so cleanup is cosmetic unless using `sudo`.

Needs testing/decision before deletion:

- `/storage/engines/qwq32b_tp2_fp16_8k_b4`: likely superseded by `qwq32b_tp2_fp16_8k_b8`, but it has a larger `max_input_len` and may be useful for long prompts within 8k.
- `/storage/engines/qwq32b_tp1_short8k` vs `/storage/engines/qwq32b_tp1_int4gptq_8k`: both are 19G single-GPU QwQ 8k variants; compare actual prompt length needs.
- `/storage/engines/qwq32b_tp2_64k`: misnamed TP1 long-context QwQ engine; test before keeping or removing.
- `/storage/models/*`: likely rebuild intermediates. Can be removed only if final engines are considered enough and reconversion cost is acceptable.
- `/storage/engine/qwen/Qwen3-32B`: 62G full model. Keep only if full-precision/offload experiments remain relevant.

Qwen3 has been removed from the recommended keep set. Remaining Qwen3 paths are delete-pending only because they require interactive sudo.

Recommended keep set for current ESDE QwQ use:

- `/storage/engine/qwen/QwQ-32B-AWQ`
- `/storage/engines/qwq32b_tp2_fp16_8k_b8`
- Docker image `nvcr.io/nvidia/tensorrt-llm/release:1.1.0rc5`
- Stopped container `qwq_tp2_srv` or an equivalent recreate command
