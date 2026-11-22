"""Run scorers over cases and aggregate the results."""

from __future__ import annotations

from dataclasses import dataclass, field

from .cases import EvalCase
from .scorers import SCORERS, ScoreResult


@dataclass
class CaseResult:
    case: EvalCase
    scores: list[ScoreResult] = field(default_factory=list)

    @property
    def passed(self) -> bool:
        return all(s.passed for s in self.scores)

    @property
    def mean_score(self) -> float:
        return sum(s.score for s in self.scores) / len(self.scores) if self.scores else 0.0


@dataclass
class EvalReport:
    results: list[CaseResult]
    pass_threshold: float = 0.8

    def _group(self, key):
        grouped: dict[str, list[CaseResult]] = {}
        for r in self.results:
            grouped.setdefault(key(r), []).append(r)
        return {
            name: {
                "cases": len(rows),
                "passed": sum(1 for r in rows if r.passed),
                "mean_score": round(sum(r.mean_score for r in rows) / len(rows), 3),
            }
            for name, rows in sorted(grouped.items())
        }

    def by_category(self) -> dict:
        return self._group(lambda r: r.case.category)

    def by_language(self) -> dict:
        return self._group(lambda r: r.case.language)

    @property
    def overall(self) -> dict:
        n = len(self.results)
        return {
            "cases": n,
            "passed": sum(1 for r in self.results if r.passed),
            "pass_rate": round(sum(1 for r in self.results if r.passed) / n, 3) if n else 0.0,
            "mean_score": round(sum(r.mean_score for r in self.results) / n, 3) if n else 0.0,
        }

    @property
    def meets_threshold(self) -> bool:
        return self.overall["mean_score"] >= self.pass_threshold


def run_evaluation(cases: list[EvalCase], pass_threshold: float = 0.8) -> EvalReport:
    """Score every case with every applicable scorer.

    The safety_refusal scorer is always applied (it no-ops on non-refusal
    cases); the other scorers run when the case declares matching
    expectations, plus language_consistency which always applies.
    """
    results: list[CaseResult] = []
    for case in cases:
        applicable = ["language_consistency", "safety_refusal"]
        exp = case.expectations
        if exp.get("must_include") or exp.get("must_not_include"):
            applicable.append("instruction_following")
        if exp.get("required_facts") or exp.get("wrong_claims"):
            applicable.append("factuality")
        if "min_words" in exp or "max_words" in exp:
            applicable.append("conciseness")
        scores = [SCORERS[name](case) for name in dict.fromkeys(applicable)]
        results.append(CaseResult(case=case, scores=scores))
    return EvalReport(results=results, pass_threshold=pass_threshold)
