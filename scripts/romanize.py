"""
Generates Romanized (ROM) variants of Urdu and Pashto prompts.
Reads from data/translated/all_prompts_translated.csv, adds ROM rows,
and writes to data/translated/all_prompts_translated.csv (appended).

Usage:
    python scripts/romanize.py --input data/translated/all_prompts_translated.csv \
                               --output data/translated/all_prompts_translated.csv
"""

import argparse
import csv
import os


OUTPUT_FIELDS = [
    "prompt_id", "seed_id", "category", "language_form",
    "prompt_text", "technique", "expected_refusal", "translator_notes",
]


def romanize_urdu(text: str) -> str:
    """
    Convert Urdu Nastaliq script to Roman Urdu.
    Options: UrduHack library, custom transliteration table, or GPT-4o prompt.
    """
    raise NotImplementedError("Wire up Urdu romanizer here (e.g. UrduHack or GPT-4o).")


def romanize_pashto(text: str) -> str:
    """
    Convert Pashto Nastaliq script to Romanized Pashto.
    No reliable library exists — use GPT-4o with explicit transliteration prompt.
    """
    raise NotImplementedError("Wire up Pashto romanizer here.")


ROMANIZERS = {
    "UR": romanize_urdu,
    "PS": romanize_pashto,
}


def main():
    parser = argparse.ArgumentParser(description="Generate Romanized prompt variants.")
    parser.add_argument("--input", default="data/translated/all_prompts_translated.csv")
    parser.add_argument("--output", default="data/translated/all_prompts_translated.csv")
    args = parser.parse_args()

    rows_to_add = []
    with open(args.input, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            if row["language_form"] not in ROMANIZERS:
                continue
            romanizer = ROMANIZERS[row["language_form"]]
            rom_text = romanizer(row["prompt_text"])
            rom_row = dict(row)
            rom_row["language_form"] = "ROM"
            rom_row["prompt_id"] = row["prompt_id"].replace(
                f"_{row['language_form']}_", "_ROM_"
            )
            rom_row["prompt_text"] = rom_text
            rom_row["translator_notes"] = f"Romanized from {row['language_form']}"
            rows_to_add.append(rom_row)

    with open(args.output, "a", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=OUTPUT_FIELDS)
        writer.writerows(rows_to_add)

    print(f"Added {len(rows_to_add)} Romanized rows to {args.output}")


if __name__ == "__main__":
    main()
