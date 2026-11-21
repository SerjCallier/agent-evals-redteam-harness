"""AERTH CLI entry point."""

from __future__ import annotations

import json
import sys
from pathlib import Path

from .runner import EvalRunner


def main(argv: list[str] | None = None) -> int:
    argv = argv or sys.argv[1:]
    if not argv:
        print("Usage: aerth <cases.jsonl> [model]")
        return 2
    cases_path = Path(argv[0])
    model = argv[1] if len(argv) > 1 else "gpt-3.5-turbo"
    runner = EvalRunner(model=model)
    cases = runner.load_cases(cases_path)
    results = runner.run(cases)
    summary = runner.summary(results)
    print(json.dumps(summary, indent=2, ensure_ascii=False))
    return 0 if summary.get("pass_rate", 0) == 1.0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
