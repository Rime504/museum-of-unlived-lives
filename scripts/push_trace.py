from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from museum.trace import TRACE_DATASET, TRACE_FILE


def main() -> int:
    if not TRACE_FILE.is_file():
        print(f"No trace at {TRACE_FILE} — generate exhibits in the app first.")
        return 1

    lines = TRACE_FILE.read_text(encoding="utf-8").strip().splitlines()
    records = [json.loads(line) for line in lines if line.strip()]
    print(f"Found {len(records)} trace entries")

    try:
        from huggingface_hub import HfApi

        api = HfApi()
        repo_id = TRACE_DATASET
        try:
            api.create_repo(repo_id, repo_type="dataset", exist_ok=True)
        except Exception:
            pass

        out_path = ROOT / "trace_export.jsonl"
        out_path.write_text(
            "\n".join(json.dumps(r, ensure_ascii=False) for r in records) + "\n",
            encoding="utf-8",
        )
        api.upload_file(
            path_or_fileobj=str(out_path),
            path_in_repo="trace.jsonl",
            repo_id=repo_id,
            repo_type="dataset",
            commit_message="Update agent trace",
        )
        print(f"Pushed to https://huggingface.co/datasets/{repo_id}")
        return 0
    except Exception as e:
        print(f"Upload failed (set HF_TOKEN): {e}")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
