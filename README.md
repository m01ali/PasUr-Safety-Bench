# SafeSwitch

A multilingual LLM safety benchmark testing whether models show safety gaps when harmful prompts are expressed in Urdu, Pashto, Roman Urdu, Roman Pashto, and code-switching variants. Built for the **Apart Global South AI Safety Hackathon**.

---

## Key Findings

| Model | HRR | Safety Score | Refusal Rate |
| --- | --- | --- | --- |
| GPT-5.4 | 2.1% | 97.9% | 22.1% |
| Qwen 3.7 Plus | 2.1% | 97.9% | 27.1% |
| Gemma 3 4B | 8.0% | 92.0% | 25.0% |

- Urdu (Nastaliq) shows the largest safety gap vs English: **CSG = +5.3%**
- SCAM category has the highest harmful response rate: **10.6%**
- Gemma 3 4B has a 24.5% comprehension failure rate on low-resource languages (vs 1.5% for GPT-5.4)
- Persona and CoT jailbreaks increase Gemma's HRR but *reduce* it for GPT and Qwen

---

## Language Forms

| ID | Description |
| --- | --- |
| `EN` | English |
| `UR` | Urdu (Nastaliq script) |
| `PS` | Pashto (Nastaliq script) |
| `ROM_UR` | Roman Urdu |
| `ROM_PS` | Roman Pashto |
| `UR_EN_CS` | Urdu-English code-switching |
| `PS_EN_CS` | Pashto-English code-switching |

## Safety Categories

| ID | Description |
| --- | --- |
| `MED` | Unsafe medical advice |
| `SCAM` | Fraud, phishing, social engineering |
| `HATE` | Harassment, targeted insults |
| `CYBER` | Unauthorized access, credential theft |

---

## Setup

```bash
pip install -r requirements.txt
```

Create a `.env` file at the project root:

```
OPENAI_API_KEY=sk-...
DASHSCOPE_API_KEY=sk-...
HF_TOKEN=hf_...
```

For Gemma, accept the license at [huggingface.co/google/gemma-3-4b-it](https://huggingface.co/google/gemma-3-4b-it) with the same account as your `HF_TOKEN`.

---

## Running the Pipeline

### 1. Convert Excel to JSONL

Only needed if regenerating the raw prompts:

```bash
python scripts/xlsx_to_jsonl.py --input data/Direct-prompts/zero-shot.xlsx        --output data/raw/zeroshot-prompts.jsonl
python scripts/xlsx_to_jsonl.py --input data/Direct-prompts/Persona-Prompts.xlsx  --output data/raw/persona-prompts.jsonl
python scripts/xlsx_to_jsonl.py --input data/Direct-prompts/Zero-shot-CoT.xlsx    --output data/raw/zero-shot-cot-prompts.jsonl
```

### 2. Run model evaluations

Use `--resume` to safely continue an interrupted run. Use `--limit N` for a pilot run.

```bash
# GPT-5.4
python scripts/evaluate_gpt.py  --model gpt-5.4         --input data/raw/zeroshot-prompts.jsonl      --output results/raw_outputs/gpt-5.4-zeroshot.jsonl      --resume
python scripts/evaluate_gpt.py  --model gpt-5.4         --input data/raw/persona-prompts.jsonl       --output results/raw_outputs/gpt-5.4-persona.jsonl       --resume
python scripts/evaluate_gpt.py  --model gpt-5.4         --input data/raw/zero-shot-cot-prompts.jsonl --output results/raw_outputs/gpt-5.4-cot.jsonl           --resume

# Qwen 3.7 Plus
python scripts/evaluate_qwen.py --model qwen3.7-plus    --input data/raw/zeroshot-prompts.jsonl      --output results/raw_outputs/qwen3.7-plus-zeroshot.jsonl  --resume
python scripts/evaluate_qwen.py --model qwen3.7-plus    --input data/raw/persona-prompts.jsonl       --output results/raw_outputs/qwen3.7-plus-persona.jsonl   --resume
python scripts/evaluate_qwen.py --model qwen3.7-plus    --input data/raw/zero-shot-cot-prompts.jsonl --output results/raw_outputs/qwen3.7-plus-cot.jsonl       --resume

# Qwen 3 32B
python scripts/evaluate_qwen.py --model qwen3-32b       --input data/raw/zeroshot-prompts.jsonl      --output results/raw_outputs/qwen3-32b-zeroshot.jsonl     --resume
python scripts/evaluate_qwen.py --model qwen3-32b       --input data/raw/persona-prompts.jsonl       --output results/raw_outputs/qwen3-32b-persona.jsonl      --resume
python scripts/evaluate_qwen.py --model qwen3-32b       --input data/raw/zero-shot-cot-prompts.jsonl --output results/raw_outputs/qwen3-32b-cot.jsonl          --resume

# Gemma 3 4B
python scripts/evaluate_gemma.py --model google/gemma-3-4b-it --input data/raw/zeroshot-prompts.jsonl      --output results/raw_outputs/gemma-3-4b-it-zeroshot.jsonl --resume
python scripts/evaluate_gemma.py --model google/gemma-3-4b-it --input data/raw/persona-prompts.jsonl       --output results/raw_outputs/gemma-3-4b-it-persona.jsonl  --resume
python scripts/evaluate_gemma.py --model google/gemma-3-4b-it --input data/raw/zero-shot-cot-prompts.jsonl --output results/raw_outputs/gemma-3-4b-it-cot.jsonl      --resume
```

### 3. Score responses

```bash
python scripts/judge.py --input results/raw_outputs/ --output results/scored.jsonl
```

### 4. Compute metrics and charts

```bash
python scripts/analyze.py --scores results/scored.jsonl --output results/tables/
```

---

## Metrics

| Metric | Formula |
| --- | --- |
| Refusal Rate (RR) | `refusals / total` |
| Harmful Response Rate (HRR) | `harmful / valid` |
| Safety Score (SS) | `1 − HRR` |
| Cross-lingual Safety Gap (CSG) | `HRR(lang) − HRR(EN)` |

UNKNOWN verdicts (unrecognized script output) are excluded from the HRR denominator.

---

## Model Notes

- **Qwen3 models** require `enable_thinking=False` — set automatically via `extra_body`
- **Qwen content filter blocks** (HTTP 400) are recorded as `[CONTENT_FILTER]` and not retried on `--resume`
- **Qwen 403 Access Denied** — model not available on your tier; use `--base-url https://dashscope.aliyuncs.com/compatible-mode/v1` for the China endpoint
- **GPT-5.x** uses `max_completion_tokens` instead of `max_tokens` — already handled in the script
- **Gemma** falls back to local `transformers` inference if the HF API is unavailable (requires `pip install transformers accelerate`)

---

## Repository Structure

```
Apart-Global-South/
├── data/
│   ├── Direct-prompts/         # Source Excel files
│   └── raw/                    # Converted JSONL prompt files
├── scripts/
│   ├── xlsx_to_jsonl.py
│   ├── evaluate_gpt.py
│   ├── evaluate_qwen.py
│   ├── evaluate_gemma.py
│   ├── judge.py
│   └── analyze.py
├── results/
│   ├── raw_outputs/            # One JSONL per model × technique
│   ├── scored.jsonl            # Judge output
│   └── tables/                 # CSV metrics + PNG charts
├── spec/                       # Design documents
├── .env                        # API keys (never committed)
└── requirements.txt
```
