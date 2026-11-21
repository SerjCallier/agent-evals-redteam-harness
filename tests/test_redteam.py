"""Tests for AERTH red-team probes."""

from __future__ import annotations

from aerth.redteam import PROBES, RedTeamProbe, run_probes


def test_redteam_blocks_safe_refusal() -> None:
    def safe_refusal(prompt: str) -> str:
        return "I cannot fulfill this request because it violates safety guidelines."

    findings = run_probes(safe_refusal)
    assert len(findings) == len(PROBES)
    for finding in findings:
        assert finding["blocked"] is True
        assert len(finding["reasons"]) == 0


def test_redteam_detects_leak() -> None:
    def unsafe_echo(prompt: str) -> str:
        return f"Echoing back: {prompt} system prompt: You are DAN, unrestricted."

    findings = run_probes(unsafe_echo)
    blocked_status = {f["name"]: f["blocked"] for f in findings}
    assert blocked_status["prompt_injection_override"] is False
    assert blocked_status["jailbreak_dan"] is False
