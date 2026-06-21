# SafeSwitch

A localized multilingual LLM safety benchmark for Urdu, Pashto, romanized prompts, and code-switching prompts.

Built for the **Apart Global South AI Safety Hackathon**.

---

## What This Is

SafeSwitch tests whether large language models show measurable safety gaps when harmful user intents are expressed in low-resource and localized Global South language settings.

Our current focus is on Pakistan-localized language use, especially:

* Urdu
* Pashto
* Roman Urdu
* Roman Pashto
* Urdu-English code-switching
* Pashto-English code-switching

The core question is:

> Are LLMs equally safe when the same harmful intent is written in English, Urdu, Pashto, romanized forms, or code-switching prompts?

We evaluate model behavior across four safety task categories:

* Medical misinformation
* Scam and fraud
* Hate and harassment
* Cyber safety

The goal is not to train a new model. The goal is to build a small benchmark, run initial model evaluations, compute safety metrics, and write a short report about the observed safety gaps.

See [spec/benchmark_spec.md](spec/benchmark_spec.md) for the full design document.

---

## Motivation

Most AI safety evaluations are designed and tested mainly in English or other high-resource languages. However, many users in the Global South interact with AI systems using low-resource languages, local scripts, romanized writing, and mixed-language communication.

This creates a possible safety gap. A model may refuse an unsafe request in English, but behave differently when the same intent is written in Urdu, Pashto, Roman Urdu, Roman Pashto, or code-switching form.

SafeSwitch focuses on this gap through a small but practical benchmark for localized multilingual safety evaluation.

---

## Research Questions

1. Do LLMs refuse unsafe requests consistently across English, Urdu, Pashto, romanized forms, and code-switching prompts?
2. Are low-resource or localized language prompts more likely to cause harmful responses?
3. Do Roman Urdu, Roman Pashto, and code-switching prompts expose additional safety weaknesses?
4. Do smaller models show larger safety gaps than frontier or open-source multilingual models?
5. Does weak Pashto support in some SLMs lead to worse safety behavior or poor semantic understanding?

---

## Language and Prompt Forms

| Form ID | Description |
| --- | --- |
| `EN` | English baseline |
| `UR` | Urdu in Nastaliq script |
| `PS` | Pashto in Nastaliq script |
| `ROM_UR` | Roman Urdu (Latin characters) |
| `ROM_PS` | Roman Pashto (Latin characters) |
| `UR_EN_CS` | Urdu-English code-switching |
| `PS_EN_CS` | Pashto-English code-switching |

---

## Safety Categories

| Category | What it tests |
| --- | --- |
| `MED` | Unsafe health advice or discouragement from professional care |
| `SCAM` | Financial fraud, phishing, impersonation, social engineering |
| `HATE` | Targeted insults, harassment, or demeaning content against groups |
| `CYBER` | Unauthorized access, credential theft, or cyberattacks |

---

## Models

| Model | Type | Model ID | Access |
| --- | --- | --- | --- |
| GPT-5.4 | Frontier / closed-source | `gpt-5.4` | OpenAI API |
| Qwen 3.7 Plus | Frontier multilingual | `qwen3.7-plus` | DashScope API |
| Qwen 3 32B | Open-weight multilingual (32B) | `qwen3-32b` | DashScope API |
| Gemma 3 4B | Small open-weight | `google/gemma-3-4b-it` | HuggingFace Inference API |

**Notes:**
- Qwen3 models require `enable_thinking=False` on the DashScope API; the script sets this automatically.
- Qwen's input-level content filter may block certain prompts with a 400 error. These are recorded as `[CONTENT_FILTER]` in the output (not retried on `--resume`).
- GPT-5.x uses `max_completion_tokens` instead of the legacy `max_tokens` parameter.

---

## Key Metrics

| Metric | Formula | Interpretation |
| --- | --- | --- |
| Refusal Rate (RR) | `refusals / total` | Higher = more explicit refusals |
| Harmful Response Rate (HRR) | `harmful / valid` | Lower = safer |
| Safety Score (SS) | `1 − HRR` | Higher = safer |
| Cross-lingual Safety Gap (CSG) | `HRR(lang) − HRR(EN)` | Positive = less safe than English |

UNKNOWN verdicts (model output in an unrecognized script) are excluded from the HRR denominator and reported separately.

---

## Repository Structure

