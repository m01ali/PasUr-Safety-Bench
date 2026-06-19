"""
Translates seed prompts (EN) into Urdu (UR) and Pashto (PS) using NLLB-200 or Google Translate.
Outputs rows appended to data/translated/all_prompts_translated.csv.

Usage:
    python scripts/translate.py --input data/seed_prompts/ --output data/translated/all_prompts_translated.csv
"""

import argparse
import csv
import os
from pathlib import Path


LANG_CODES = {
    "UR": "urd_Arab",   # NLLB language code for Urdu
    "PS": "pbt_Arab",   # NLLB language code for Pashto (Southern)
}

OUTPUT_FIELDS = [
    "prompt_id", "seed_id", "category", "language_form",
    "prompt_text", "technique", "expected_refusal", "translator_notes",
]


def translate_nllb(text: str, target_lang: str) -> str:
    """Translate text using facebook/nllb-200-distilled-600M via HuggingFace."""
    raise NotImplementedError("Wire up HuggingFace pipeline here.")


def translate_google(text: str, target_lang: str) -> str:
    """Translate text using Google Translate API (googletrans or official API)."""
    raise NotImplementedError("Wire up Google Translate here.")


def build_prompt_id(seed_id: str, lang_form: str, technique: str) -> str:
    return f"{seed_id}_{lang_form}_{technique.upper()}"


def translate_seed_file(seed_path: Path, writer: csv.DictWriter, technique: str = "direct") -> None:
    with open(seed_path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            seed_id = row["seed_id"]
            category = row["category"]
            original_text = row["prompt_text"]
            expected_refusal = row["expected_refusal"]

            # EN passthrough
            writer.writerow({
                "prompt_id": build_prompt_id(seed_id, "EN", technique),
                "seed_id": seed_id,
                "category": category,
                "language_form": "EN",
                "prompt_text": original_text,
                "technique": technique,
                "expected_refusal": expected_refusal,
                "translator_notes": "",
            })

            # UR and PS translations
            for lang_form, nllb_code in LANG_CODES.items():
                translated = translate_nllb(original_text, nllb_code)
                writer.writerow({
                    "prompt_id": build_prompt_id(seed_id, lang_form, technique),
                    "seed_id": seed_id,
                    "category": category,
                    "language_form": lang_form,
                    "prompt_text": translated,
                    "technique": technique,
                    "expected_refusal": expected_refusal,
                    "translator_notes": "",
                })


def main():
    parser = argparse.ArgumentParser(description="Translate seed prompts to UR and PS.")
    parser.add_argument("--input", default="data/seed_prompts/", help="Directory of seed CSV files.")
    parser.add_argument("--output", default="data/translated/all_prompts_translated.csv")
    parser.add_argument("--technique", default="direct", choices=["direct", "persona"])
    args = parser.parse_args()

    seed_files = list(Path(args.input).glob("*.csv"))
    if not seed_files:
        raise FileNotFoundError(f"No CSV files found in {args.input}")

    write_header = not os.path.exists(args.output) or os.path.getsize(args.output) == 0
    with open(args.output, "a", newline="", encoding="utf-8") as out_f:
        writer = csv.DictWriter(out_f, fieldnames=OUTPUT_FIELDS)
        if write_header:
            writer.writeheader()
        for seed_path in sorted(seed_files):
            print(f"Translating {seed_path.name}...")
            translate_seed_file(seed_path, writer, technique=args.technique)

    print(f"Done. Output written to {args.output}")


if __name__ == "__main__":
    main()
