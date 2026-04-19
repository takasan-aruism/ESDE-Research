# Ubuntu GPU/LLM Environment Snapshot

調査日: 2026-04-20 01:21-01:26 JST  
目的: 今後ローカルLLMを導入・運用するためのUbuntu/GPU環境メモ

## 結論

この環境はローカルLLM用途としてかなり強力です。特に `NVIDIA GeForce RTX 5090` が2枚あり、各GPUに約32GB、合計で約64GBのVRAMがあります。CPU/RAMも余裕があり、単体GPUでの量子化モデル運用、2GPUでのtensor parallel、実験用の複数モデル常駐に向いています。

一方で、RTX 5090はBlackwell世代でCUDA capability `sm_120` です。既存の一部Conda環境にはCUDA 12.1世代のPyTorch/vLLMが残っており、`vllm_rtx5090`環境ではPyTorchから「sm_120非対応」の警告が出ています。LLM実行基盤はCUDA 12.8以降、かつRTX 5090/Blackwell対応済みのPyTorch・vLLM・関連wheelを使う前提で整備するのが安全です。

## OS / Kernel

| 項目 | 値 |
|---|---|
| OS | Ubuntu 24.04.2 LTS |
| Codename | noble |
| Kernel | `6.14.0-37-generic` |
| Architecture | `x86_64` |
| Hostname | `takasan-System-Product-Name` |
| Uptime確認時点 | 6 days, 3 hours |

`uname -a`:

```text
Linux takasan-System-Product-Name 6.14.0-37-generic #37~24.04.1-Ubuntu SMP PREEMPT_DYNAMIC Thu Nov 20 10:25:38 UTC 2 x86_64 x86_64 x86_64 GNU/Linux
```

## CPU / RAM

| 項目 | 値 |
|---|---|
| CPU | AMD Ryzen Threadripper PRO 7965WX 24-Cores |
| 論理CPU | 48 |
| 物理コア | 24 |
| Threads per core | 2 |
| NUMA node | 1 |
| L3 cache | 128 MiB |
| RAM | 503 GiB |
| 調査時点の空きRAM | 約486 GiB free / 約492 GiB available |
| Swap | 8.0 GiB |

LLM用途ではCPU/RAM側の余裕は大きいです。GPUメモリに載らないモデルのオフロード、複数の開発環境、データ前処理を同時に動かしても余裕があります。

## GPU

### 構成

| GPU | Model | Architecture | VRAM total | VRAM free | Bus-Id | Display | Persistence |
|---|---|---:|---:|---:|---|---|---|
| 0 | NVIDIA GeForce RTX 5090 | Blackwell | 32607 MiB | 32103 MiB | `00000000:C1:00.0` | Off | Enabled |
| 1 | NVIDIA GeForce RTX 5090 | Blackwell | 32607 MiB | 31463 MiB | `00000000:E1:00.0` | On | Enabled |

GPU UUID:

```text
GPU 0: GPU-920db009-a2aa-fe3a-b117-bdcbc2e77759
GPU 1: GPU-af2c6e88-5475-4651-7152-be0fcd49b25c
```

### Driver / CUDA

| 項目 | 値 |
|---|---|
| NVIDIA Driver | `570.158.01` |
| nvidia-smi CUDA表示 | `12.8` |
| CUDA Toolkit | `12.8`, nvcc `V12.8.93` |
| CUDA package | `cuda-toolkit-12-8 12.8.1-1` |
| NVIDIA driver package | `nvidia-driver-570-open 570.158.01-0ubuntu1` |
| DKMS | `nvidia/570.158.01` installed for `6.14.0-37-generic` |

`nvcc --version`:

```text
Cuda compilation tools, release 12.8, V12.8.93
```

### 現在のGPU負荷

調査時点ではGPU計算負荷はほぼありません。

| GPU | Util | Temp | Power | Memory used |
|---|---:|---:|---:|---:|
| 0 | 0% | 45-46 C | 約10 W | 18 MiB |
| 1 | 0% | 47-48 C | 約16-23 W | 655 MiB |

