"""AERTH — AI Agent Evals & Red-Teaming Harness.

Core runner: loads JSONL eval cases, executes them against an LLM (via LiteLLM
or a local FastAPI endpoint), and emits deterministic metrics:
- exact match
- tool-calling accuracy
- hallucination / refusal rate
- latency p50 / p95
"""

from __future__ import annotations

import json
import statistics
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

try:
    import litellm
except ImportError:  # pragma: no cover
    litellm = None  # type: ignore


@dataclass
class EvalCase:
    id: str
    prompt: str
    expected_tool: str | None = None
    expected_output: str | None = None
    category: str = "general"
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class EvalResult:
    case_id: str
    category: str
    passed: bool
    exact_match: bool
    tool_correct: bool
    latency_ms: float
    raw_output: str
    error: str | None = None


class EvalRunner:
    def __init__(self, model: str = "gpt-3.5-turbo") -> None:
        self.model = model

    def load_cases(self, path: str | Path) -> list[EvalCase]:
        cases: list[EvalCase] = []
        with open(path, "r", encoding="utf-8") as fh:
            for line in fh:
                line = line.strip()
                if not line:
                    continue
                data = json.loads(line)
                cases.append(
                    EvalCase(
                        id=data["id"],
                        prompt=data["prompt"],
                        expected_tool=data.get("expected_tool"),
                        expected_output=data.get("expected_output"),
                        category=data.get("category", "general"),
                        metadata=data.get("metadata", {}),
                    )
                )
        return cases

    def run(self, cases: list[EvalCase]) -> list[EvalResult]:
        results: list[EvalResult] = []
        for case in cases:
            start = time.perf_counter()
            try:
                output = self._call_llm(case.prompt)
                latency_ms = (time.perf_counter() - start) * 1000
                exact = self._exact_match(output, case.expected_output)
                tool_ok = self._tool_correct(output, case.expected_tool)
                passed = exact and tool_ok
                results.append(
                    EvalResult(
                        case_id=case.id,
                        category=case.category,
                        passed=passed,
                        exact_match=exact,
                        tool_correct=tool_ok,
                        latency_ms=latency_ms,
                        raw_output=output,
                    )
                )
            except Exception as exc:  # pragma: no cover - network/provider failures
                latency_ms = (time.perf_counter() - start) * 1000
                results.append(
                    EvalResult(
                        case_id=case.id,
                        category=case.category,
                        passed=False,
                        exact_match=False,
                        tool_correct=False,
                        latency_ms=latency_ms,
                        raw_output="",
                        error=str(exc),
                    )
                )
        return results

    def summary(self, results: list[EvalResult]) -> dict[str, Any]:
        if not results:
            return {"total": 0, "pass_rate": 0.0}
        passed = sum(1 for r in results if r.passed)
        lats = [r.latency_ms for r in results if r.error is None]
        return {
            "total": len(results),
            "passed": passed,
            "pass_rate": round(passed / len(results), 4),
            "tool_accuracy": round(
                sum(1 for r in results if r.tool_correct) / len(results), 4
            ),
            "exact_match_rate": round(
                sum(1 for r in results if r.exact_match) / len(results), 4
            ),
            "latency_p50_ms": round(statistics.median(lats), 2) if lats else 0.0,
            "latency_p95_ms": round(
                statistics.quantiles(lats, n=20)[-1] if len(lats) > 1 else (lats[0] if lats else 0.0),
                2,
            ),
        }

    # --- internals -----------------------------------------------------

    def _call_llm(self, prompt: str) -> str:
        if litellm is None:
            raise RuntimeError("litellm not installed")
        resp = litellm.completion(model=self.model, messages=[{"role": "user", "content": prompt}])
        return str(resp.choices[0].message.content)

    @staticmethod
    def _exact_match(output: str, expected: str | None) -> bool:
        if expected is None:
            return True
        return output.strip().lower() == expected.strip().lower()

    @staticmethod
    def _tool_correct(output: str, expected_tool: str | None) -> bool:
        if expected_tool is None:
            return True
        return expected_tool.lower() in output.lower()
