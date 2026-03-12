---
name: NLP Crime Extraction
description: Advanced NLP patterns for extracting complex location relationships and risk sentiment from news.
---

# NLP Crime Extraction Skill

Methodologies for accurate information extraction from unstructured crime reports in Dhaka.

## 📍 Complex Entity Resolution
When processing news text, distinguish between **Event Location**, **Filing Thana**, and **Mentioned Localities**.
- **Rule**: If a sentence mentions "incident in Mirpur" and "case filed at Pallabi Thana", the primary geographic cluster is `Mirpur`, but the administrative link is `Pallabi`.
- **Normalization**: Always map extracted areas to the canonical `tracked_areas.md` list to prevent name duplication (e.g., "DHAKA University" -> "Dhaka University").
- **Exact Match Logic**: Prefer exact string matches for compound names like "North Uttara" before splitting into "Uttara".

## 🎭 Sentiment & Risk Scoring
Beyond incident counts, evaluate the "Severity Weight" based on text adjectives.
- **Keywords for Boosting**: "brutal", "mass", "armed", "gang", "syndicate".
- **Formula**: `Risk = Base_Weight * Severity_Multiplier`.
- **Multiplier Range**: 1.0 (standard) to 2.5 (extreme severity).

## 🛠️ Groq/LLM Prompting Expert
- Use **JSON-mode** strictly for data extraction.
- **Negative Guardrails**: Explicitly instruct the model to return `null` or empty lists if coordinates or area names are not found, instead of hallucinating.
- **Few-Shot Examples**: Always provide at least 2 examples of Dhaka-specific crime reports to the LLM to improve thana/area accuracy.
