"""`cd ~/repo && git ...` and `git -C $VAR/repo ...` reach the right folder in every hook that follows a cd."""

import importlib.util
import sys
from pathlib import Path

import pytest

HOOKS = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(HOOKS / "lib"))
NAMES = ["pretool-branch-safety", "pretool-unified-gate", "pretool-private-name-leak-gate", "security-review-hook"]


def _load(name: str):
    spec = importlib.util.spec_from_file_location(name.replace("-", "_"), HOOKS / f"{name}.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


@pytest.mark.parametrize("name", NAMES)
def test_home_variable_and_relative_targets_are_resolved(name, monkeypatch):
    monkeypatch.setenv("HOME", "/home/u")
    monkeypatch.setenv("WORK", "/srv/work")
    cwd = _load(name)._extract_effective_cwd
    assert cwd("cd ~/repo && git commit -m x", "/session") == "/home/u/repo"
    assert cwd('cd "~/my repo"; git commit -m x', "/session") == "/home/u/my repo"
    assert cwd("git -C $WORK/repo commit -m x", "/session") == "/srv/work/repo"
    assert cwd("cd sub && git commit -m x", "/session") == "/session/sub"
    assert cwd("cd /abs && git commit -m x", "/session") == "/abs"
    assert cwd("git status", "/session") == "/session"
