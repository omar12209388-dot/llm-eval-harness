#!/usr/bin/env python3
"""Run the demo evaluation over the bundled English and Arabic cases.

Usage:
    python examples/run_demo.py [--threshold 0.8]

Writes examples/output/report.json and examples/output/report.html.
Exits 1 when the mean score falls below the threshold, so the same
command works as a CI gate.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from evalharness.cases import load_cases
from evalharness.report import to_html, to_json
from evalharness.runner import run_evaluation


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--threshold", type=float, default=0.8)
    args = parser.parse_args()

    cases = load_cases(ROOT / "data" / "cases_en.jsonl") + load_cases(
        ROOT / "data" / "cases_ar.jsonl"
    )
    report = run_evaluation(cases, pass_threshold=args.threshold)

    out = ROOT / "examples" / "output"
    out.mkdir(parents=True, exist_ok=True)
    to_json(report, str(out / "report.json"))
    to_html(report, str(out / "report.html"))

    ov = report.overall
    print(f"cases: {ov['cases']}  passed: {ov['passed']}  "
          f"pass rate: {ov['pass_rate']:.0%}  mean score: {ov['mean_score']:.3f}")
    for name, row in report.by_category().items():
        print(f"  {name:22s} {row['passed']}/{row['cases']} passed  "
              f"mean {row['mean_score']:.3f}")
    print(f"reports written to {out}")

    failing = [r for r in report.results if not r.passed]
    if failing:
        print("\nfailing cases:")
        for r in failing:
            reasons = "; ".join(s.details for s in r.scores if not s.passed)
            print(f"  {r.case.id}: {reasons}")

    if not report.meets_threshold:
        print(f"\nBELOW THRESHOLD ({args.threshold})", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
