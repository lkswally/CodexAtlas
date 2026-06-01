import os

os.environ["ATLAS_DISABLE_EVENT_LOGS"] = "1"

from tests._support_paths import ATLAS_ROOT
from tools.n8n_workflow_blueprint_generator import generate_n8n_workflow_blueprint


def test_n8n_workflow_blueprint_without_side_effects_stays_low_or_medium_risk():
    result = generate_n8n_workflow_blueprint(
        {
            "task": "Crear un workflow n8n para analizar una idea de negocio y devolver un reporte interno para revision humana."
        },
        root=ATLAS_ROOT,
        project=ATLAS_ROOT,
    )

    assert result["status"] == "ok"
    assert result["readiness_posture"]["risk_level"] in {"low", "medium"}
    assert result["side_effects"] == []
    assert result["test_payload"]


def test_n8n_workflow_blueprint_with_email_requires_human_approval():
    result = generate_n8n_workflow_blueprint(
        {
            "task": "Crear un workflow n8n para recibir una idea de negocio, analizarla con IA y enviar un informe por email."
        },
        root=ATLAS_ROOT,
        project=ATLAS_ROOT,
    )

    assert result["human_approval_required"] is True
    assert "send_email_real" in result["side_effects"]
    assert result["readiness_posture"]["human_approval_required"] is True
    assert result["credentials_placeholders"]


def test_n8n_workflow_blueprint_always_provides_test_payload_and_readiness():
    result = generate_n8n_workflow_blueprint(
        {
            "task": "Crear un workflow n8n para revisar un brief y estructurar una salida."
        },
        root=ATLAS_ROOT,
        project=ATLAS_ROOT,
    )

    assert isinstance(result["test_payload"], dict)
    assert result["test_payload"]
    assert result["readiness_posture"]["status"] == "ok"
    assert result["readiness_posture"]["test_payload_required"] is False
