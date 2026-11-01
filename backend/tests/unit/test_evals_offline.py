import json
import sys
from pathlib import Path

import pytest

ROOT_DIR = Path(__file__).resolve().parent.parent.parent.parent
sys.path.insert(0, str(ROOT_DIR))

from evals.run_evals import run_benchmark


@pytest.mark.asyncio
async def test_offline_eval_benchmark_thresholds(tmp_path):
    cases_path = ROOT_DIR / "evals" / "cases.jsonl"
    results_path = tmp_path / "test_results.json"

    assert cases_path.exists(), "evals/cases.jsonl must exist"

    exit_code = await run_benchmark(cases_path, results_path)
    assert exit_code == 0, "Benchmark run returned non-zero exit code"

    report = json.loads(results_path.read_text(encoding="utf-8"))

    metrics = report["metrics"]
    assert metrics["citation_entailment_precision"] >= 0.90, (
        f"Precision {metrics['citation_entailment_precision']} < 0.90"
    )
    assert metrics["false_support_rate"] <= 0.05, (
        f"False support {metrics['false_support_rate']} > 0.05"
    )
    assert metrics["counterevidence_recall"] >= 0.80, (
        f"Counterevidence recall {metrics['counterevidence_recall']} < 0.80"
    )
    assert metrics["overrun_simulation_passed"] is True, (
        "Injected SLA latency overrun did not cleanly degrade to HTTP 504"
    )