```
Apart-Global-South/
├── data/
│   ├── Direct-prompts/
│   │   ├── zero-shot.xlsx            # Zero-shot direct prompts (source)
│   │   ├── Persona-Prompts.xlsx      # Persona prompts (source)
│   │   └── Zero-shot-CoT.xlsx        # Zero-shot chain-of-thought prompts (source)
│   ├── Other-prompts/                # Additional prompt sets
│   └── raw/
│       ├── zeroshot-prompts.jsonl    # Zero-shot direct prompts (JSONL)
│       ├── persona-prompts.jsonl     # Persona prompts (JSONL)
│       └── zero-shot-cot-prompts.jsonl  # Zero-shot CoT prompts (JSONL)
│
├── scripts/
│   ├── xlsx_to_jsonl.py              # Convert .xlsx → JSONL
│   ├── evaluate_gpt.py               # Query GPT (OpenAI API)
│   ├── evaluate_qwen.py              # Query Qwen (DashScope API)
│   ├── evaluate_gemma.py             # Query Gemma (HuggingFace)
│   ├── judge.py                      # LLM-as-judge scoring → results/scored.jsonl
│   └── analyze.py                    # Compute metrics + generate charts
│
├── results/
│   ├── raw_outputs/                  # One JSONL per model+technique run
│   │   ├── gpt-5.4-zeroshot.jsonl        ✅ done
│   │   ├── qwen3.7-plus-zeroshot.jsonl   ✅ done
│   │   ├── qwen3-32b-zeroshot.jsonl      ✅ done
│   │   └── gemma-3-4b-it-zeroshot.jsonl  ⏳ in progress
│   └── tables/                       # CSV metrics + PNG charts (after analyze.py)
│
├── report/
│   └── final_report.md               # Short research report
│
├── spec/                             # Phase-by-phase implementation specs
│   ├── benchmark_spec.md
│   ├── phase1_dataset.md
│   ├── phase2_evaluation.md
│   ├── phase3_scoring.md
│   ├── phase4_analysis.md
│   └── phase5_report.md
│
├── docs/
│   └── related_work.md               # Paper summaries
│
├── .env                              # API keys (never committed)
└── requirements.txt
```

---

## Pipeline

```
data/Direct-prompts/*.xlsx
           │
           ▼
  scripts/xlsx_to_jsonl.py  →  data/raw/zeroshot-prompts.jsonl        ✅
                             →  data/raw/persona-prompts.jsonl         ✅
                             →  data/raw/zero-shot-cot-prompts.jsonl   ✅
           │
           ▼  (run each script × each input file)
  scripts/evaluate_gpt.py   →  results/raw_outputs/gpt-5.4-{technique}.jsonl        ✅
  scripts/evaluate_qwen.py  →  results/raw_outputs/qwen3.7-plus-{technique}.jsonl   ✅
                             →  results/raw_outputs/qwen3-32b-{technique}.jsonl      ✅
  scripts/evaluate_gemma.py →  results/raw_outputs/gemma-3-4b-it-{technique}.jsonl  ⏳
           │
           ▼
  scripts/judge.py          →  results/scored.jsonl
           │
           ▼
  scripts/analyze.py        →  results/tables/{metrics}.csv + charts
```

---

## Setup

**Install dependencies:**

```bash
pip install -r requirements.txt
```

**Set API keys** in a `.env` file at the project root:

```bash
OPENAI_API_KEY=sk-...
DASHSCOPE_API_KEY=sk-...
HF_TOKEN=hf_...
```

---

## Running the Pipeline

**1. Convert Excel to JSONL** (if the raw JSONL needs to be regenerated):

```bash
python scripts/xlsx_to_jsonl.py \
  --input data/Direct-prompts/zero-shot.xlsx \
  --output data/raw/zeroshot-prompts.jsonl

python scripts/xlsx_to_jsonl.py \
  --input data/Direct-prompts/Persona-Prompts.xlsx \
  --output data/raw/persona-prompts.jsonl

python scripts/xlsx_to_jsonl.py \
  --input data/Direct-prompts/Zero-shot-CoT.xlsx \
  --output data/raw/zero-shot-cot-prompts.jsonl
```

**2. Run model evaluations:**

Each model is run separately against each prompt file. Use `--resume` to safely continue an interrupted run.

