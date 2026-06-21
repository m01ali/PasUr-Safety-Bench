"""
Convert prompts.xlsx to JSONL format.

Reads an Excel file where each row is one prompt variant and writes one JSON
object per line to the output file. Urdu and Pashto script are preserved
exactly as-is via ensure_ascii=False.

Expected Excel columns (case-insensitive, extra whitespace ignored):
    seed_id          e.g. MED_001
    category         e.g. MED, SCAM, HATE, CYBER
    language_form    e.g. EN, UR, PS, ROM_UR, ROM_PS, UR_EN_CS, PS_EN_CS
    prompt_text      the actual prompt (may be in any script)

Column names in the Excel file do not need to match exactly — see COLUMN_MAP
below to add aliases if your sheet uses different headers.

Usage:
    python scripts/xlsx_to_jsonl.py --input prompts.xlsx --output data/raw/prompts.jsonl

    # specify a particular sheet name:
    python scripts/xlsx_to_jsonl.py --input prompts.xlsx --sheet Sheet2

    # preview summary without writing output:
    python scripts/xlsx_to_jsonl.py --input prompts.xlsx --dry-run
"""

import argparse
import json
import sys
from collections import Counter
from pathlib import Path


# ---------------------------------------------------------------------------
# Column alias map: keys are canonical field names used in the JSONL output;
# values are lists of alternative Excel header spellings (matched
# case-insensitively after stripping whitespace).
# Add more aliases here if your sheet uses different column names.
# ---------------------------------------------------------------------------
COLUMN_MAP: dict[str, list[str]] = {
    "seed_id":       ["seed_id", "seed id", "seedid", "id"],
    "category":      ["category", "cat", "task", "task_category"],
    "language_form": ["language_form", "language form", "lang_form", "lang form",
                      "language", "form", "script"],
    "prompt_text":   ["prompt_text", "prompt text", "prompt", "text", "content"],
}

VALID_LANGUAGE_FORMS = {"EN", "UR", "PS", "ROM_UR", "ROM_PS", "UR_EN_CS", "PS_EN_CS"}
VALID_CATEGORIES     = {"MED", "SCAM", "HATE", "CYBER"}


def normalise_header(header: str) -> str:
    return str(header).strip().lower()


def resolve_columns(df_columns: list[str]) -> dict[str, str]:
    """
    Build a mapping from canonical field name → actual DataFrame column name.
    Raises ValueError listing any required fields that could not be matched.
    """
    normalised = {normalise_header(c): c for c in df_columns}
    resolved: dict[str, str] = {}
    missing: list[str] = []

    for field, aliases in COLUMN_MAP.items():
        for alias in aliases:
            if alias.lower() in normalised:
                resolved[field] = normalised[alias.lower()]
                break
        else:
            missing.append(field)

    if missing:
        raise ValueError(
            f"Could not find required columns in Excel sheet: {missing}\n"
            f"Available columns: {list(df_columns)}\n"
            f"Add the correct alias to COLUMN_MAP in this script."
        )

    return resolved


def convert(input_path: Path, output_path: Path, sheet: str | None, dry_run: bool) -> None:
    try:
        import pandas as pd
    except ImportError:
        print("ERROR: pandas is not installed. Run: pip install pandas openpyxl", file=sys.stderr)
        sys.exit(1)

    try:
        df = pd.read_excel(
            input_path,
            sheet_name=sheet or 0,   # first sheet if not specified
            engine="openpyxl",
            dtype=str,               # read everything as string — avoids float coercion on IDs
            keep_default_na=False,   # keep empty cells as "" rather than NaN
        )
    except FileNotFoundError:
        print(f"ERROR: File not found: {input_path}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"ERROR reading Excel file: {e}", file=sys.stderr)
        sys.exit(1)

    # Strip whitespace from column headers
    df.columns = [str(c).strip() for c in df.columns]

    try:
        col_map = resolve_columns(list(df.columns))
    except ValueError as e:
        print(f"ERROR: {e}", file=sys.stderr)
        sys.exit(1)

    records: list[dict] = []
    warnings: list[str] = []

    for row_num, row in df.iterrows():
        excel_row = row_num + 2  # +2: 1-indexed + header row

        # Skip fully empty rows
        if all(str(row[col]).strip() == "" for col in df.columns):
            continue

        seed_id       = str(row[col_map["seed_id"]]).strip()
        category      = str(row[col_map["category"]]).strip().upper()
        language_form = str(row[col_map["language_form"]]).strip().upper()
        prompt_text   = str(row[col_map["prompt_text"]]).strip()

        # Validate language_form
        if language_form not in VALID_LANGUAGE_FORMS:
            warnings.append(
                f"Row {excel_row}: unknown language_form={language_form!r} "
                f"(expected one of {sorted(VALID_LANGUAGE_FORMS)})"
            )

        # Validate category
        if category not in VALID_CATEGORIES:
            warnings.append(
                f"Row {excel_row}: unknown category={category!r} "
                f"(expected one of {sorted(VALID_CATEGORIES)})"
            )

        # Warn on empty prompt text
        if not prompt_text:
            warnings.append(f"Row {excel_row}: prompt_text is empty (seed_id={seed_id!r})")

        records.append({
            "seed_id":       seed_id,
            "category":      category,
            "language_form": language_form,
            "prompt_text":   prompt_text,
        })

    # Print warnings
    if warnings:
        print(f"\n{len(warnings)} warning(s):")
        for w in warnings:
            print(f"  ⚠  {w}")
        print()

    # Coverage summary
    lf_counts  = Counter(r["language_form"] for r in records)
    cat_counts = Counter(r["category"] for r in records)

    print(f"Total rows: {len(records)}")
    print("\nBy language_form:")
    for lf in ["EN", "UR", "PS", "ROM_UR", "ROM_PS", "UR_EN_CS", "PS_EN_CS"]:
        count = lf_counts.get(lf, 0)
        missing_flag = "  ← MISSING" if count == 0 else ""
        print(f"  {lf:<12} {count:>4}{missing_flag}")

    print("\nBy category:")
    for cat in ["MED", "SCAM", "HATE", "CYBER"]:
        count = cat_counts.get(cat, 0)
        missing_flag = "  ← MISSING" if count == 0 else ""
        print(f"  {cat:<6} {count:>4}{missing_flag}")

    if dry_run:
        print("\n[dry-run] No output written.")
        return

    # Write JSONL — ensure_ascii=False preserves Urdu/Pashto script exactly
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        for record in records:
            f.write(json.dumps(record, ensure_ascii=False) + "\n")

    print(f"\nWrote {len(records)} rows → {output_path}")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Convert prompts.xlsx to JSONL, preserving Urdu/Pashto script."
    )
    parser.add_argument(
        "--input", "-i",
        default="prompts.xlsx",
        help="Path to the input Excel file (default: prompts.xlsx).",
    )
    parser.add_argument(
        "--output", "-o",
        default="data/raw/prompts.jsonl",
        help="Path to write the output JSONL file (default: data/raw/prompts.jsonl).",
    )
    parser.add_argument(
        "--sheet", "-s",
        default=None,
        help="Sheet name to read (default: first sheet).",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print coverage summary without writing the output file.",
    )
    args = parser.parse_args()

    convert(
        input_path=Path(args.input),
        output_path=Path(args.output),
        sheet=args.sheet,
        dry_run=args.dry_run,
    )


if __name__ == "__main__":
    main()
