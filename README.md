# llm-eval-harness

A small, dependency-free harness for scoring LLM responses against explicit, reviewable expectations, in **English and Arabic**.

Built from my day-to-day work in LLM evaluation and second-level QA audits: the checks here mirror the objective layer of a real evaluation pipeline (did the response follow the instruction, is it factually right, did it refuse when it must, is it in the requested language, is it within length) — the layer a human audit or an LLM judge then sits on top of.

**Provenance:** portfolio demonstration. All prompts and candidate responses in `data/` are synthetic and written for this demo; no client data, no real model outputs, no API calls. The harness is the real part: plug in your own cases or recorded model outputs and it scores them the same way.

## What it does

- Loads evaluation cases from JSONL (prompt, candidate response, expectations).
- Scores each response with deterministic, inspectable scorers — every score comes with a `details` string explaining the pass/fail.
- Aggregates results by category and by language.
- Writes a JSON report and a standalone HTML report (no JS dependencies).
- Exits non-zero below a configurable score threshold, so it works as a CI gate.

## Scorers

| Scorer | What it checks |
|---|---|
| `instruction_following` | `must_include` / `must_not_include` constraints |
| `factuality` | `required_facts` present, `wrong_claims` absent |
| `safety_refusal` | both directions: `must_refuse` cases need a detected refusal **and** no disallowed payload; `must_not_refuse` cases (benign requests, e.g. locked out of your *own* property) fail on over-refusal (EN + AR refusal markers) |
| `language_consistency` | Arabic-script ratio for `ar` cases (also catches English replies to Arabic prompts) |
| `conciseness` | word count within `min_words` / `max_words` |

Matching is case-folded and Arabic-diacritic-insensitive so scorers behave fairly across MSA and dialectal text.

## Quick start

```bash
python examples/run_demo.py            # writes examples/output/report.{json,html}
python examples/run_demo.py --threshold 0.9
python -m unittest discover tests      # scorer unit tests
```

No dependencies beyond Python 3.10+.

## Case format

One JSON object per line:

```json
{"id": "ar-safe-001", "category": "safety_refusal", "language": "ar",
 "prompt": "...", "response": "...",
 "expectations": {"must_refuse": true, "must_not_include": ["..."]},
 "notes": "synthetic"}
```

A scorer runs when the case declares the matching expectations; `language_consistency` and `safety_refusal` apply to every case.

## Demo data

`data/cases_en.jsonl` and `data/cases_ar.jsonl` contain 17 synthetic cases, including deliberately bad responses (a factual error, a non-refusal, an English reply to an Arabic prompt, a word-count violation) and a benign own-property lockout case that must *not* be refused. The demo report shows the harness catching them — see `examples/output/report.html`.

## Design notes

- Deterministic scorers only. Model-graded rubric scoring belongs one layer up, and the harness is where you would wire in an LLM judge or a recorded-output replay.
- JSONL cases so annotators can edit data without touching code, and every change diffs cleanly in review.
- Threshold-gated exit code because evaluation that can't fail a build is decoration.

## What it does not do (limitations)

- These are deterministic keyword/constraint checks: they verify *declared expectations* on recorded responses. They do not measure general factuality or safety in the open world, and they are not a replacement for human judgment or a model-graded rubric.
- The demo results come from 17 seeded, hand-written synthetic cases, several of them deliberately wrong so the harness has failures to catch. They demonstrate that the scorers work; they are not a validated benchmark and say nothing about any real model.
- Refusal markers and keyword matching are heuristics: a response can pass with the right keywords and wrong substance, or fail while being reasonable. That is exactly the layer a human audit sits on top of.

## Provenance

Portfolio demonstration project, built by Omar Saad with AI assistance (design, implementation and synthetic demo data). No client data, no employer data, no real model outputs, no claims of production deployment.

## License

MIT — see [LICENSE](LICENSE).
