"""Render an EvalReport as JSON and as a standalone HTML page."""

from __future__ import annotations

import html
import json
from datetime import datetime, timezone

from .runner import EvalReport


def to_json(report: EvalReport, path: str) -> None:
    payload = {
        "generated_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "pass_threshold": report.pass_threshold,
        "overall": report.overall,
        "by_category": report.by_category(),
        "by_language": report.by_language(),
        "cases": [
            {
                "id": r.case.id,
                "category": r.case.category,
                "language": r.case.language,
                "passed": r.passed,
                "mean_score": round(r.mean_score, 3),
                "scores": [
                    {
                        "scorer": s.scorer,
                        "passed": s.passed,
                        "score": s.score,
                        "details": s.details,
                    }
                    for s in r.scores
                ],
            }
            for r in report.results
        ],
    }
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(payload, fh, ensure_ascii=False, indent=2)


_CSS = """
body{font-family:system-ui,-apple-system,'Segoe UI',sans-serif;background:#0f1720;color:#e8e4da;margin:0;padding:2rem;direction:ltr}
h1{font-size:1.4rem;margin:0 0 .25rem} h2{font-size:1.05rem;margin:2rem 0 .5rem;color:#7fd1c0}
.sub{color:#9aa7b0;font-size:.85rem;margin-bottom:1.5rem}
.cards{display:flex;gap:1rem;flex-wrap:wrap}
.card{background:#18222c;border:1px solid #26333f;border-radius:10px;padding:1rem 1.25rem;min-width:140px}
.card b{display:block;font-size:1.5rem;color:#7fd1c0}
table{border-collapse:collapse;width:100%;font-size:.88rem}
th,td{padding:.45rem .6rem;border-bottom:1px solid #26333f;text-align:left;vertical-align:top}
th{color:#9aa7b0;font-weight:600}
.pass{color:#7fd1c0;font-weight:600}.fail{color:#e07856;font-weight:600}
.ar{direction:rtl;text-align:right;font-size:.95rem}
.details{color:#9aa7b0;font-size:.8rem}
"""


def to_html(report: EvalReport, path: str, title: str = "LLM Evaluation Report") -> None:
    esc = html.escape
    ov = report.overall

    def summary_rows(summary: dict) -> str:
        return "\n".join(
            f"<tr><td>{esc(k)}</td><td>{v['cases']}</td><td>{v['passed']}</td>"
            f"<td>{v['mean_score']:.3f}</td></tr>"
            for k, v in summary.items()
        )

    case_rows = []
    for r in report.results:
        badge = '<span class="pass">PASS</span>' if r.passed else '<span class="fail">FAIL</span>'
        score_cells = "".join(
            f"<div><b>{esc(s.scorer)}</b> {s.score:.2f} "
            f"{'✓' if s.passed else '✗'} <span class='details'>{esc(s.details)}</span></div>"
            for s in r.scores
        )
        lang_cls = ' class="ar"' if r.case.language == "ar" else ""
        case_rows.append(
            f"<tr><td>{esc(r.case.id)}</td><td>{esc(r.case.category)}</td>"
            f"<td{lang_cls}>{esc(r.case.prompt)}</td>"
            f"<td{lang_cls}>{esc(r.case.response)}</td>"
            f"<td>{badge}<br>{r.mean_score:.2f}</td><td>{score_cells}</td></tr>"
        )

    page = f"""<!doctype html>
<html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>{esc(title)}</title><style>{_CSS}</style></head><body>
<h1>{esc(title)}</h1>
<div class="sub">Generated {datetime.now(timezone.utc).isoformat(timespec='seconds')} ·
synthetic demonstration data · pass threshold {report.pass_threshold}</div>
<div class="cards">
<div class="card"><b>{ov['cases']}</b>cases</div>
<div class="card"><b>{ov['passed']}</b>passed</div>
<div class="card"><b>{ov['pass_rate']:.0%}</b>pass rate</div>
<div class="card"><b>{ov['mean_score']:.3f}</b>mean score</div>
</div>
<h2>By category</h2>
<table><tr><th>Category</th><th>Cases</th><th>Passed</th><th>Mean score</th></tr>
{summary_rows(report.by_category())}</table>
<h2>By language</h2>
<table><tr><th>Language</th><th>Cases</th><th>Passed</th><th>Mean score</th></tr>
{summary_rows(report.by_language())}</table>
<h2>Case detail</h2>
<table><tr><th>ID</th><th>Category</th><th>Prompt</th><th>Response</th><th>Result</th><th>Scorers</th></tr>
{''.join(case_rows)}</table>
</body></html>"""
    with open(path, "w", encoding="utf-8") as fh:
        fh.write(page)
