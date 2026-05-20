from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Any, Dict, List, Optional

try:
    from tools.model_cost_control_readiness import assess_model_cost_control
except ModuleNotFoundError:
    from model_cost_control_readiness import assess_model_cost_control


DEFAULT_ROOT = Path(__file__).resolve().parents[1]
RULES_PATH = Path("config/business_idea_simulation_rules.json")


def load_business_idea_simulation_rules(root: Path = DEFAULT_ROOT) -> Dict[str, Any]:
    return json.loads((root / RULES_PATH).read_text(encoding="utf-8-sig"))


def _normalize(text: str) -> str:
    return re.sub(r"\s+", " ", str(text or "")).strip().lower()


def _stringify(value: Any) -> str:
    if isinstance(value, str):
        return value.strip()
    if isinstance(value, (list, tuple, set)):
        return ", ".join(str(item).strip() for item in value if str(item).strip())
    if isinstance(value, dict):
        return ", ".join(f"{key}: {value[key]}" for key in value if str(value[key]).strip())
    return str(value).strip()


def _has_value(value: Any) -> bool:
    if value is None:
        return False
    if isinstance(value, str):
        return bool(value.strip())
    if isinstance(value, (list, tuple, set, dict)):
        return bool(value)
    return True


def _extract_inputs(payload: Dict[str, Any], rules: Dict[str, Any]) -> Dict[str, str]:
    aliases = rules.get("input_aliases", {})
    extracted: Dict[str, str] = {}
    for canonical in rules.get("required_inputs", []):
        candidates = [canonical, *list(aliases.get(canonical, []))]
        for name in candidates:
            value = payload.get(name)
            if _has_value(value):
                extracted[canonical] = _stringify(value)
                break

    for optional_field in ("legal_risks", "technical_risks", "commercial_risks"):
        candidates = [optional_field, *list(aliases.get(optional_field, []))]
        for name in candidates:
            value = payload.get(name)
            if _has_value(value):
                extracted[optional_field] = _stringify(value)
                break
    return extracted


def _collect_surface(payload: Dict[str, Any], extracted: Dict[str, str]) -> str:
    parts: List[str] = []
    for key, value in payload.items():
        if key.endswith("_json"):
            continue
        text = _stringify(value)
        if text:
            parts.append(text)
    parts.extend(value for value in extracted.values() if value)
    return " ".join(parts)


def _detect_prediction_block(surface: str, payload: Dict[str, Any], rules: Dict[str, Any]) -> bool:
    if bool(payload.get("guaranteed_prediction_requested")):
        return True
    normalized_surface = _normalize(surface)
    return any(_normalize(term) in normalized_surface for term in rules.get("blocked_prediction_terms", []))


def _infer_signal(
    *,
    blocked: bool,
    present_count: int,
    missing_core: List[str],
    missing_required: List[str],
    rules: Dict[str, Any],
) -> str:
    if blocked:
        return "weak"
    if missing_core:
        return "weak"
    thresholds = rules.get("signal_thresholds", {})
    if present_count >= int(thresholds.get("promising_min_present", 7)) and len(missing_required) <= 2:
        return "promising"
    if present_count >= int(thresholds.get("incomplete_min_present", 4)):
        return "incomplete"
    return "weak"


def _infer_readiness_state(
    *,
    blocked: bool,
    missing_core: List[str],
    present_inputs: Dict[str, str],
    rules: Dict[str, Any],
) -> str:
    if blocked:
        return "blocked"
    if missing_core:
        return "insufficient_data"
    scenario_ready_inputs = [str(item).strip() for item in rules.get("scenario_ready_inputs", []) if str(item).strip()]
    if all(field in present_inputs for field in scenario_ready_inputs):
        return "scenario_ready"
    return "research_required"


def _profitability_posture(present_inputs: Dict[str, str], rules: Dict[str, Any]) -> tuple[bool, str, List[str]]:
    required = [str(item).strip() for item in rules.get("profitability_inputs", []) if str(item).strip()]
    missing = [field for field in required if field not in present_inputs]
    if not {"pricing", "costs"} <= set(present_inputs):
        return False, "low", missing
    if not missing:
        return True, "medium", []
    return True, "low", missing


