# -*- coding: utf-8 -*-
"""Unit tests for agent-command resolution."""

from __future__ import annotations

import sys

import pytest

from paw import resolve
from paw.resolve import AgentResolutionError, resolve_agent_command


def test_explicit_agent_cmd_is_split():
    r = resolve_agent_command(agent_cmd="qwenpaw acp")
    assert r.command == ["qwenpaw", "acp"]


def test_agent_id_is_appended():
    r = resolve_agent_command(agent_cmd="qwenpaw acp", agent="writer")
    assert r.command == ["qwenpaw", "acp", "--agent", "writer"]


def test_ssh_target():
    r = resolve_agent_command(ssh="ssh://me@box:2222")
    assert r.command == ["ssh", "-p", "2222", "me@box", "qwenpaw", "acp"]
    assert "ssh" in r.description


def test_ssh_without_user_or_port():
    r = resolve_agent_command(ssh="ssh://host")
    assert r.command == ["ssh", "host", "qwenpaw", "acp"]


def test_bundled_preferred(monkeypatch):
    monkeypatch.setattr(resolve, "_bundled_qwenpaw", lambda: True)
    r = resolve_agent_command()
    assert r.command == [sys.executable, "-m", "qwenpaw", "acp"]
    assert r.description == "bundled qwenpaw"


def test_path_fallback(monkeypatch):
    monkeypatch.setattr(resolve, "_bundled_qwenpaw", lambda: False)
    monkeypatch.setattr(resolve.shutil, "which", lambda _: "/usr/bin/qwenpaw")
    r = resolve_agent_command()
    assert r.command == ["/usr/bin/qwenpaw", "acp"]


def test_not_found_raises(monkeypatch):
    monkeypatch.setattr(resolve, "_bundled_qwenpaw", lambda: False)
    monkeypatch.setattr(resolve.shutil, "which", lambda _: None)
    with pytest.raises(AgentResolutionError):
        resolve_agent_command()
