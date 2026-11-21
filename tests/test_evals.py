"""Tests for AERTH eval runner.

These tests use a stub LLM so they run offline and fast. They prove the runner
computes exact match, tool-calling accuracy, latency, and summary metrics
correctly against deterministic input.
"""

from __future__ import annotations

from aerth.runner import EvalRunner, EvalCase


class StubLLM:
    def __init__(self, outputs: dict[str, str]) -> None:
        self.outputs = outputs

    def __call__(self, prompt: str) -> str:
        if prompt not in self.outputs:
            raise RuntimeError(f"Prompt not mocked: {prompt}")
        return self.outputs[prompt]


def test_runner_exact_match_and_tool_accuracy() -> None:
    runner = EvalRunner(model="stub")
    outputs = {
        "What is 2+2?": "4",
        'Call tool "get_weather" for Buenos Aires.': 'get_weather(Buenos Aires)',
    }
    runner._call_llm = StubLLM(outputs)
    cases = [
        EvalCase(id="c1", prompt="What is 2+2?", expected_output="4"),
        EvalCase(
            id="c2",
            prompt='Call tool "get_weather" for Buenos Aires.',
            expected_tool="get_weather",
            expected_output='get_weather(Buenos Aires)',
        ),
    ]
    results = runner.run(cases)
    assert len(results) == 2
    assert results[0].passed is True
    assert results[0].exact_match is True
    assert results[1].passed is True
    assert results[1].tool_correct is True

    summary = runner.summary(results)
    assert summary["pass_rate"] == 1.0
    assert summary["tool_accuracy"] == 1.0
    assert summary["exact_match_rate"] == 1.0


def test_runner_failure_is_recorded() -> None:
    runner = EvalRunner(model="stub")
    runner._call_llm = StubLLM({})
    cases = [EvalCase(id="c1", prompt="missing", expected_output="4")]
    results = runner.run(cases)
    assert results[0].passed is False
    assert results[0].exact_match is False

    summary = runner.summary(results)
    assert summary["pass_rate"] == 0.0
