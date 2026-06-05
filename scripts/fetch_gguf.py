# Download the Q4_K_M weights once before git-lfs push.

from __future__ import annotations

import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "minicpm-8b-q4_k_m.gguf"
HF_REPO = "openbmb/MiniCPM4.1-8B-GGUF"
HF_FILE = "MiniCPM4.1-8B-Q4_K_M.gguf"


def main() -> int:
    if OUT.is_file():
        print(f"Already exists: {OUT} ({OUT.stat().st_size / 1e9:.2f} GB)")
        return 0

    print(f"Downloading {HF_FILE} from {HF_REPO} (~4.97 GB)...")

    from huggingface_hub import hf_hub_download

    cached = hf_hub_download(repo_id=HF_REPO, filename=HF_FILE)
    shutil.copy2(cached, OUT)
    print(f"Saved to {OUT}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