def _infer_risks(surface: str, extracted: Dict[str, str], missing_inputs: List[str], rules: Dict[str, Any]) -> List[Dict[str, str]]:
    risks: List[Dict[str, str]] = []
    normalized_surface = _normalize(surface)

    for category in rules.get("risk_categories", []):
        signal_terms = [str(item).strip().lower() for item in (rules.get("risk_signals", {}) or {}).get(category, []) if str(item).strip()]
        hits = [term for term in signal_terms if term in normalized_surface]
        explicit_key = f"{category}_risks"
        if hits or explicit_key in extracted:
            risks.append(
                {
                    "category": str(category),
                    "level": "medium" if hits else "stated",
                    "reason": extracted.get(explicit_key) or f"Detected {category} risk signals: {', '.join(hits)}.",
                }
            )

    if "competition" in missing_inputs:
        risks.append(
            {
                "category": "commercial",
                "level": "medium",
                "reason": "Competition or substitute map is missing, so differentiation is still weak.",
            }
        )
    if "pricing" in missing_inputs or "costs" in missing_inputs:
        risks.append(
            {
                "category": "commercial",
                "level": "high",
                "reason": "Pricing or cost structure is missing, so unit economics cannot be defended yet.",
            }
        )
    if "channels" in missing_inputs or "acquisition" in missing_inputs:
        risks.append(
            {
                "category": "commercial",
                "level": "medium",
                "reason": "Acquisition path is unclear, so demand may be harder or more expensive than expected.",
            }
        )
    if "retention" in missing_inputs:
        risks.append(
            {
                "category": "commercial",
                "level": "medium",
                "reason": "Retention assumptions are missing, so recurring revenue or repeat usage is uncertain.",
            }
        )

    deduped: List[Dict[str, str]] = []
    seen: set[tuple[str, str]] = set()
    for risk in risks:
        key = (risk["category"], risk["reason"])
        if key not in seen:
            seen.add(key)
            deduped.append(risk)
    return deduped


def _select_experiments(missing_inputs: List[str], rules: Dict[str, Any]) -> List[Dict[str, str]]:
    selected: List[Dict[str, str]] = []
    missing_set = set(missing_inputs)
    for experiment in rules.get("experiment_catalog", []):
        applies = set(str(item).strip() for item in experiment.get("applies_when_missing_any", []) if str(item).strip())
        if applies and missing_set.intersection(applies):
            selected.append(
                {
                    "id": str(experiment.get("id", "")).strip(),
                    "objective": str(experiment.get("objective", "")).strip(),
                    "success_signal": str(experiment.get("success_signal", "")).strip(),
                    "time_estimate": str(experiment.get("time_estimate", "")).strip(),
                }
            )
    if not selected:
        for experiment in rules.get("experiment_catalog", [])[:2]:
            selected.append(
                {
                    "id": str(experiment.get("id", "")).strip(),
                    "objective": str(experiment.get("objective", "")).strip(),
                    "success_signal": str(experiment.get("success_signal", "")).strip(),
                    "time_estimate": str(experiment.get("time_estimate", "")).strip(),
                }
            )
    return selected[:5]


def _build_hypotheses(present_inputs: Dict[str, str], missing_inputs: List[str]) -> List[Dict[str, str]]:
    hypotheses: List[Dict[str, str]] = []
    for field in ("problem", "customer", "value_proposition", "pricing", "channels", "retention"):
        hypotheses.append(
            {
                "hypothesis": f"The {field.replace('_', ' ')} assumption is valid.",
                "needs_validation": "yes" if field in missing_inputs or field in {"pricing", "channels", "retention"} else "partially",
                "risk_if_false": "high" if field in {"problem", "customer", "pricing"} else "medium",
            }
        )
    return hypotheses


def _build_scenarios(missing_inputs: List[str]) -> Dict[str, Dict[str, Any]]:
    pricing_missing = "pricing" in missing_inputs or "costs" in missing_inputs
    acquisition_missing = "channels" in missing_inputs or "acquisition" in missing_inputs
    retention_missing = "retention" in missing_inputs
    return {
        "optimistic": {
            "what_has_to_happen": [
                "The customer pain is real and frequent.",
                "Early users accept the first pricing hypothesis.",
                "Acquisition works through one repeatable channel.",
            ],
            "risks": ["Overestimating willingness to pay." if pricing_missing else "Execution still needs disciplined delivery."],
            "signals_to_watch": ["Qualified demand", "Positive pricing reactions", "Repeat usage or paid pilots"],
        },
        "base": {
            "what_has_to_happen": [
                "A narrower customer segment responds first.",
                "Manual delivery validates value before automation.",
                "The go-to-market path is learnable but not yet efficient.",
            ],
            "risks": [
                "Sales cycles may be slower than expected." if acquisition_missing else "Acquisition cost may still be higher than expected.",
                "Retention may depend on manual support." if retention_missing else "Retention still needs proof.",
            ],
            "signals_to_watch": ["Follow-up meetings", "Pilot conversion", "Second-session or renewal behavior"],
        },
        "pessimistic": {
            "what_has_to_happen": [
                "The problem is not urgent enough to trigger action.",
                "Current substitutes are good enough.",
                "Pricing or acquisition economics break the model.",
            ],
            "risks": ["Weak differentiation", "Low willingness to pay", "Channel inefficiency"],
            "signals_to_watch": ["Interview indifference", "High CAC", "No repeat usage"],
        },
    }


