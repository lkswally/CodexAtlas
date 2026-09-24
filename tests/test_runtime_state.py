from tools.runtime_state import runtime_state_dir, runtime_state_file


def test_runtime_state_is_separate_from_versioned_memory(tmp_path, monkeypatch):
    monkeypatch.delenv("ATLAS_RUNTIME_STATE_DIR", raising=False)

    assert runtime_state_dir(tmp_path) == tmp_path / ".atlas_runtime"
    assert runtime_state_file(tmp_path, "routing_log.jsonl") == tmp_path / ".atlas_runtime" / "routing_log.jsonl"
    assert runtime_state_file(tmp_path, "routing_log.jsonl") != tmp_path / "memory" / "routing_log.jsonl"


def test_runtime_state_directory_can_be_overridden(tmp_path, monkeypatch):
    monkeypatch.setenv("ATLAS_RUNTIME_STATE_DIR", "local-state")

    assert runtime_state_file(tmp_path, "mcp_events.jsonl") == tmp_path / "local-state" / "mcp_events.jsonl"
