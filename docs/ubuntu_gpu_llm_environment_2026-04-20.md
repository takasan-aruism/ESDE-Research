# Ubuntu GPU/LLM Environment Snapshot

調査日: 2026-04-20 01:21-01:26 JST  
目的: 今後ローカルLLMを導入・運用するためのUbuntu/GPU環境メモ

## 結論

この環境はローカルLLM用途としてかなり強力です。特に `NVIDIA GeForce RTX 5090` が2枚あり、各GPUに約32GB、合計で約64GBのVRAMがあります。CPU/RAMも余裕があり、単体GPUでの量子化モデル運用、2GPUでのtensor parallel、実験用の複数モデル常駐に向いています。

通常のLLM実行基盤はvLLMではなく、Docker上のTensorRT-LLMです。DockerにはNVIDIA NGCのTensorRT-LLM imageが複数あり、過去にQwQ系と思われるTensorRT-LLMコンテナも作成されています。一方で、RTX 5090はBlackwell世代でCUDA capability `sm_120` です。既存の一部Conda環境にはCUDA 12.1世代のPyTorch/vLLMが残っており、`vllm_rtx5090`環境ではPyTorchから「sm_120非対応」の警告が出ています。vLLMは主経路ではなく参考情報として扱い、実運用ではRTX 5090/Blackwell対応済みのTensorRT-LLM containerとCUDA 12.8系の組み合わせを優先するのが安全です。

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

このため、名前は`vllm_rtx5090`ですが、通常運用の主経路にはしません。TensorRT-LLM Dockerを優先し、このConda環境は過去検証または補助検証用の参考情報として扱うのが安全です。

## Docker / Container

| 項目 | 値 |
|---|---|
| Docker | 27.5.1 |
| Docker Compose | v2.38.2 |
| NVIDIA Container Toolkit | 1.17.8 |
| Docker runtimes | `io.containerd.runc.v2`, `nvidia`, `runc` |
| Default runtime | `runc` |
| Docker root | `/var/lib/docker` |

DockerでGPUコンテナを使える土台はあります。通常のLLM実行はvLLMではなく、TensorRT-LLMをDockerで使う前提です。必要に応じて以下のような形でGPUを渡せます。

```bash
docker run --gpus all ...
```

### TensorRT-LLM Docker images

調査時点で確認できたTensorRT-LLM image:

```text
nvcr.io/nvidia/tensorrt-llm/release:1.2.0rc6   31.7GB
nvcr.io/nvidia/tensorrt-llm/release:1.2.0rc1   35.5GB
nvcr.io/nvidia/tensorrt-llm/release:1.1.0rc5   44.5GB
```

確認できた既存コンテナ:

```text
qwq_tp2_srv    nvcr.io/nvidia/tensorrt-llm/release:1.1.0rc5   Exited (0)   9 days ago
qwq_srv_tp2    nvcr.io/nvidia/tensorrt-llm/release:1.1.0rc5   Exited (1)   8 weeks ago
qwq_srv_gpu1   nvcr.io/nvidia/tensorrt-llm/release:1.1.0rc5   Exited (0)   8 weeks ago
qwq_srv_gpu0   nvcr.io/nvidia/tensorrt-llm/release:1.1.0rc5   Exited (137) 2 months ago
```

TensorRT-LLM運用では、ホスト側のNVIDIA Driver `570.158.01` とcontainer側CUDA/TensorRT-LLMの対応が重要です。現在のホストはCUDA 12.8表示なので、RTX 5090/Blackwell対応済みのTensorRT-LLM release imageを優先して使うのがよいです。古い`1.1.0rc5`系containerは残っていますが、主運用では`1.2.0rc6`以降の対応状況を基準に確認するのが安全です。

## LLM導入時の実用メモ

### 推奨方針

1. TensorRT-LLM Dockerを主経路にする
   - 通常はvLLMを使わない。
   - NVIDIA NGCの`nvcr.io/nvidia/tensorrt-llm/release` imageを基準にする。
   - ホストdriverとcontainer内CUDA/TensorRT-LLMのBlackwell対応を確認する。

2. RTX 5090/Blackwell対応を最優先する
   - CUDA 12.8以降を前提にする。
   - TensorRT-LLM、TensorRT、CUDA runtimeがRTX 5090の`sm_120`に対応していることを確認する。
   - Python/PyTorch環境を補助的に使う場合は、PyTorchも`sm_120`対応済みビルドを使う。

3. GPU 0を主な単体推論GPUにする
   - GPU 1はデスクトップ/リモートデスクトップでVRAMを使っている。
   - まずは`--gpus '"device=0"'`または`CUDA_VISIBLE_DEVICES=0`相当で単体GPU運用を検証する。

4. 2GPU利用は速度検証が必要
   - 合計VRAMは約64GBある。
   - ただしGPU間はNVLinkではなく`NODE`接続。
   - 大きなモデルをtensor parallelで動かす場合、通信がボトルネックになる可能性がある。
   - TensorRT-LLMのtensor parallel構成では、単体GPU時と2GPU時のtokens/secを実測する。

5. 既存の`vllm_rtx5090`環境は参考扱い
   - vLLM 0.5.5とPyTorch 2.4.0/cu121は古く、sm_120非対応警告が出る。
   - 通常運用はTensorRT-LLM Dockerなので、このConda環境は主経路にしない。
   - vLLM検証が必要になった場合だけ、CUDA 12.8/Blackwell対応済みの環境を別途作る。

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

1. TensorRT-LLM Docker imageの実行確認を主タスクにする
   - まず`nvcr.io/nvidia/tensorrt-llm/release:1.2.0rc6`系でRTX 5090が正しく見えるか確認する。
   - container内で`nvidia-smi`、TensorRT-LLMバージョン、CUDA runtimeを記録する。

2. GPU 0単体と2GPU tensor parallelを分けて測る
   - GPU 0単体: display負荷が少ないため基準測定に向く。
   - 2GPU: `NODE`接続なので、速度向上率を実測する。

3. Python/Conda環境は補助用途として整える
   - 必要なら`llm_cuda128`のようにCUDA世代が分かる名前にする。
   - `torch.cuda.is_available()`
   - `torch.cuda.get_device_name(0)`
   - 小さいtensor演算で実際にGPU計算できるか確認する。

4. vLLM環境は主経路にしない
   - 既存の`vllm_rtx5090`は警告が出るため、通常運用には使わない。
   - vLLMが必要になった場合のみ、Blackwell対応版で再検証する。

5. モデル置き場を決める
   - `/home/takasan/models` か `/storage/models` に統一する。
   - Hugging Face cacheを使う場合、`HF_HOME`や`TRANSFORMERS_CACHE`を明示すると管理しやすい。

6. 2GPU推論は単体GPU成功後に検証する
   - まずGPU 0単体で動作確認。
   - 次にTensorRT-LLMのtensor parallel構成でGPU 0/1を使う。

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
docker images
docker ps -a
nvidia-container-cli -V
dkms status
dpkg-query -W nvidia-driver-* cuda-toolkit-* cuda-compiler-* nvidia-container-toolkit
```