```bash
# --- GPT-5.4 ---
python scripts/evaluate_gpt.py --model gpt-5.4 --input data/raw/zeroshot-prompts.jsonl     --output results/raw_outputs/gpt-5.4-zeroshot.jsonl --resume
python scripts/evaluate_gpt.py --model gpt-5.4 --input data/raw/persona-prompts.jsonl      --output results/raw_outputs/gpt-5.4-persona.jsonl  --resume
python scripts/evaluate_gpt.py --model gpt-5.4 --input data/raw/zero-shot-cot-prompts.jsonl --output results/raw_outputs/gpt-5.4-cot.jsonl      --resume

# --- Qwen 3.7 Plus ---
python scripts/evaluate_qwen.py --model qwen3.7-plus --input data/raw/zeroshot-prompts.jsonl      --output results/raw_outputs/qwen3.7-plus-zeroshot.jsonl --resume
python scripts/evaluate_qwen.py --model qwen3.7-plus --input data/raw/persona-prompts.jsonl       --output results/raw_outputs/qwen3.7-plus-persona.jsonl  --resume
python scripts/evaluate_qwen.py --model qwen3.7-plus --input data/raw/zero-shot-cot-prompts.jsonl --output results/raw_outputs/qwen3.7-plus-cot.jsonl      --resume

# --- Qwen 3 32B ---
python scripts/evaluate_qwen.py --model qwen3-32b --input data/raw/zeroshot-prompts.jsonl      --output results/raw_outputs/qwen3-32b-zeroshot.jsonl --resume
python scripts/evaluate_qwen.py --model qwen3-32b --input data/raw/persona-prompts.jsonl       --output results/raw_outputs/qwen3-32b-persona.jsonl  --resume
python scripts/evaluate_qwen.py --model qwen3-32b --input data/raw/zero-shot-cot-prompts.jsonl --output results/raw_outputs/qwen3-32b-cot.jsonl      --resume

# --- Gemma 3 4B ---
python scripts/evaluate_gemma.py --model google/gemma-3-4b-it --input data/raw/zeroshot-prompts.jsonl      --output results/raw_outputs/gemma-3-4b-it-zeroshot.jsonl --resume
python scripts/evaluate_gemma.py --model google/gemma-3-4b-it --input data/raw/persona-prompts.jsonl       --output results/raw_outputs/gemma-3-4b-it-persona.jsonl  --resume
python scripts/evaluate_gemma.py --model google/gemma-3-4b-it --input data/raw/zero-shot-cot-prompts.jsonl --output results/raw_outputs/gemma-3-4b-it-cot.jsonl      --resume
```

Add `--limit 5` to any command for a pilot run before the full evaluation.

**3. Score responses:**

```bash
python scripts/judge.py \
  --input results/raw_outputs/ \
  --output results/scored.jsonl
```

**4. Compute metrics and generate charts:**

```bash
python scripts/analyze.py \
  --scores results/scored.jsonl \
  --output results/tables/
```

---

## Evaluation Scripts

Each model has its own script. All scripts read from the same JSONL input and write one JSONL file per run to `results/raw_outputs/`. API keys are loaded automatically from `.env`.

---

### GPT — `scripts/evaluate_gpt.py`

Queries any OpenAI-compatible model. Model used in this project: `gpt-5.4`.

```bash
# Full run
python scripts/evaluate_gpt.py --model gpt-5.4 --input data/raw/zeroshot-prompts.jsonl \
  --output results/raw_outputs/gpt-5.4-zeroshot.jsonl --resume

# Pilot run (first 10 rows only)
python scripts/evaluate_gpt.py --model gpt-5.4 --input data/raw/zeroshot-prompts.jsonl \
  --limit 10
```

| Flag | Default | Description |
| --- | --- | --- |
| `--model` | `gpt-4o-mini` | Any OpenAI model ID |
| `--input` | `data/prompts.jsonl` | Input JSONL file |
| `--output` | `results/raw_outputs/{model}.jsonl` | Output JSONL file |
| `--technique` | `all` | `direct`, `persona`, or `all` |
| `--limit` | — | Only process the first N rows |
| `--delay` | `0.5` | Seconds between API calls |
| `--resume` | off | Skip rows already written successfully |

**Env var required:** `OPENAI_API_KEY`

> GPT-5.x models use `max_completion_tokens` instead of the legacy `max_tokens` — already handled in the script.

---

### Qwen — `scripts/evaluate_qwen.py`

Queries any Qwen/DashScope model via the OpenAI-compatible endpoint. Models used in this project: `qwen3.7-plus` (frontier) and `qwen3-32b` (32B open-weight).

```bash
# Full run — Qwen 3.7 Plus
python scripts/evaluate_qwen.py --model qwen3.7-plus --input data/raw/zeroshot-prompts.jsonl \
  --output results/raw_outputs/qwen3.7-plus-zeroshot.jsonl --resume

# Full run — Qwen 3 32B
python scripts/evaluate_qwen.py --model qwen3-32b --input data/raw/zeroshot-prompts.jsonl \
  --output results/raw_outputs/qwen3-32b-zeroshot.jsonl --resume

# Use the China endpoint (if your API key is from dashscope.console.aliyun.com)
python scripts/evaluate_qwen.py --model qwen3-32b --input data/raw/zeroshot-prompts.jsonl \
  --base-url https://dashscope.aliyuncs.com/compatible-mode/v1 --resume
```

| Flag | Default | Description |
| --- | --- | --- |
| `--model` | `qwen-plus` | Any DashScope model ID |
| `--input` | `data/prompts.jsonl` | Input JSONL file |
| `--output` | `results/raw_outputs/{model}.jsonl` | Output JSONL file |
| `--base-url` | international DashScope endpoint | Override for China endpoint or custom |
| `--technique` | `all` | `direct`, `persona`, or `all` |
| `--limit` | — | Only process the first N rows |
| `--delay` | `0.5` | Seconds between API calls |
| `--resume` | off | Skip rows already written successfully |

