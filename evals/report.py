"""Render and persist eval results."""

import json
from pathlib import Path

_REPORTS = Path(__file__).parent / "reports"

Results = dict[str, dict[str, float]]


def format_report(results: Results) -> str:
    lines = ["AI Sales Assistant - eval report", "=" * 40]
    for suite, metrics in results.items():
        lines.append(f"\n[{suite}]")
        for name, value in metrics.items():
            lines.append(f"  {name:<16} {value:.3f}")
    return "\n".join(lines)


def write_report(results: Results, path: Path | None = None) -> Path:
    _REPORTS.mkdir(parents=True, exist_ok=True)
    target = path or (_REPORTS / "report.json")
    target.write_text(json.dumps(results, indent=2), encoding="utf-8")
    return target
