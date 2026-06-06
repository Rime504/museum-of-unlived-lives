---
title: Museum of Unlived Lives
emoji: 🏛️
colorFrom: gray
colorTo: purple
sdk: gradio
sdk_version: "6.16.0"
python_version: "3.11"
app_file: app.py
pinned: false
license: mit
---

# Museum of Unlived Lives

*Some lives we live. Most we only imagine.*

Enter a counterfactual — a path you did not take. The curator builds a museum exhibit: title, narrative, artifact, and abstract visual style. Each result is saved to your personal gallery.

**Demo:** [build-small-hackathon/museum-of-unlived-lives](https://huggingface.co/spaces/build-small-hackathon/museum-of-unlived-lives)  
**Code:** [github.com/Rime504/museum-of-unlived-lives](https://github.com/Rime504/museum-of-unlived-lives)

**Model:** [MiniCPM4.1-8B Q4_K_M](https://huggingface.co/openbmb/MiniCPM4.1-8B-GGUF) · llama.cpp · `@spaces.GPU` on ZeroGPU

## Architecture

```mermaid
flowchart LR
  subgraph client["Browser"]
    UI["frontend/<br/>index.html · styles.css · app.js"]
  end

  subgraph server["gr.Server (app.py)"]
    GET["GET /"]
    API["POST /open_room"]
  end

  subgraph museum["museum/"]
    SCHEMA["schema.py<br/>JSON validate"]
    MODEL["model.py<br/>MiniCPM + @spaces.GPU"]
    CARD["card.py + shapes.py<br/>HTML + SVG"]
    EXPORT["export.py<br/>PNG card"]
  end

  UI -->|"@gradio/client"| API
  GET --> UI
  API --> SCHEMA
  SCHEMA --> MODEL
  SCHEMA --> CARD
  API --> EXPORT
  API -->|"card_html + png"| UI
```

Custom HTML/CSS frontend — no default Gradio UI. Inference runs locally via llama.cpp; no external LLM API.

## Deploy on Build Small Hackathon org (ZeroGPU)

1. Create Space under **build-small-hackathon** → SDK **Gradio** → template **Blank**
2. **Settings → Hardware → ZeroGPU** (free with org PRO — 40 min GPU/day)
3. Push this repo:

```bash
git remote add hackathon https://huggingface.co/spaces/build-small-hackathon/museum-of-unlived-lives
git push hackathon main --force
```

4. Optional secrets (Settings → Variables and secrets):

| Secret | Value |
|--------|--------|
| `MUSEUM_N_GPU_LAYERS` | `-1` |
| `HF_TOKEN` | token with read access (faster model download) |

**Do not** disable warmup on ZeroGPU unless debugging — weights download without GPU; only model load uses a short GPU slot.

### Using your $40 credits wisely

| Do | Don't |
|----|--------|
| **ZeroGPU** as Space hardware (free tier + org PRO quota) | Leave **T4** running 24/7 ($0.40/hr ≈ $10/day) |
| Let Space **sleep** when idle (48h default) | Disable warmup unless you know you need to |
| Use credits only if you **exceed 40 min/day** ZeroGPU ($1 / 10 min) | Spin up multiple paid GPU Spaces |
| Bundle GGUF via Git LFS once (optional) | Re-download 5 GB every cold start |

## Repository

```
app.py              gr.Blocks + custom / + /open_room API
frontend/           Custom UI (HTML, CSS, JS)
museum/             Model, prompts, schema, shapes, card, export
requirements.txt
scripts/            Optional: fetch weights, tests
```

Weights (`minicpm-8b-q4_k_m.gguf`, ~4.97 GB) download when the Space **starts**. MiniCPM loads into GPU memory during warmup and again when the page opens (`/preload_curator`). First **Open this room** should then be inference-only (~30–60 s). To bundle in repo: `python scripts/fetch_gguf.py` then push via Git LFS.

## Run locally

**Requirements:** Python 3.10 or 3.11, ~6 GB free disk (model + deps), internet on first run (model download).

Pick the path that matches your machine:

| Path | Best for | Speed |
|------|----------|-------|
| **A — GPU (Linux / Windows + NVIDIA)** | Gaming laptop, Linux workstation, CUDA 12.x | Fast (~30–60 s per exhibit) |
| **B — CPU only** | No GPU, or CUDA install fails | Slow (~3–8 min per exhibit) |
| **C — Mac (Apple Silicon)** | M1 / M2 / M3 / M4 | Fast via Metal |

All paths use the same app — only `llama-cpp-python` install differs. The `spaces` package is optional locally (ZeroGPU decorator becomes a no-op).

### Quick start (every path)

```bash
git clone https://github.com/Rime504/museum-of-unlived-lives.git
cd museum-of-unlived-lives
python -m venv .venv
```

**Linux / macOS:** `source .venv/bin/activate`  
**Windows (PowerShell):** `.venv\Scripts\Activate.ps1`

Then follow **A**, **B**, or **C** below, and run:

```bash
python app.py
```

Open **http://localhost:7860** and try:

> I had taken the job in Tokyo instead of staying home

---

### A — GPU (Linux / Windows + NVIDIA)

Use the repo’s default `requirements.txt` (CUDA 12.4 wheel + pip CUDA runtime for compatibility):

```bash
pip install -r requirements.txt
python app.py
```

**Optional env vars** (defaults are fine):

```bash
export MUSEUM_N_GPU_LAYERS=-1   # full GPU offload (Windows: set MUSEUM_N_GPU_LAYERS=-1)
export MUSEUM_N_CTX=4096
```

**If you see** `libcudart.so.12: cannot open shared object file` on Linux: the repo already ships `nvidia-cuda-runtime-cu12` and preloads libs in `museum/model.py`. Reinstall deps:

```bash
pip install --force-reinstall -r requirements.txt
```

**CUDA version mismatch?** Swap the wheel index in `requirements.txt` — e.g. `cu121`, `cu122`, `cu123`, or `cu125` instead of `cu124` — to match your driver/CUDA install ([llama-cpp-python wheels](https://llama-cpp-python.readthedocs.io/en/latest/)).

---

### B — CPU fallback (no GPU)

Do **not** use the CUDA extra index. Install the CPU wheel and force CPU inference:

```bash
pip install gradio==6.16.0 spaces>=0.43.0 Pillow>=10.3.0 huggingface_hub>=0.24.0
pip install llama-cpp-python==0.3.23
```

**Linux / macOS:**

```bash
export MUSEUM_N_GPU_LAYERS=0
python app.py
```

**Windows (PowerShell):**

```powershell
$env:MUSEUM_N_GPU_LAYERS="0"
python app.py
```

Expect **3–8 minutes** per exhibit on a typical laptop CPU. It works — just be patient on the first “Open this room” click while the ~5 GB model downloads and loads.

---

### C — Mac (Apple Silicon)

Install Metal-accelerated `llama-cpp-python`, then the rest of the deps:

```bash
pip install gradio==6.16.0 spaces>=0.43.0 Pillow>=10.3.0 huggingface_hub>=0.24.0
CMAKE_ARGS="-DGGML_METAL=on" pip install llama-cpp-python==0.3.23
export MUSEUM_N_GPU_LAYERS=-1
python app.py
```

Metal build uses the GPU via llama.cpp; no NVIDIA/CUDA needed.

---

### Verify it works

1. App starts at `http://localhost:7860` with the custom museum UI (not default Gradio widgets).
2. Enter a counterfactual and click **Open this room**.
3. On **startup**, weights download (~4.97 GB) — logs show `Warmup: weights ready on disk.` then `Warmup complete — curator is ready.` Opening the page also triggers GPU load. Wait ~1–2 min after startup before the first exhibit; later exhibits are faster.
4. You should get an exhibit card: title, narrative, artifact, mood colors, and PNG export.

**Harmless log:** `n_ctx_seq (4096) < n_ctx_train (65536)` — expected; 4K context is intentional and does not limit quality for short exhibits.

**Troubleshooting**

| Symptom | Fix |
|---------|-----|
| `libcudart.so.12` / CUDA load error | Path **A**: reinstall `requirements.txt`. Path **B**: CPU install + `MUSEUM_N_GPU_LAYERS=0`. |
| Import error on Mac | Use Path **C** (Metal), not CUDA `requirements.txt`. |
| Very slow generation | Normal on CPU (Path **B**). Use GPU or Mac Metal for speed. |
| Empty or invalid JSON | Retry once; model occasionally needs a second pass (schema repair handles this). |

## Space settings

| Variable | Default | Purpose |
|----------|---------|---------|
| `MUSEUM_N_GPU_LAYERS` | `-1` | Full GPU offload when CUDA is available |
| `MUSEUM_WARMUP` | `true` | Download + load model at startup (set `false` to defer to first request) |
| `MUSEUM_N_CTX` | `4096` | Context window (4K keeps inference fast) |

Hardware: **ZeroGPU** on the hackathon org Space.
