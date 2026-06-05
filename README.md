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
hardware: t4-small
license: mit
---

# Museum of Unlived Lives

*Some lives we live. Most we only imagine.*

Enter a counterfactual — a path you did not take. The curator builds a museum exhibit: title, narrative, artifact, and abstract visual style. Each result is saved to your personal gallery.

**Demo:** [huggingface.co/spaces/divmodelhq/museum-of-unlived-lives](https://huggingface.co/spaces/divmodelhq/museum-of-unlived-lives)  
**Code:** [github.com/Rime504/museum-of-unlived-lives](https://github.com/Rime504/museum-of-unlived-lives)

**Model:** [MiniCPM4.1-8B Q4_K_M](https://huggingface.co/openbmb/MiniCPM4.1-8B-GGUF) · llama.cpp · local inference on T4

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
    MODEL["model.py<br/>MiniCPM + grammar"]
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

Custom HTML/CSS frontend on `gr.Server` — no default Gradio UI. Inference runs fully on-device; no external LLM API.

## Repository

```
app.py              gr.Server + /open_room endpoint
frontend/           Custom UI (HTML, CSS, JS)
museum/             Model, prompts, schema, shapes, card, export
requirements.txt
scripts/            Optional: fetch weights, tests
```

Weights (`minicpm-8b-q4_k_m.gguf`, ~4.97 GB) are downloaded on first startup if not bundled. To ship them with the repo: `python scripts/fetch_gguf.py` then push via Git LFS (`.gitattributes` is configured).

## Run locally

```bash
pip install -r requirements.txt
python app.py
```

Open `http://localhost:7860`.

## Space settings

| Variable | Default | Purpose |
|----------|---------|---------|
| `MUSEUM_N_GPU_LAYERS` | `0` | Set `-1` for full GPU offload on T4 |
| `MUSEUM_WARMUP` | `false` | Preload model at startup |
| `MUSEUM_N_CTX` | `4096` | Context window (model supports 64K; 4K keeps T4 fast) |

Hardware: **Nvidia T4 - small**.