def assess_business_idea_simulation_readiness(
    payload: Dict[str, Any],
    *,
    root: Path = DEFAULT_ROOT,
) -> Dict[str, Any]:
    rules = load_business_idea_simulation_rules(root)
    present_inputs = _extract_inputs(payload, rules)
    surface = _collect_surface(payload, present_inputs)
    blocked = _detect_prediction_block(surface, payload, rules)

    required_inputs = [str(item).strip() for item in rules.get("required_inputs", []) if str(item).strip()]
    core_inputs = [str(item).strip() for item in rules.get("core_inputs", []) if str(item).strip()]
    missing_inputs = [field for field in required_inputs if field not in present_inputs]
    missing_core = [field for field in core_inputs if field not in present_inputs]

    signal = _infer_signal(
        blocked=blocked,
        present_count=len(present_inputs),
        missing_core=missing_core,
        missing_required=missing_inputs,
        rules=rules,
    )
    readiness_state = _infer_readiness_state(
        blocked=blocked,
        missing_core=missing_core,
        present_inputs=present_inputs,
        rules=rules,
    )
    can_estimate_profitability, profitability_confidence, profitability_missing = _profitability_posture(present_inputs, rules)

    risks = _infer_risks(surface, present_inputs, missing_inputs, rules)
    experiments = _select_experiments(missing_inputs, rules)
    hypotheses = _build_hypotheses(present_inputs, missing_inputs)
    scenarios = _build_scenarios(missing_inputs)

    if blocked:
        recommended_next_step = (
            "Reframe the request: ask Atlas for hypotheses, risks, scenarios and experiments instead of a guaranteed prediction."
        )
    elif missing_core:
        recommended_next_step = "Define one target customer, one painful problem and one concrete value proposition before discussing profitability."
    elif "pricing" in missing_inputs or "costs" in missing_inputs:
        recommended_next_step = "Write a first pricing hypothesis and rough cost structure before using this idea as an investment filter."
    elif "channels" in missing_inputs or "acquisition" in missing_inputs:
        recommended_next_step = "Run a small acquisition smoke test to learn whether qualified demand is reachable."
    elif "retention" in missing_inputs:
        recommended_next_step = "Run a concierge or manual pilot to observe repeat usage before extrapolating retention."
    else:
        recommended_next_step = "Choose the smallest manual MVP or pricing experiment that can validate demand in under two weeks."

    model_cost_guidance = assess_model_cost_control(
        root=root,
        task=surface or "Evaluate a business idea with scenarios, risks and validation experiments.",
        task_type="planning",
        risk_level="medium" if readiness_state != "blocked" else "high",
        complexity="medium" if signal != "weak" else "low",
    )

    why = (
        "Atlas treats business idea evaluation as structured hypothesis review. It can frame scenarios and profitability assumptions, but it must not predict certain outcomes."
    )

    return {
        "status": "ok" if readiness_state != "blocked" else "needs_attention",
        "signal": signal,
        "readiness_state": readiness_state,
        "can_estimate_profitability": can_estimate_profitability and not blocked,
        "profitability_confidence": "low" if blocked else profitability_confidence,
        "must_not_claim_prediction": True,
        "present_inputs": sorted(present_inputs.keys()),
        "missing_inputs": missing_inputs,
        "risks": risks,
        "hypotheses": hypotheses,
        "scenarios": scenarios,
        "experiments": experiments,
        "profitability_missing_inputs": profitability_missing,
        "recommended_next_step": recommended_next_step,
        "model_cost_guidance": model_cost_guidance,
        "why": why,
        "advisory_only": bool(rules.get("advisory_only", True)),
    }


def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(add_help=True)
    parser.add_argument("--payload-json", required=True)
    args = parser.parse_args(argv)
    payload = json.loads(args.payload_json)
    result = assess_business_idea_simulation_readiness(payload, root=DEFAULT_ROOT)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