GPU 1はXorg / gnome-remote-desktop / gnome-shellで画面用途に使われています。LLM実行時に少しでもVRAMを空けたい場合は、GPU 0を優先的に使うのが扱いやすいです。

例:

```bash
CUDA_VISIBLE_DEVICES=0 python ...
```

### GPU間トポロジ

`nvidia-smi topo -m`:

```text
        GPU0    GPU1    CPU Affinity    NUMA Affinity    GPU NUMA ID
GPU0     X      NODE    0-47            0                N/A
GPU1    NODE     X      0-47            0                N/A
```

2枚のGPU間は `NODE` 接続です。NVLink表示はありません。2GPU tensor parallelは可能ですが、GPU間通信はNVLinkほど速くない前提で見積もるべきです。巨大モデルを2GPUに分割する場合、推論速度はモデルサイズ、batch size、実装の通信量に強く依存します。

### PCIe情報

`nvidia-smi -q`上のリンク情報:

| GPU | Link width | PCIe max | Current at idle | Device max | Host max |
|---|---:|---:|---:|---:|---:|
| 0 | x16 | Gen4 | Gen1 | Gen5 | Gen4 |
| 1 | x16 | Gen4 | Gen1 | Gen5 | Gen4 |

調査時点はアイドル状態なのでCurrentがGen1に落ちています。負荷時には上がる可能性があります。ホスト側はGen4上限です。

## Storage

| Mount | Size | Used | Available | Use% |
|---|---:|---:|---:|---:|
| `/` | 1.1T | 431G | 597G | 42% |
| `/storage` | 672G | 305G | 334G | 48% |

Disk:

```text
nvme0n1  1.8T  CT2000T705SSD5
```

LLMモデル保存先は容量面では `/` でも `/storage` でも可能です。大きめのモデルを複数置くなら、用途ごとに明示的なディレクトリを作るのがよいです。

候補:

```text
/home/takasan/models
/storage/models
```

現状ホーム直下には `/home/takasan/models` が存在します。

## Python / Conda / LLM Packages

### Tool paths

```text
/usr/bin/nvidia-smi
/usr/local/cuda-12.8/bin/nvcc
/home/takasan/miniconda/bin/python3
/home/takasan/miniconda/bin/pip3
/home/takasan/miniconda/bin/conda
```

### Base環境

| 項目 | 値 |
|---|---|
| Python | 3.13.5 |
| pip | 25.2 |
| conda | 25.5.1 |
| torch | `2.9.0.dev20250708+cu128` |
| torch CUDA runtime | `12.8` |
| transformers | `4.53.0` |
| accelerate | `1.8.1` |
| bitsandbytes | `0.45.5` |
| vLLM | not installed |
| llama-cpp-python | not installed |
| xformers | not installed |
| flash-attn | not installed |
| triton | not installed |

Base環境ではPyTorchから2枚のRTX 5090が見えています。

```text
torch 2.9.0.dev20250708+cu128
cuda_available True
cuda_runtime 12.8
device_count 2
0 NVIDIA GeForce RTX 5090 33680064512
1 NVIDIA GeForce RTX 5090 33676918784
```

### Conda environments

```text
base                 * /home/takasan/miniconda
aruism_ai              /home/takasan/miniconda/envs/aruism_ai
vllm_env               /home/takasan/miniconda/envs/vllm_env
vllm_rtx5090           /home/takasan/miniconda/envs/vllm_rtx5090
```

`vllm_env`:

```text
torch: 2.6.0.dev20241112+cu121
vllm: not installed
transformers: 4.53.0
triton: 3.3.0
```

`vllm_rtx5090`:

```text
torch: 2.4.0
vllm: 0.5.5
transformers: 4.53.0
triton: 3.0.0
```

注意: `vllm_rtx5090`では以下の警告が出ました。

```text
NVIDIA GeForce RTX 5090 with CUDA capability sm_120 is not compatible with the current PyTorch installation.
The current PyTorch install supports CUDA capabilities sm_50 sm_60 sm_70 sm_75 sm_80 sm_86 sm_90.
```

