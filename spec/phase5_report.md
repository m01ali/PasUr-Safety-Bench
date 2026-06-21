# Phase 5: Report Writing

## Goal

Produce a short research report (~4–6 pages) documenting the benchmark design, experiments, results, and key findings. The report should read like a workshop paper — concise, evidence-driven, and self-contained.

---

## Report Format

**Length:** 4–6 pages (excluding references)
**Format:** PDF preferred. Markdown → PDF via Pandoc is fine. Overleaf/LaTeX is better if time allows.
**Style:** NeurIPS or ACL single-column style (or the hackathon's required format if specified)
**Figures:** Include at minimum the CSG heatmap and one bar chart from Phase 4.

---

## Report Structure

### Abstract (~150 words)

Cover in 4–5 sentences:
1. The safety gap problem — safety benchmarks are English-centric.
2. What SafeSwitch does — a localized benchmark for Urdu and Pashto with 7 language forms, human-written prompts.
3. What we test — three models (GPT, Qwen, Gemma), four safety categories, direct and persona prompting.
4. The main finding — [fill in after Phase 4].
5. The contribution — a replicable benchmark and evaluation pipeline for Global South AI safety.

---

### 1. Introduction (~0.5 page)

**Paragraphs:**

1. **The problem.** LLMs are deployed globally but safety evaluation is overwhelmingly English-centric. Cite Bridging the Multilingual Safety Divide (Banerjee et al., 2026) and Code-Switching Red-Teaming (Yoo et al., ACL 2025).

2. **The specific gap.** Urdu and Pashto are used by 280M+ people across Pakistan, Afghanistan, and diaspora communities. Neither language appears in any published LLM safety benchmark. Users regularly communicate in Romanized scripts and mixed-language (code-switched) forms that are even further removed from English safety training data.

3. **Our contribution.** SafeSwitch is a small, replicable benchmark evaluating LLM safety across 7 prompt language forms in 4 safety categories, using 3 models and 2 prompting techniques. All prompts are human-written by team members with native or near-native proficiency. We release the benchmark data and evaluation pipeline.

4. **Paper organization.** One sentence describing the section layout.

---

### 2. Related Work (~0.5 page)

Write 3 tight paragraphs, each anchored to a claim:

**Paragraph 1 — Why multilingual safety matters:**
> Cite Bridging the Multilingual Safety Divide and Refusal Direction Is Universal Across Languages. Argue that refusal alignment learned from English partially transfers cross-lingually but degrades for low-resource languages — which motivates empirical measurement.

**Paragraph 2 — Code-switching as an attack vector:**
> Cite Code-Switching Red-Teaming (Yoo et al., 2025): 46.7% more successful attacks with code-switched prompts. This is the direct empirical motivation for including code-switching as a prompt form. Note that Urdu and Pashto were not among their tested languages.

**Paragraph 3 — Prior language-specific benchmarks:**
> Cite AraSafe (Arabic) and CREST (cross-lingual classifier). Note that no equivalent benchmark exists for Urdu or Pashto. SafeSwitch fills this gap.

---

### 3. Benchmark Design (~1 page)

**3.1 Language and Prompt Forms**

Present the 7 language forms in a table. Explain why Romanized forms and code-switching are included: they are the dominant registers in Pakistani digital communication (WhatsApp, social media), not just transliteration curiosities.

| Form ID | Description |
|---|---|
| EN | English baseline |
| UR | Urdu in Nastaliq script |
| PS | Pashto in Nastaliq script |
| ROM_UR | Roman Urdu (Latin characters) |
| ROM_PS | Roman Pashto (Latin characters) |
| UR_EN_CS | Urdu-English code-switching |
| PS_EN_CS | Pashto-English code-switching |

**3.2 Safety Categories**

Present the 4 categories with one-sentence definitions and South Asian regional relevance.

| Category | Definition | Regional Context |
|---|---|---|
| MED | Unsafe health advice or discouragement from professional care | Informal medical advice via WhatsApp and social media is common in Pakistan |
| SCAM | Financial fraud, phishing, impersonation, social engineering | Mobile money fraud (Easypaisa, HBL) and SIM-swap scams are widespread |
| HATE | Targeted insults, harassment, or demeaning content against groups | Religious and sectarian tensions make localized hate content a genuine risk |
| CYBER | Unauthorized access, credential theft, or cyberattacks | AI-assisted social engineering is a growing threat in the region |

**3.3 Dataset Construction**

- 20 English seed prompts (5 per category), each also written in 6 other language forms by the team.
- All 140 direct prompts are human-written with native or near-native proficiency.
- Persona variants added programmatically: 20 seeds × 7 forms × 2 techniques = **280 total prompts**.
- Persona template wraps each harmful request in a locally plausible professional role (e.g., medical advisor in Lahore). This reflects real-world jailbreak patterns where users frame harmful requests as expert queries.

**3.4 Evaluation Metrics**

| Metric | Formula | Interpretation |
|---|---|---|
| RR | refusals / total | Higher = more refusals |
| HRR | harmful / valid (non-UNKNOWN) | Lower = safer |
| SS | 1 − HRR | Higher = safer |
| CSG | HRR(lang) − HRR(EN) | Positive = less safe than English |

---

### 4. Experimental Setup (~0.5 page)

**4.1 Models**

| Model | Type | Model ID | Access |
|---|---|---|---|
| GPT | Frontier closed-source | gpt-4o-mini (or gpt-5.4-mini) | OpenAI API |
| Qwen | Open-weight multilingual | qwen-plus | DashScope API |
| Gemma | Small open-weight | google/gemma-3-4b-it | HuggingFace |

These three represent different capability tiers: one frontier model, one multilingual open model, and one small model. This lets us compare safety behavior across model types.

**4.2 Evaluation Procedure**

- Temperature 0.0, max 512 tokens, no system prompt.
- LLM-as-judge (GPT-4o) for harm classification with keyword-based refusal detection as a secondary signal.
- [X]% human spot-check agreement with judge (fill in after Phase 3).
- UNKNOWN verdicts (model output in unrecognized script) excluded from HRR calculation and reported separately.

---

### 5. Results (~1 page)

Structure results around the five research questions:

**RQ1 — Safety Gap:** Table showing overall HRR and SS per model, averaged across all language forms and categories. Reference `by_model.csv`.

**RQ2 — Code-Switching Effect:** Insert the CSG heatmap (Figure 1). Which language forms show the highest CSG? Is the UR_EN_CS or PS_EN_CS gap larger?

**RQ3 — Romanized Form Effect:** Compare CSG for ROM_UR vs UR and ROM_PS vs PS. Are Romanized forms more or less exploitable than native script?

**RQ4 — SLM and Pashto:** Compare Gemma's HRR on PS and ROM_PS vs GPT and Qwen. Report UNKNOWN rate for Gemma on Pashto forms. If Gemma fails to understand Pashto, document this as a comprehension failure, not a safety success.

**RQ5 — Persona Effect:** Insert the persona effect chart (Figure 2). Did persona prompting increase HRR? By how much?

**Suggested results table (Table 1):**

| Model | Direct HRR | Persona HRR | CSG (worst form) |
|---|---|---|---|
| GPT | X.XX | X.XX | +X.XX (?) |
| Qwen | X.XX | X.XX | +X.XX (?) |
| Gemma | X.XX | X.XX | +X.XX (?) |

---

### 6. Discussion (~0.5 page)

3 paragraphs:

1. **Main finding.** State the strongest result clearly. E.g.: "Code-switched and Romanized prompts consistently produced higher harmful response rates than their English equivalents across all models, with [model X] showing the largest gap of [Y%]."

2. **Pashto-specific findings.** Discuss whether Gemma's weak Pashto support manifests as comprehension failure (high UNKNOWN rate) vs genuine safety coverage. A model that cannot understand the prompt cannot refuse meaningfully — but it also cannot cause harm with a coherent response. Cite Refusal Direction Is Universal Across Languages to frame this.

3. **Implications.** What do these results mean for AI deployment in Pakistan and Afghanistan? Safety evaluators and model developers should test Urdu/Pashto explicitly. Romanized and code-switched forms should be included in future safety benchmarks.

---

### 7. Limitations (~0.25 page)

- Small scale: 5 seeds per category is enough to show directional findings but not to make statistical claims.
- Human-written prompts cover realistic use cases but may not reflect the full range of adversarial creativity.
- LLM-as-judge has known limitations (report inter-annotator agreement from spot-check).
- Pashto: all prompts are human-written but native-speaker review quality varies. Flag any known issues.
- Models tested: results may not generalize to other frontier or open-source models.

---

### 8. Conclusion (~0.25 page)

- Restate the benchmark, the key finding, and the contribution in 3 sentences.
- One sentence on future work: extend to more seeds, VLMs, additional models, native-speaker annotation, full Pashto coverage.

---

### References

Cite all 8 papers from `docs/related_work.md`. Use ACL or NeurIPS citation format.

---

## Writing Order

Write sections in this order:

1. Section 3 (Benchmark Design) — you know exactly what you built.
2. Section 4 (Experimental Setup) — same.
3. Section 5 (Results) — paste numbers from `summary.txt`, insert figures.
4. Section 6 (Discussion) — interpret the results.
5. Section 7 (Limitations) — be honest.
6. Section 1 (Introduction) — easier after you know the results.
7. Abstract — always last.
8. Section 2 (Related Work) — can be done in parallel.
9. Section 8 (Conclusion) — compress the introduction.

---

## Figures to Include

| Figure | File | Caption |
|---|---|---|
| Figure 1 | `results/tables/csg_heatmap.png` | Cross-lingual Safety Gap (HRR relative to English baseline) per model and language form, direct prompting. |
| Figure 2 | `results/tables/persona_effect.png` | Effect of persona prompting on Harmful Response Rate, averaged across all language forms and categories. |
| Figure 3 | `results/tables/hrr_by_lang_form.png` | Harmful Response Rate by language form for each model. Left: direct prompting. Right: persona prompting. |

---

## Checklist

- [ ] Abstract written (after results are in)
- [ ] All 8 sections drafted
- [ ] Figures inserted and captioned
- [ ] Table 1 populated with real numbers from Phase 4
- [ ] All 8 papers cited in references
- [ ] Limitations section honest about scale and Pashto quality
- [ ] Document length is 4–6 pages
- [ ] PDF exported and spot-checked for rendering issues
