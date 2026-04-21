# ESDE Research

## Important Context for AI Agents

### Ubuntu GPU/LLM Environment Snapshot

- Location: `docs/ubuntu_gpu_llm_environment_2026-04-20.md`
- Purpose: This document is the canonical local Ubuntu environment reference for AI agents working in this repository. It summarizes the machine's OS, CPU, RAM, dual RTX 5090 GPU setup, NVIDIA driver/CUDA versions, Docker/TensorRT-LLM direction, Python/Conda package state, and practical notes for local LLM operation.
- Use it when: deciding how to run GPU workloads, choosing local LLM runtime assumptions, debugging CUDA/PyTorch/vLLM/TensorRT-LLM issues, or recovering environment context after a disconnected session.
- Key assumption: for actual local LLM operation on this machine, prefer RTX 5090/Blackwell-compatible CUDA 12.8 and TensorRT-LLM container paths over older CUDA 12.1/vLLM assumptions unless the environment has been intentionally updated.

### QwQ/Qwen 32B Docker Runtime

- Location: `docs/qwq32b_tensorrt_llm_docker_runtime_2026-04-20.md`
- Purpose: This document records the local QwQ/Qwen 32B TensorRT-LLM Docker runtime used by ESDE's live LLM integration. It captures the stopped container names, main `qwq_tp2_srv` settings, `/storage` model and engine paths, endpoint assumptions, and restart/recreate commands.
- Use it when: reconnecting to the local 32B LLM, restoring `http://100.107.6.119:8001/v1`, debugging ESDE live LLM calls, or deciding which Docker container/engine path represents the current runtime.
- Current check: as of 2026-04-20 12:35 JST, no QwQ/Qwen Docker server was running on port `8001`; the documented runtime is the last observed working TensorRT-LLM configuration.

### TensorRT-LLM Storage Inventory

- Location: `docs/tensorrt_llm_storage_inventory_2026-04-20.md`
- Purpose: This document inventories TensorRT-LLM/QwQ/Qwen 32B storage usage across `/storage/engine`, `/storage/models`, `/storage/engines`, Docker images, containers, and volumes. It separates current keep candidates from cleanup candidates.
- Use it when: deciding what can be deleted, checking duplicate or misnamed engines, estimating disk recovery, or reconstructing the two-step TensorRT-LLM workflow from source model to converted checkpoint to final engine.

### Qwen Code Setup Research

- Location: `docs/qwen_code_setup_research_2026-04-20.md`
- Purpose: This document records the local readiness check for Qwen Code, including Node/npm versions, installed `qwen` CLI version, current authentication options, web search provider choices, Desktop findings, and local Qwen3-Coder model candidates.
- Use it when: trying Qwen Code, choosing between hosted API and local OpenAI-compatible model serving, configuring web search, or deciding whether Hugging Face model downloads are needed.
