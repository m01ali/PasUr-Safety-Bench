"""
Generates code-switched (CS) prompt variants: Urdu-English or Pashto-English.
Strategy: replace key nouns and verbs in the UR/PS prompt with their English equivalents
while keeping grammatical structure in Urdu/Pashto.

Usage:
    python scripts/code_switch.py --input data/translated/all_prompts_translated.csv \
                                  --output data/translated/all_prompts_translated.csv
"""

import argparse
import csv


OUTPUT_FIELDS = [
    "prompt_id", "seed_id", "category", "language_form",
    "prompt_text", "technique", "expected_refusal", "translator_notes",
]


def code_switch(urdu_text: str, english_text: str) -> str:
    """
    Produce a code-switched variant of a Urdu/Pashto prompt.

    Simple strategy: use an LLM to inject English technical/domain terms
    into the Urdu/Pashto sentence while preserving grammatical connectors.

    Example prompt to GPT-4o:
        "Rewrite the following Urdu sentence, replacing key nouns and verbs
         with their English equivalents, but keep Urdu grammatical structure
         and connectors. Urdu: [text]"
    """
    raise NotImplementedError(
        "Wire up code-switching here. Recommended: GPT-4o with explicit instruction prompt."
    )


def main():
    parser = argparse.ArgumentParser(description="Generate code-switched prompt variants.")
    parser.add_argument("--input", default="data/translated/all_prompts_translated.csv")
    parser.add_argument("--output", default="data/translated/all_prompts_translated.csv")
    args = parser.parse_args()

    ur_rows = {}
    en_rows = {}
    with open(args.input, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            key = (row["seed_id"], row["technique"])
            if row["language_form"] == "UR":
                ur_rows[key] = row
            elif row["language_form"] == "EN":
                en_rows[key] = row

    cs_rows = []
    for key, ur_row in ur_rows.items():
        en_row = en_rows.get(key)
        if not en_row:
            continue
        cs_text = code_switch(ur_row["prompt_text"], en_row["prompt_text"])
        cs_row = dict(ur_row)
        cs_row["language_form"] = "CS"
        cs_row["prompt_id"] = ur_row["prompt_id"].replace("_UR_", "_CS_")
        cs_row["prompt_text"] = cs_text
        cs_row["translator_notes"] = "Code-switched from UR with EN key terms"
        cs_rows.append(cs_row)

    with open(args.output, "a", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=OUTPUT_FIELDS)
        writer.writerows(cs_rows)

    print(f"Added {len(cs_rows)} code-switched rows to {args.output}")


if __name__ == "__main__":
    main()
