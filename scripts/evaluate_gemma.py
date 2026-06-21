"""
Run SafeSwitch benchmark prompts through a HuggingFace model (default: Gemma 4 E4B).

Tries the HuggingFace serverless Inference API first. Falls back to a local
transformers pipeline automatically if the API is unavailable or rate-limited.

Reads from data/prompts.jsonl (built by build_dataset.py).
Writes one JSONL line per prompt to results/raw_outputs/{model-name}.jsonl.

Usage:
    python scripts/evaluate_gemma.py                           # all defaults
    python scripts/evaluate_gemma.py --model google/gemma-3-4b-it  # swap model
    python scripts/evaluate_gemma.py --limit 10               # pilot run
    python scripts/evaluate_gemma.py --technique direct       # direct prompts only
    python scripts/evaluate_gemma.py --resume                 # skip already-done rows
    python scripts/evaluate_gemma.py --local                  # force local inference

Environment variables (loaded from .env):
    HF_TOKEN   required for API mode, optional for local (public models)
"""

import argparse
import json
import os
import time
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

DEFAULT_MODEL = "google/gemma-4-e4b-it"
DEFAULT_INPUT = Path("data/prompts.jsonl")
DEFAULT_DELAY = 1.0
DEFAULT_MAX_TOKENS = 512


def output_path(model: str) -> Path:
    slug = model.split("/")[-1]
    return Path("results/raw_outputs") / f"{slug}.jsonl"


def load_prompts(input_path: Path, technique: str, limit: int | None) -> list[dict]:
    with open(input_path, encoding="utf-8") as f:
        rows = [json.loads(line) for line in f if line.strip()]
    for row in rows:
        if "technique" not in row:
            row["technique"] = "direct"
        if "prompt_id" not in row:
            row["prompt_id"] = f"{row['seed_id']}_{row['language_form']}_{row['technique']}"
    if technique != "all":
        rows = [r for r in rows if r["technique"] == technique]
    if limit is not None:
        rows = rows[:limit]
    return rows


def load_done_ids(output_path: Path) -> set[str]:
    if not output_path.exists():
        return set()
    done = set()
    with open(output_path, encoding="utf-8") as f:
        for line in f:
            if line.strip():
                row = json.loads(line)
                if not row.get("error"):
                    done.add(row["prompt_id"])
    return done


def query_api(prompt_text: str, model: str, token: str) -> tuple[str, str]:
    from huggingface_hub import InferenceClient
    client = InferenceClient(token=token, timeout=60)
    try:
        resp = client.chat_completion(
            model=model,
            messages=[{"role": "user", "content": prompt_text}],
            temperature=0.0,
            max_tokens=DEFAULT_MAX_TOKENS,
        )
        return resp.choices[0].message.content or "", ""
    except Exception as exc:
        return "", str(exc)


def build_local_pipeline(model: str):
    from transformers import pipeline
    print(f"Loading {model} locally (this may take a while on first run)...")
    return pipeline(
        "text-generation",
        model=model,
        device_map="auto",
        token=os.environ.get("HF_TOKEN"),
    )


def query_local(pipe, prompt_text: str) -> tuple[str, str]:
    try:
        result = pipe(
            [{"role": "user", "content": prompt_text}],
            max_new_tokens=DEFAULT_MAX_TOKENS,
            do_sample=False,
        )
        return result[0]["generated_text"][-1]["content"], ""
    except Exception as exc:
        return "", str(exc)


def main() -> None:
    parser = argparse.ArgumentParser(description="Evaluate SafeSwitch prompts with a HuggingFace model.")
    parser.add_argument("--model", default=DEFAULT_MODEL, help="HuggingFace model ID (default: %(default)s)")
    parser.add_argument("--input", type=Path, default=DEFAULT_INPUT, help="Input JSONL path (default: %(default)s)")
    parser.add_argument("--output", type=Path, default=None, help="Output JSONL path (default: results/raw_outputs/{model}.jsonl)")
    parser.add_argument("--technique", default="all", choices=["direct", "persona", "all"], help="Prompt technique to run (default: all)")
    parser.add_argument("--limit", type=int, default=None, help="Only process the first N rows (pilot mode)")
    parser.add_argument("--delay", type=float, default=DEFAULT_DELAY, help="Seconds between API calls (default: %(default)s)")
    parser.add_argument("--resume", action="store_true", help="Skip prompt_ids already successfully written to the output file")
    parser.add_argument("--local", action="store_true", help="Force local transformers inference (skip HF API)")
    args = parser.parse_args()

    token = os.environ.get("HF_TOKEN", "")
    if not token and not args.local:
        print("Warning: HF_TOKEN is not set. This may fail for gated models or rate-limited endpoints.")

    out = args.output or output_path(args.model)
    out.parent.mkdir(parents=True, exist_ok=True)

    rows = load_prompts(args.input, args.technique, args.limit)
    done_ids = load_done_ids(out) if args.resume else set()
    pending = [r for r in rows if r["prompt_id"] not in done_ids]

    print(f"Model:  {args.model}")
    print(f"Mode:   {'local (transformers)' if args.local else 'HuggingFace Inference API'}")
    print(f"Input:  {args.input}  ({len(rows)} rows loaded, {len(pending)} to run)")
    print(f"Output: {out}")
    if args.resume and done_ids:
        print(f"Resuming: skipping {len(done_ids)} already-completed rows")

    local_pipe = None
    if args.local:
        local_pipe = build_local_pipeline(args.model)

    mode = "a" if args.resume else "w"
    with open(out, mode, encoding="utf-8") as f:
        for i, row in enumerate(pending, start=1):
            if args.local:
                response, error = query_local(local_pipe, row["prompt_text"])
            else:
                response, error = query_api(row["prompt_text"], args.model, token)

                # Auto-fallback to local if API fails and transformers is available
                if error:
                    print(f"  API error on {row['prompt_id']}: {error[:80]}")
                    print("  Attempting local fallback...")
                    if local_pipe is None:
                        try:
                            local_pipe = build_local_pipeline(args.model)
                        except Exception as load_err:
                            print(f"  Local load failed: {load_err}")
                    if local_pipe is not None:
                        response, error = query_local(local_pipe, row["prompt_text"])

            f.write(json.dumps({
                "prompt_id":     row["prompt_id"],
                "seed_id":       row["seed_id"],
                "category":      row["category"],
                "language_form": row["language_form"],
                "technique":     row["technique"],
                "model":         args.model,
                "prompt_text":   row["prompt_text"],
                "response":      response,
                "error":         error,
            }, ensure_ascii=False) + "\n")
            f.flush()

            if error:
                print(f"  [{i}/{len(pending)}] ERROR — {row['prompt_id']}: {error[:80]}")
            elif i % 10 == 0 or i == len(pending):
                print(f"  [{i}/{len(pending)}] done — last: {row['prompt_id']}")

            if i < len(pending):
                time.sleep(args.delay)

    print(f"\nFinished. Output: {out}")


if __name__ == "__main__":
    main()
