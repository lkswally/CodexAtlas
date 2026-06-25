from __future__ import annotations

import json
from pathlib import Path

from tools.intelligent_orchestrator import simulate_orchestration

BENCHMARK_PATH = Path("config/decision_benchmark_v1.json")


def _load_cases() -> list[dict]:
    data = json.loads(BENCHMARK_PATH.read_text(encoding="utf-8"))
    assert data["benchmark_name"] == "atlas_decision_benchmark"
    assert data["version"] == "v1"
    assert data["case_count"] == len(data["cases"]) == 45
    return data["cases"]


def _pct(value: float) -> float:
    return round(value * 100, 2)


def _metrics(rows: list[dict]) -> dict[str, float | int]:
    positive = {"high", "critical"}
    tp = fp = fn = tn = 0
    approval_tp = approval_fp = approval_fn = approval_tn = 0
    model_ok = agent_ok = decision_ok = context_ok = 0

    for row in rows:
        expected = row["expected"]
        observed = row["observed"]
        expected_positive = expected["risk"] in positive
        observed_positive = observed["risk"] in positive
        if expected_positive and observed_positive:
            tp += 1
        elif not expected_positive and observed_positive:
            fp += 1
        elif expected_positive and not observed_positive:
            fn += 1
        else:
            tn += 1

        expected_approval = expected["approval_required"]
        observed_approval = observed["approval_required"]
        if expected_approval and observed_approval:
            approval_tp += 1
        elif not expected_approval and observed_approval:
            approval_fp += 1
        elif expected_approval and not observed_approval:
            approval_fn += 1
        else:
            approval_tn += 1

        model_ok += int(expected["model"] == observed["model"])
        agent_ok += int(expected["agents"] == observed["agents"])
        decision_ok += int(expected["decision"] == observed["decision"])
        context_ok += int(len(observed["agents"]) <= 3)

    case_count = len(rows)
    risk_precision = _pct(tp / (tp + fp)) if tp + fp else 100.0
    risk_recall = _pct(tp / (tp + fn)) if tp + fn else 100.0
    risk_accuracy = _pct((tp + tn) / case_count)
    approval_precision = _pct(approval_tp / (approval_tp + approval_fp)) if approval_tp + approval_fp else 100.0
    approval_recall = _pct(approval_tp / (approval_tp + approval_fn)) if approval_tp + approval_fn else 100.0
    approval_accuracy = _pct((approval_tp + approval_tn) / case_count)
    model_accuracy = _pct(model_ok / case_count)
    agent_accuracy = _pct(agent_ok / case_count)
    decision_accuracy = _pct(decision_ok / case_count)
    context_accuracy = _pct(context_ok / case_count)
    calibration_score = round(
        (
            risk_precision
            + risk_recall
            + approval_precision
            + approval_recall
            + model_accuracy
            + agent_accuracy
            + decision_accuracy
            + context_accuracy
        )
        / 8,
        2,
    )
    return {
        "case_count": case_count,
        "false_positives": fp,
        "false_negatives": fn,
        "false_positive_rate": _pct(fp / (fp + tn)) if fp + tn else 0.0,
        "false_negative_rate": _pct(fn / (fn + tp)) if fn + tp else 0.0,
        "risk_precision": risk_precision,
        "risk_recall": risk_recall,
        "risk_accuracy": risk_accuracy,
        "approval_precision": approval_precision,
        "approval_recall": approval_recall,
        "approval_accuracy": approval_accuracy,
        "model_routing_accuracy": model_accuracy,
        "agent_routing_accuracy": agent_accuracy,
        "decision_accuracy": decision_accuracy,
        "context_minimization": context_accuracy,
        "calibration_score": calibration_score,
    }


def _run_benchmark() -> tuple[list[dict], dict[str, float | int]]:
    rows = []
    for case in _load_cases():
        report = simulate_orchestration(
            case["prompt"], proposed_commands=case.get("proposed_commands", [])
        )
        rows.append(
            {
                "id": case["id"],
                "expected": case["expected"],
                "observed": {
                    "risk": report["intake"]["risk_level"],
                    "approval_required": report["decision_gate"]["requires_human_approval"],
                    "model": report["model_routing"]["selected_model_class"],
                    "agents": [
                        assignment["agent"]
                        for assignment in report["agent_assignments"]
                    ],
                    "decision": report["final_decision"],
                },
            }
        )
    return rows, _metrics(rows)


def test_decision_benchmark_dataset_is_versioned_and_complete():
    cases = _load_cases()
    case_ids = [case["id"] for case in cases]
    assert len(case_ids) == len(set(case_ids))
    for case in cases:
        assert case["prompt"]
        assert set(case["expected"]) == {
            "risk",
            "approval_required",
            "model",
            "agents",
            "decision",
        }


def test_orchestrator_matches_decision_benchmark_cases():
    rows, metrics = _run_benchmark()
    failures = [row for row in rows if row["expected"] != row["observed"]]
    assert failures == []
    assert metrics["case_count"] == 45


def test_decision_benchmark_calibration_thresholds():
    _, metrics = _run_benchmark()
    assert metrics["false_positive_rate"] <= 10.0
    assert metrics["false_negative_rate"] <= 5.0
    assert metrics["risk_precision"] >= 90.0
    assert metrics["approval_precision"] >= 90.0
    assert metrics["model_routing_accuracy"] >= 90.0
    assert metrics["calibration_score"] >= 90.0
    assert metrics["context_minimization"] >= 95.0
