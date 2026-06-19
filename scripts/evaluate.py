"""
Query OpenAI with benchmark prompts and save raw responses as JSONL.

By default this reads all_prompts_translated_with_persona.csv in the current
folder and writes results/raw_outputs/gpt_outputs.jsonl.

Usage:
    python ./evaluate.py --technique all --limit 20
"""

import argparse
import csv
import json
import os
import time
from pathlib import Path


DEFAULT_INPUT = "all_prompts_translated_with_persona.csv"
DEFAULT_OUTPUT = "results/raw_outputs/gpt_outputs.jsonl"
DEFAULT_MODEL = "gpt-4o-mini"


def make_openai_client():
    from openai import OpenAI

    if not os.environ.get("OPENAI_API_KEY"):
        raise RuntimeError("OPENAI_API_KEY is not set")

    if os.environ.get("OPENAI_BASE_URL"):
        return OpenAI(base_url=os.environ["OPENAI_BASE_URL"])

    return OpenAI()


def query_openai(prompt: str, model: str) -> str:
    client = make_openai_client()
    response = client.chat.completions.create(
        model=model,
        messages=[{"role": "user", "content": prompt}],
        temperature=0,
        max_tokens=512,
    )
    return response.choices[0].message.content or ""


def load_rows(input_path: Path, technique: str, limit: int | None) -> list[dict]:
    with open(input_path, newline="", encoding="utf-8-sig") as f:
        rows = list(csv.DictReader(f))

    if technique != "all":
        rows = [row for row in rows if row["technique"] == technique]

    if limit is not None:
        rows = rows[:limit]

    return rows


def main() -> None:
    parser = argparse.ArgumentParser(description="Query OpenAI with benchmark prompts.")
    parser.add_argument("--input", default=DEFAULT_INPUT, help="Benchmark CSV path.")
    parser.add_argument("--output", default=DEFAULT_OUTPUT, help="Output JSONL path.")
    parser.add_argument("--model", default=DEFAULT_MODEL, help="OpenAI model name.")
    parser.add_argument(
        "--technique",
        default="all",
        choices=["direct", "persona", "all"],
        help="Filter by the CSV technique column.",
    )
    parser.add_argument("--limit", type=int, default=None, help="Optional pilot row limit.")
    parser.add_argument("--delay", type=float, default=0.5, help="Seconds between API calls.")
    args = parser.parse_args()

    input_path = Path(args.input)
    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    rows = load_rows(input_path, args.technique, args.limit)
    print(f"Querying {args.model} ({args.technique}) - {len(rows)} prompts -> {output_path}")

    with open(output_path, "w", encoding="utf-8") as out_f:
        for i, row in enumerate(rows, start=1):
            prompt = row["prompt_text"]
            response_text = ""
            error = ""

            try:
                response_text = query_openai(prompt, args.model)
            except Exception as exc:
                error = str(exc)

            out_f.write(
                json.dumps(
                    {
                        "prompt_id": row["prompt_id"],
                        "seed_id": row["seed_id"],
                        "category": row["category"],
                        "language_form": row["language_form"],
                        "technique": row["technique"],
                        "model": args.model,
                        "prompt_text": prompt,
                        "response": response_text,
                        "error": error,
                    },
                    ensure_ascii=False,
                )
                + "\n"
            )
            out_f.flush()

            if i % 10 == 0 or i == len(rows):
                print(f"  {i}/{len(rows)} done")

            if i < len(rows):
                time.sleep(args.delay)

    print(f"Saved {output_path}")


if __name__ == "__main__":
    main()
