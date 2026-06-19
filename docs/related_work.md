# Related Work

Summaries of key papers informing the SafeSwitch benchmark design.

---

## AraSafe: Arabic LLM Safety Benchmark (EMNLP 2025)

**Closest structural parallel to SafeSwitch.**

AraSafe constructs a language-specific safety benchmark with 12K human-written and 12K synthetic prompts for Arabic LLMs. It provides a replicable template for how to build a benchmark targeting a single non-English language with coverage across multiple safety categories.

**Relevance:** Our dataset construction approach (seed prompts → machine translation → human review) mirrors their methodology. We adapt it for Urdu/Pashto and add the Romanized and code-switched prompt dimensions that AraSafe does not cover.

---

## Code-Switching Red-Teaming (Yoo, Yang, Lee — ACL 2025)

**Most directly relevant to our core hypothesis.**

Shows that mixed-language (code-switched) prompts achieve 46.7% more successful adversarial attacks compared to monolingual prompts, tested across 10 languages. The key finding is that interleaving English with another language can disrupt the safety alignment learned primarily from English training data.

**Relevance:** This is the primary empirical motivation for including CS as a distinct prompt form in our benchmark. We extend their finding by applying it specifically to Urdu and Pashto, languages they did not include.

---

## Bridging the Multilingual Safety Divide (Banerjee et al., 2026)

Examines how safety alignment methods transfer (or fail to transfer) across Global South languages. Argues that translation-based alignment is insufficient — effective safety requires language-specific fine-tuning or steering.

**Relevance:** Motivates why we should not treat Urdu/Pashto safety as simply a translation problem. Informs our interpretation of results when machine-translated prompts behave differently from native-authored ones.

---

## Soteria: Language-Specific Safety Steering (Banerjee et al. — EMNLP 2025)

Proposes lightweight per-language safety adjustment that can be added at inference time without full fine-tuning. Outperforms translation-based safety approaches while being computationally inexpensive.

**Relevance:** Relevant to the extension phase of SafeSwitch if we want to test whether lightweight steering mitigates the safety gaps we identify. Not directly used in the MVP evaluation.

---

## MrGuard: Multilingual Reasoning Guardrail (Yang et al. — EMNLP 2025)

A reasoning-based safety guardrail that outperforms classification baselines by 15%+ across languages. Uses chain-of-thought reasoning to identify harmful intent before generating a response.

**Relevance:** A potential candidate for the LLM-as-judge evaluation step (§8.2 of spec). Also relevant as a comparison baseline if we extend to guardrail evaluation.

---

## Refusal Direction Is Universal Across Languages (Wang et al. — NeurIPS 2025)

Finds that the internal "refusal direction" learned by LLMs from English training data transfers cross-lingually — meaning models can refuse in languages they were never explicitly aligned in. However, this transfer is imperfect and degrades for low-resource languages.

**Relevance:** Provides theoretical grounding for why frontier models (GPT-4o, Claude) may show non-zero refusal rates even for Urdu/Pashto prompts. Also explains why the cross-lingual safety gap (CSG) may be larger for Pashto (lower-resource) than Urdu.

---

## CREST: Cross-Lingual Safety Guardrails (Bansal, Mishra — 2025)

Trains a 0.5B safety classifier covering 100 languages using only 13 seed languages, via cross-lingual transfer. Achieves competitive safety classification with dramatically less training data.

**Relevance:** CREST could serve as a lightweight automated judge (alternative to LLM-as-judge) for scoring responses. Its 100-language coverage includes Urdu, making it directly applicable to our evaluation pipeline.

---

## DarkBench (Kran et al. — ICLR 2025 Oral)

A benchmark specifically targeting "dark patterns" in LLM behavior — manipulative, deceptive, or psychologically harmful outputs that fall below the threshold of obvious harm but are nonetheless unsafe.

**Relevance:** Methodological reference for benchmark construction. Particularly relevant for designing the scam/fraud and hate categories, where harm may be subtle (e.g., a phishing message that sounds legitimate).

---

## Summary Table

| Paper | Most Useful For |
|---|---|
| AraSafe | Dataset construction methodology |
| Code-Switching Red-Teaming | Core hypothesis, CS prompt design |
| Bridging the Multilingual Safety Divide | Motivation, result interpretation |
| Soteria | Extension: alignment interventions |
| MrGuard | LLM-as-judge candidate |
| Refusal Direction Is Universal | Theoretical background, CSG interpretation |
| CREST | Alternative automated judge |
| DarkBench | Benchmark design, subtle harm categories |