このため、名前は`vllm_rtx5090`ですが、現状のまま本格利用するのは避けた方がよいです。RTX 5090対応済みのPyTorch/CUDA/vLLMへ更新するか、新しい専用環境を作り直すのが安全です。

## Docker / Container

| 項目 | 値 |
|---|---|
| Docker | 27.5.1 |
| Docker Compose | v2.38.2 |
| NVIDIA Container Toolkit | 1.17.8 |
| Docker runtimes | `io.containerd.runc.v2`, `nvidia`, `runc` |
| Default runtime | `runc` |
| Docker root | `/var/lib/docker` |

DockerでGPUコンテナを使える土台はあります。必要に応じて以下のような形でGPUを渡せます。

```bash
docker run --gpus all ...
```

## LLM導入時の実用メモ

### 推奨方針

1. RTX 5090/Blackwell対応を最優先する
   - CUDA 12.8以降を前提にする。
   - PyTorchは`sm_120`対応済みビルドを使う。
   - vLLM、FlashAttention、Triton、bitsandbytesはRTX 5090対応状況を確認してから入れる。

2. GPU 0を主な推論GPUにする
   - GPU 1はデスクトップ/リモートデスクトップでVRAMを使っている。
   - まずは`CUDA_VISIBLE_DEVICES=0`で単体GPU運用を検証する。

3. 2GPU利用は速度検証が必要
   - 合計VRAMは約64GBある。
   - ただしGPU間はNVLinkではなく`NODE`接続。
   - 大きなモデルをtensor parallelで動かす場合、通信がボトルネックになる可能性がある。

4. 既存の`vllm_rtx5090`環境は再整備候補
   - vLLM 0.5.5とPyTorch 2.4.0/cu121は古く、sm_120非対応警告が出る。
   - base環境のPyTorch cu128はGPU認識に成功しているため、CUDA 12.8系を基準にした新環境作成がよい。

### モデルサイズの目安

おおまかな目安です。実際の可否はコンテキスト長、KV cache、量子化方式、実行エンジンで変わります。

| モデル規模 | 単体GPU 32GB | 2GPU 合計64GB |
|---|---|---|
| 7B / 8B | FP16/BF16でも現実的 | 余裕あり |
| 14B | 量子化または短めcontextなら現実的 | 余裕あり |
| 30B前後 | 量子化推奨 | 現実的 |
| 70B前後 | 4bit量子化中心 | 2GPU分割で検討可能 |
| 100B超 | 厳しい | 強い量子化/分割/低速前提 |

## 直近の推奨アクション

1. 新しいConda環境を作る
   - 例: `llm_cuda128` のようにCUDA世代が分かる名前にする。

2. PyTorchのGPU認識テストを最初に行う
   - `torch.cuda.is_available()`
   - `torch.cuda.get_device_name(0)`
   - 小さいtensor演算で実際にGPU計算できるか確認する。

3. vLLM導入前にRTX 5090対応を確認する
   - 既存の`vllm_rtx5090`は警告が出るため、更新または作り直し推奨。

4. モデル置き場を決める
   - `/home/takasan/models` か `/storage/models` に統一する。
   - Hugging Face cacheを使う場合、`HF_HOME`や`TRANSFORMERS_CACHE`を明示すると管理しやすい。

5. 2GPU推論は単体GPU成功後に検証する
   - まずGPU 0単体で動作確認。
   - 次に`CUDA_VISIBLE_DEVICES=0,1`でtensor parallelを試す。

## 採取コマンド

主に以下を使用しました。

```bash
nvidia-smi
nvidia-smi -L
nvidia-smi --query-gpu=...
nvidia-smi topo -m
nvidia-smi -q
nvcc --version
lsb_release -a
uname -a
lscpu
free -h
df -h
lsblk -o NAME,SIZE,TYPE,FSTYPE,MOUNTPOINTS,MODEL
conda env list
python3 --version
pip3 --version
python3 -c "import torch; ..."
conda run -n vllm_rtx5090 python -c "import torch; ..."
docker --version
docker info
nvidia-container-cli -V
dkms status
dpkg-query -W nvidia-driver-* cuda-toolkit-* cuda-compiler-* nvidia-container-toolkit
```