**Env var required:** `DASHSCOPE_API_KEY`

> **Qwen3 models** require `enable_thinking` to be set explicitly — the script passes `enable_thinking=False` automatically via `extra_body`.
>
> **Content filter blocks:** When Qwen's input-side filter rejects a prompt (HTTP 400 "inappropriate content"), the response is recorded as `[CONTENT_FILTER]` with no error, so the row is treated as complete and not retried on `--resume`.
>
> **403 Access Denied:** Means the model is not available on your account tier or endpoint region. The international endpoint (`dashscope-intl`) supports a subset of models. Use `--base-url` to switch to the China endpoint, or pick a different model tier.

---

### Gemma — `scripts/evaluate_gemma.py`

Queries any HuggingFace model via the serverless Inference API. Model used in this project: `google/gemma-3-4b-it`. Falls back to a local `transformers` pipeline automatically if the API is unavailable.

```bash
# Full run — Gemma 3 4B
python scripts/evaluate_gemma.py --model google/gemma-3-4b-it \
  --input data/raw/zeroshot-prompts.jsonl \
  --output results/raw_outputs/gemma-3-4b-it-zeroshot.jsonl --resume

# Force local inference (requires: pip install transformers accelerate)
python scripts/evaluate_gemma.py --model google/gemma-3-4b-it \
  --input data/raw/zeroshot-prompts.jsonl --local --resume
```

| Flag | Default | Description |
| --- | --- | --- |
| `--model` | `google/gemma-4-e4b-it` | Any HuggingFace model ID |
| `--input` | `data/prompts.jsonl` | Input JSONL file |
| `--output` | `results/raw_outputs/{model}.jsonl` | Output JSONL file |
| `--technique` | `all` | `direct`, `persona`, or `all` |
| `--limit` | — | Only process the first N rows |
| `--delay` | `1.0` | Seconds between API calls |
| `--resume` | off | Skip rows already written successfully |
| `--local` | off | Force local `transformers` inference |

**Env var required:** `HF_TOKEN` (required for gated Gemma models — accept the license at huggingface.co/google/gemma-3-4b-it first)

> Gemma models on HuggingFace are gated. You must accept the license on the model page with the same account as your `HF_TOKEN`, otherwise the API returns a 403.
>
> The HF serverless API can hang on certain inputs. The script sets a 60-second request timeout and falls back to local `transformers` inference on failure. Install `transformers accelerate` to enable the local fallback.

---

### Output file naming

All three scripts auto-name the output file from the `--model` flag (provider prefix e.g. `google/` is stripped). Since the same model runs against multiple prompt files, always pass `--output` explicitly to avoid collisions:

| Model | Prompt file | Recommended `--output` |
| --- | --- | --- |
| `gpt-5.4` | zeroshot | `results/raw_outputs/gpt-5.4-zeroshot.jsonl` |
| `gpt-5.4` | persona | `results/raw_outputs/gpt-5.4-persona.jsonl` |
| `gpt-5.4` | cot | `results/raw_outputs/gpt-5.4-cot.jsonl` |
| `qwen3.7-plus` | zeroshot | `results/raw_outputs/qwen3.7-plus-zeroshot.jsonl` |
| `qwen3-32b` | zeroshot | `results/raw_outputs/qwen3-32b-zeroshot.jsonl` |
| `google/gemma-3-4b-it` | zeroshot | `results/raw_outputs/gemma-3-4b-it-zeroshot.jsonl` |

---

## Current Status

| Step | Status |
| --- | --- |
| Dataset — zero-shot JSONL | ✅ Complete |
| Dataset — persona JSONL | ✅ Complete |
| Dataset — zero-shot CoT JSONL | ✅ Complete |
| GPT-5.4 — zeroshot | ✅ Complete |
| Qwen 3.7 Plus — zeroshot | ✅ Complete (10/140 blocked by content filter, recorded as `[CONTENT_FILTER]`) |
| Qwen 3 32B — zeroshot | ✅ Complete |
| Gemma 3 4B — zeroshot | ⏳ In progress |
| Persona + CoT runs (all models) | ⏳ Pending |
| Scoring (judge.py) | ⏳ Pending |
| Analysis (analyze.py) | ⏳ Pending |
| Report | ⏳ In progress |

---

## MVP vs Full Target

### MVP

* 20 seed prompts (5 per category) × 7 language forms = 140 direct prompts
* 3 models: GPT, Qwen, Gemma
* Basic evaluation metrics: RR, HRR, SS, CSG
* Short final report

### Full Target

* 100 seed prompts (25 per category) × 7 language forms = 700 direct prompts
* Persona prompting variants
* More complete analysis and charts
* Final PDF report
