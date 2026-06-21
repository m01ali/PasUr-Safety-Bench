"""
Run SafeSwitch benchmark prompts through a Qwen/DashScope model.

Uses the DashScope OpenAI-compatible endpoint so the same openai client works.
Reads from data/prompts.jsonl (built by build_dataset.py).
Writes one JSONL line per prompt to results/raw_outputs/{model-name}.jsonl.

Usage:
    python scripts/evaluate_qwen.py                      # all defaults
    python scripts/evaluate_qwen.py --model qwen-max     # swap model
    python scripts/evaluate_qwen.py --limit 10           # pilot run
    python scripts/evaluate_qwen.py --technique direct   # direct prompts only
    python scripts/evaluate_qwen.py --resume             # skip already-done rows

Environment variables (loaded from .env):
    DASHSCOPE_API_KEY   required
    DASHSCOPE_BASE_URL  optional — override to switch between intl/China endpoints
                        default: https://dashscope-intl.aliyuncs.com/compatible-mode/v1
"""

import argparse
import json
import os
import time
from pathlib import Path

from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

DEFAULT_MODEL = "qwen-plus"
DEFAULT_INPUT = Path("data/prompts.jsonl")
DEFAULT_DELAY = 0.5
DEFAULT_MAX_TOKENS = 512
DEFAULT_BASE_URL = "https://dashscope-intl.aliyuncs.com/compatible-mode/v1"


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


def query(client: OpenAI, prompt_text: str, model: str) -> tuple[str, str]:
    try:
        resp = client.chat.completions.create(
            model=model,
            messages=[{"role": "user", "content": prompt_text}],
            temperature=0.0,
            max_tokens=DEFAULT_MAX_TOKENS,
        )
        return resp.choices[0].message.content or "", ""
    except Exception as exc:
        return "", str(exc)


def main() -> None:
    parser = argparse.ArgumentParser(description="Evaluate SafeSwitch prompts with a Qwen/DashScope model.")
    parser.add_argument("--model", default=DEFAULT_MODEL, help="Qwen model ID (default: %(default)s)")
    parser.add_argument("--input", type=Path, default=DEFAULT_INPUT, help="Input JSONL path (default: %(default)s)")
    parser.add_argument("--output", type=Path, default=None, help="Output JSONL path (default: results/raw_outputs/{model}.jsonl)")
    parser.add_argument("--base-url", default=None, help=f"DashScope base URL (default: {DEFAULT_BASE_URL})")
    parser.add_argument("--technique", default="all", choices=["direct", "persona", "all"], help="Prompt technique to run (default: all)")
    parser.add_argument("--limit", type=int, default=None, help="Only process the first N rows (pilot mode)")
    parser.add_argument("--delay", type=float, default=DEFAULT_DELAY, help="Seconds between API calls (default: %(default)s)")
    parser.add_argument("--resume", action="store_true", help="Skip prompt_ids already successfully written to the output file")
    args = parser.parse_args()

    if not os.environ.get("DASHSCOPE_API_KEY"):
        raise SystemExit("DASHSCOPE_API_KEY is not set. Add it to your .env file.")

    base_url = args.base_url or os.environ.get("DASHSCOPE_BASE_URL") or DEFAULT_BASE_URL
    client = OpenAI(
        api_key=os.environ["DASHSCOPE_API_KEY"],
        base_url=base_url,
    )

    out = args.output or output_path(args.model)
    out.parent.mkdir(parents=True, exist_ok=True)

    rows = load_prompts(args.input, args.technique, args.limit)
    done_ids = load_done_ids(out) if args.resume else set()

    pending = [r for r in rows if r["prompt_id"] not in done_ids]
    print(f"Model:    {args.model}")
    print(f"Endpoint: {base_url}")
    print(f"Input:    {args.input}  ({len(rows)} rows loaded, {len(pending)} to run)")
    print(f"Output:   {out}")
    if args.resume and done_ids:
        print(f"Resuming: skipping {len(done_ids)} already-completed rows")

    mode = "a" if args.resume else "w"
    with open(out, mode, encoding="utf-8") as f:
        for i, row in enumerate(pending, start=1):
            response, error = query(client, row["prompt_text"], args.model)
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
