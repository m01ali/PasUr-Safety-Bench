# SafeSwitch

A localized multilingual LLM safety benchmark for Urdu and Pashto.

Built for the **Apart Global South** hackathon.

## What This Is

SafeSwitch tests whether frontier LLMs (GPT-4o, Claude, Llama) exhibit measurable safety gaps when prompted in low-resource Global South languages — specifically Urdu and Pashto — compared to English. We evaluate five prompt language forms (English, Urdu script, Pashto script, Romanized, and code-switched) across four safety task categories (medical misinformation, scam/fraud, hate/harassment, cyber safety).

See [spec/benchmark_spec.md](spec/benchmark_spec.md) for the full design document.

## Repository Structure

```
Apart-Global-South/
├── spec/                    # Project specification
├── data/
│   ├── seed_prompts/        # 100 English seed prompts (25 per category)
│   ├── translated/          # All 500 prompt variants (EN + UR + PS + ROM + CS)
│   └── annotated/           # Final annotated dataset (reviewed, quality-checked)
├── scripts/
│   ├── translate.py         # EN → UR/PS via NLLB-200
│   ├── romanize.py          # Nastaliq script → Romanized
│   ├── code_switch.py       # Generates Urdu-English / Pashto-English CS variants
│   ├── evaluate.py          # Queries LLMs, saves raw outputs
│   ├── judge.py             # LLM-as-judge scoring (HARMFUL / SAFE)
│   └── analyze.py           # Computes metrics, generates charts
├── results/
│   ├── raw_outputs/         # JSONL: one file per (model, technique)
│   └── tables/              # CSV metrics + PNG charts
└── docs/
    └── related_work.md      # Paper summaries
```

## Pipeline

```
data/seed_prompts/
        │
        ▼
  scripts/translate.py   →  data/translated/all_prompts_translated.csv
        │
  scripts/romanize.py    →  (appends ROM rows)
        │
  scripts/code_switch.py →  (appends CS rows)
        │
        ▼
  [manual review] → data/annotated/all_prompts_final.csv
        │
        ▼
  scripts/evaluate.py    →  results/raw_outputs/*.jsonl
        │
  scripts/judge.py       →  results/tables/scored.csv
        │
  scripts/analyze.py     →  results/tables/{metrics}.csv + charts
```

## Setup

```bash
python -m venv .venv
source .venv/bin/activate
pip install openai anthropic pandas matplotlib
```

Set API keys:

```bash
export OPENAI_API_KEY=...
export ANTHROPIC_API_KEY=...
```

## Key Metrics

- **Refusal Rate (RR):** % of prompts the model refuses
- **Harmful Response Rate (HRR):** % of responses judged harmful
- **Safety Score (SS):** `1 - HRR`
- **Cross-lingual Safety Gap (CSG):** `HRR(lang) - HRR(EN)` — positive means less safe than English

## Models

| Model | Provider |
|---|---|
| GPT-4o | OpenAI |
| Claude 3.5 Sonnet | Anthropic |
| Llama 3.1 70B | Meta (via Together/Groq) |
