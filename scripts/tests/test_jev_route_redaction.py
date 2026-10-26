"""Integration contracts for route transport and project context."""

from __future__ import annotations

import importlib.util
import json
import subprocess
import sys
from pathlib import Path
from unittest import mock

import pytest

SCRIPTS = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(SCRIPTS))
spec = importlib.util.spec_from_file_location("jev_route", SCRIPTS / "jev-route.py")
jev_route = importlib.util.module_from_spec(spec)
spec.loader.exec_module(jev_route)
FAKE = "ghp_" + "x" * 36


@pytest.mark.parametrize(
    ("scenario", "expected_calls", "expected_source"),
    [
        ("normal", 1, "session"),
        ("force", 1, "pre-route-force"),
        ("trivial", 1, "session"),
        ("unavailable", 0, "session"),
        ("error", 1, "session"),
    ],
)
def test_cli_only_evaluates_attachment_evidence(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
    scenario: str,
    expected_calls: int,
    expected_source: str,
) -> None:
    """Prepare batches attachment evidence once and leaves intent validation to dispatch."""
    request = "hello" if scenario == "trivial" else "fix it"
    monkeypatch.setattr(sys, "argv", ["jev-route.py", "--request", request, "--json-compact"])
    monkeypatch.setattr(
        jev_route,
        "_run_pre_route",
        lambda _request: {
            "matched": scenario == "force",
            "confidence": "high",
            "match_type": "force_route",
            "agent": "python-general-engineer",
            "skill": "pr-workflow",
        },
    )
    monkeypatch.setattr(jev_route.jev_transport, "available", lambda: (scenario != "unavailable", "test"))
    answers = {
        "answers": {
            **{key: {"noul": 0.0} for key in jev_route.NOUL_SIGNAL_KEYS},
            **{
                f"{jev_route.DOMAIN_NOUL_PREFIX}{jev_route._sanitize_key(name)}": {"noul": 0.0}
                for name in jev_route.DOMAIN_NOUL_INSTRUCTIONS
            },
        }
    }
    responses = RuntimeError("gateway unavailable") if scenario == "error" else [answers]
    with mock.patch.object(jev_route.jev_transport, "evaluate_packed", side_effect=responses) as evaluate:
        assert jev_route.main() == 0
    result = json.loads(capsys.readouterr().out)
    assert evaluate.call_count == expected_calls
    assert result["source"] == expected_source
    assert "intent_alignment" not in result
    assert result["jev_called"] is (expected_calls == 1)
    assert (result["forced"] is not None) is (scenario == "force")
    assert (result["error"] is not None) is (scenario in {"unavailable", "error"})
    if expected_calls:
        questions = evaluate.call_args.args[1]
        assert set(questions) == set(answers["answers"])
        assert {question["type"] for question in questions.values()} == {"noul"}


def test_call_jev_uses_vercel_gateway_and_never_passes_a_direct_api_key():
    payload = {"state": f"deploy with token {FAKE} now", "model": "typesafe-ai/jev", "questions": {}}
    sent: dict[str, object] = {}

    def evaluate(state, questions, *, timeout):
        sent.update({"state": state, "questions": questions, "timeout": timeout})
        return {"answers": {}}

    with mock.patch.object(jev_route.jev_transport, "evaluate_packed", side_effect=evaluate):
        result, _ = jev_route._call_jev(payload, 5)
    assert result == {"answers": {}}
    assert sent["state"] == payload["state"]
    assert sent["questions"] == {}
    assert "api_key" not in sent


def test_call_jev_redacts_before_the_vercel_bridge(monkeypatch, capsys):
    payload = {"state": f"deploy with token {FAKE} now", "model": "typesafe-ai/jev", "questions": {}}
    sent: dict[str, object] = {}

    def run(command, *, input, text, capture_output, timeout, check, env):
        sent.update(command=command, input=input, timeout=timeout, env=env)
        return subprocess.CompletedProcess(command, 0, json.dumps({"answers": {}}), "")

    monkeypatch.setenv("AI_GATEWAY_API_KEY", "gateway-test-key")
    monkeypatch.delenv("TYPESAFE_API_KEY", raising=False)
    with mock.patch.object(jev_route.jev_transport.jev_vercel.subprocess, "run", side_effect=run):
        result, _ = jev_route._call_jev(payload, 5)
    assert result["answers"] == {}
    assert FAKE not in str(sent["input"])
    assert "<redacted:github:xxxx>" in str(sent["input"])
    assert "gateway-test-key" not in str(sent["input"])
    assert FAKE in payload["state"]
    assert "[jev-redact] 1 value(s)" in capsys.readouterr().err


class TestProjectContext:
    def test_detects_languages_frameworks_datastores(self, tmp_path):
        (tmp_path / "requirements.txt").write_text("Flask==3.0\npeewee>=3\n", encoding="utf-8")
        (tmp_path / "package.json").write_text('{"dependencies": {"react": "18"}}', encoding="utf-8")
        assert jev_route.detect_project_context(tmp_path) == {
            "languages": ["python", "javascript"],
            "frameworks": ["flask", "react"],
            "datastores": ["peewee"],
        }

    def test_returns_none_when_nothing_detected(self, tmp_path):
        assert jev_route.detect_project_context(tmp_path) is None
        assert jev_route.detect_project_context(None) is None
        assert jev_route.detect_project_context(tmp_path / "missing") is None

    def test_context_never_carries_paths_or_file_contents(self, tmp_path):
        (tmp_path / "requirements.txt").write_text("flask\nSECRET_TOKEN=abc123\n", encoding="utf-8")
        context = str(jev_route.detect_project_context(tmp_path))
        assert str(tmp_path) not in context
        assert "abc123" not in context

    def test_bare_request_state_is_unchanged_without_project(self):
        payload = jev_route._build_attach_payload("fix it")
        assert payload["state"] == "fix it"

    def test_project_facts_go_in_state(self):
        project = {"languages": ["python"]}
        payload = jev_route._build_attach_payload("fix it", project)
        assert payload["state"] == {"request": "fix it", "project": project}
