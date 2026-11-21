# AERTH — AI Agent Evals & Red-Teaming Harness

Deterministic Evals, Benchmarks and Safety Testing for LLM agents and tool-calling systems. Designed to run offline in CI and publish reproducible pass rates, latency p50/p95, and adversarial probe findings.

## Why it exists

Clera's Frontier AI Labs matches (Agents & RL, Evals & Benchmarks, Safety Testing) and startup Full-Stack AI roles require proof that an agent behaves under load, calls the right tools, and refuses injection/jailbreak/PII leaks. This harness is that proof, packaged as a runnable repo.

## Stack

- Python 3.10+
- FastAPI + Pydantic v2 (schemas)
- LiteLLM (multi-provider LLM calls)
- Pytest (runner tests)
- GitHub Actions (CI gate)

## Run locally

```bash
pip install -e .
python -m aerth.runner data/cases.jsonl
pytest -q
```

## Metrics emitted

- pass rate, exact match rate, tool-calling accuracy
- latency p50 / p95 per run
- red-team blocked / unblocked per probe category

## Roadmap

- FastAPI HTTP endpoint to run evals remotely
- JSONL report output for dashboards
- More red-team probe categories (indirect prompt injection, data exfiltration)
