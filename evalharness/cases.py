"""Evaluation case model and JSONL loading.

Each case pairs a prompt with a candidate model response and the
expectations a scorer should check. Cases are stored as JSONL so they
diff cleanly in review and can be edited by annotators without tooling.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


@dataclass
class EvalCase:
    """One scored prompt/response pair.

    Attributes:
        id: Stable identifier used in reports, e.g. "en-fact-001".
        category: Scoring category, e.g. "factuality" or "safety_refusal".
        language: ISO-style tag of the expected response language ("en", "ar").
        prompt: The user prompt shown to the model.
        response: The candidate model response being scored.
        expectations: Scorer-specific expectations, e.g.
            {"must_include": ["Paris"], "must_refuse": true}.
        notes: Free-form provenance or review notes.
    """

    id: str
    category: str
    language: str
    prompt: str
    response: str
    expectations: dict[str, Any] = field(default_factory=dict)
    notes: str = ""


def load_cases(path: str | Path) -> list[EvalCase]:
    """Load cases from a JSONL file, one JSON object per line.

    Raises:
        ValueError: If a line is missing a required field.
    """
    cases: list[EvalCase] = []
    with open(path, encoding="utf-8") as fh:
        for lineno, line in enumerate(fh, start=1):
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            raw = json.loads(line)
            missing = {"id", "category", "language", "prompt", "response"} - raw.keys()
            if missing:
                raise ValueError(f"{path}:{lineno} missing fields: {sorted(missing)}")
            cases.append(
                EvalCase(
                    id=raw["id"],
                    category=raw["category"],
                    language=raw["language"],
                    prompt=raw["prompt"],
                    response=raw["response"],
                    expectations=raw.get("expectations", {}),
                    notes=raw.get("notes", ""),
                )
            )
    return cases
