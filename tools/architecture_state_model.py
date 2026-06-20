from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict, Mapping, Optional


ARCHITECTURE_DOMAINS = (
    "governance",
    "evidence",
    "mcp",
    "skills",
    "agents_roles",
    "workflows",
    "security",
    "tests",
    "docs",
    "dashboard",
    "model_routing",
    "failure_registry",
    "release",
)
VALID_STATUSES = {"PASS", "WARN", "FAIL", "UNKNOWN"}
DOMAIN_FIELDS = (
    "status",
    "evidence",
    "freshness",
    "risks",
    "dependencies",
    "confidence",
    "next_actions",
)


class ArchitectureStateError(ValueError):
    """Raised when an architecture state report violates its contract."""


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _list_value(value: Any) -> list[Any]:
    return list(value) if isinstance(value, (list, tuple)) else []


def _confidence(value: Any) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        return 0.0
    return min(1.0, max(0.0, float(value)))


def _build_domain(raw: Any) -> Dict[str, Any]:
    source = dict(raw) if isinstance(raw, Mapping) else {}
    risks = _list_value(source.get("risks"))
    next_actions = _list_value(source.get("next_actions"))
    evidence = _list_value(source.get("evidence"))
    freshness = (
        dict(source.get("freshness", {}))
        if isinstance(source.get("freshness", {}), Mapping)
        else {}
    )

    requested_status = str(source.get("status", "UNKNOWN")).upper()
    status = requested_status if requested_status in VALID_STATUSES else "UNKNOWN"
    if status != requested_status:
        risks.append("invalid_status_rejected")
        next_actions.append("Provide a valid PASS, WARN, FAIL or UNKNOWN status.")

    if status == "PASS" and not evidence:
        status = "UNKNOWN"
        risks.append("pass_without_evidence_rejected")
        next_actions.append("Attach evidence before declaring PASS.")

    if status == "PASS" and freshness.get("is_stale") is True:
        status = "WARN"
        risks.append("stale_pass_downgraded")
        next_actions.append("Refresh evidence before restoring PASS.")

    return {
        "status": status,
        "evidence": evidence,
        "freshness": freshness,
        "risks": list(dict.fromkeys(str(item) for item in risks if str(item))),
        "dependencies": _list_value(source.get("dependencies")),
        "confidence": _confidence(source.get("confidence", 0.0)),
        "next_actions": list(
            dict.fromkeys(str(item) for item in next_actions if str(item))
        ),
    }


def _overall_status(domains: Mapping[str, Mapping[str, Any]]) -> str:
    statuses = [str(item["status"]) for item in domains.values()]
    if "FAIL" in statuses:
        return "FAIL"
    if "WARN" in statuses:
        return "WARN"
    if "UNKNOWN" in statuses:
        return "UNKNOWN" if set(statuses) == {"UNKNOWN"} else "WARN"
    return "PASS"


def build_architecture_state(
    observations: Optional[Mapping[str, Mapping[str, Any]]] = None,
    *,
    generated_at: Optional[str] = None,
) -> Dict[str, Any]:
    """Build a conservative architecture state from explicit observations."""
    source = observations or {}
    domains = {
        domain: _build_domain(source.get(domain, {}))
        for domain in ARCHITECTURE_DOMAINS
    }
    report = {
        "state_model": "atlas_architecture_state",
        "version": "v1",
        "generated_at": generated_at or _utc_now_iso(),
        "overall_status": _overall_status(domains),
        "domains": domains,
    }
    validate_architecture_state(report)
    return report


def validate_architecture_state(report: Any) -> bool:
    if not isinstance(report, Mapping):
        raise ArchitectureStateError("Architecture state must be an object.")
    required = {"state_model", "version", "generated_at", "overall_status", "domains"}
    if not required.issubset(report):
        raise ArchitectureStateError("Architecture state is missing required fields.")
    if report["overall_status"] not in VALID_STATUSES:
        raise ArchitectureStateError("Architecture overall_status is invalid.")
    domains = report.get("domains")
    if not isinstance(domains, Mapping) or set(domains) != set(ARCHITECTURE_DOMAINS):
        raise ArchitectureStateError("Architecture state must contain every canonical domain exactly once.")

    for name, domain in domains.items():
        if not isinstance(domain, Mapping) or set(domain) != set(DOMAIN_FIELDS):
            raise ArchitectureStateError(f"Domain `{name}` violates the field contract.")
        if domain["status"] not in VALID_STATUSES:
            raise ArchitectureStateError(f"Domain `{name}` has an invalid status.")
        for field in ("evidence", "risks", "dependencies", "next_actions"):
            if not isinstance(domain[field], list):
                raise ArchitectureStateError(f"Domain `{name}` field `{field}` must be a list.")
        if not isinstance(domain["freshness"], Mapping):
            raise ArchitectureStateError(f"Domain `{name}` freshness must be an object.")
        confidence = domain["confidence"]
        if isinstance(confidence, bool) or not isinstance(confidence, (int, float)):
            raise ArchitectureStateError(f"Domain `{name}` confidence must be numeric.")
        if not 0.0 <= float(confidence) <= 1.0:
            raise ArchitectureStateError(f"Domain `{name}` confidence must be between 0 and 1.")
        if domain["status"] == "PASS" and not domain["evidence"]:
            raise ArchitectureStateError(f"Domain `{name}` cannot PASS without evidence.")
    expected_overall = _overall_status(domains)
    if report["overall_status"] != expected_overall:
        raise ArchitectureStateError(
            f"Architecture overall_status must be {expected_overall} for the domain states."
        )
    return True
