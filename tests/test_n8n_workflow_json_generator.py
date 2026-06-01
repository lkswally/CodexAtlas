import os

os.environ["ATLAS_DISABLE_EVENT_LOGS"] = "1"

from tests._support_paths import ATLAS_ROOT
from tools.n8n_workflow_json_generator import generate_n8n_workflow_json


def test_n8n_workflow_json_generated_inactive_by_default():
    result = generate_n8n_workflow_json(
        {
            "task": "Crear un workflow n8n para analizar una idea de negocio y dejar un reporte interno."
        },
        root=ATLAS_ROOT,
        project=ATLAS_ROOT,
    )

    assert result["status"] == "ok"
    assert result["workflow_json_generated"] is True
    assert result["workflow_active"] is False
    assert result["workflow_json"]["active"] is False


def test_n8n_workflow_json_blocks_real_credentials():
    result = generate_n8n_workflow_json(
        {
            "task": "Crear un workflow n8n para enviar un informe por email.",
            "credentials": {
                "api_key": "sk-live-real-secret"
            },
        },
        root=ATLAS_ROOT,
        project=ATLAS_ROOT,
    )

    assert result["status"] == "blocked"
    assert result["workflow_json_generated"] is False
    assert result["contains_real_credentials"] is True
    assert "real_credentials_not_allowed" in result["blocked_reasons"]


def test_n8n_workflow_json_uses_safe_placeholders_and_readiness_posture():
    result = generate_n8n_workflow_json(
        {
            "task": "Crear un workflow n8n para recibir una idea de negocio, analizarla con IA y enviar un informe por email."
        },
        root=ATLAS_ROOT,
        project=ATLAS_ROOT,
    )

    assert result["status"] == "ok"
    assert result["requires_manual_credential_binding"] is True
    assert any("MANUAL_BIND_REQUIRED" in item for item in result["credential_placeholders"])
    assert result["human_approval_required"] is True
    assert result["readiness_posture"]["status"] == "ok"
    assert result["test_payload"]
