# -*- coding: utf-8 -*-
"""Resolve how to launch the QwenPaw ACP agent paw should drive.

Resolution order (first match wins):

1. ``--agent-cmd "..."`` — an explicit command, used verbatim.
2. ``--remote ssh://[user@]host[:port]`` — run ``qwenpaw acp`` on a remote host
   over SSH (ACP/stdio tunnelled through ssh).
3. Bundled QwenPaw — if ``qwenpaw`` is importable in *this* interpreter
   (``pip install paw[bundled]``), run ``python -m qwenpaw acp``.
4. QwenPaw on PATH — ``qwenpaw acp``.

If none apply, a clear error tells the user how to fix it.
"""

from __future__ import annotations

import importlib.util
import shlex
import shutil
import sys
from dataclasses import dataclass
from urllib.parse import urlparse


class AgentResolutionError(RuntimeError):
    """Raised when paw cannot determine how to start a QwenPaw agent."""


@dataclass(frozen=True)
class ResolvedAgent:
    command: list[str]
    description: str  # human-readable, for the status bar / errors


def _bundled_qwenpaw() -> bool:
    return importlib.util.find_spec("qwenpaw") is not None


def _ssh_command(remote: str) -> list[str]:
    """Build an ssh argv for ``ssh://[user@]host[:port]``."""
    parsed = urlparse(remote)
    if not parsed.hostname:
        raise AgentResolutionError(f"invalid ssh target: {remote!r}")
    target = (
        f"{parsed.username}@{parsed.hostname}"
        if parsed.username
        else parsed.hostname
    )
    cmd = ["ssh"]
    if parsed.port:
        cmd += ["-p", str(parsed.port)]
    cmd.append(target)
    return cmd


def resolve_agent_command(
    *,
    agent: str | None = None,
    agent_cmd: str | None = None,
    ssh: str | None = None,
) -> ResolvedAgent:
    """Return the argv (and a label) to spawn the QwenPaw ACP agent."""
    suffix: list[str] = ["--agent", agent] if agent else []

    if agent_cmd:
        return ResolvedAgent(
            command=shlex.split(agent_cmd) + suffix,
            description=f"custom: {agent_cmd}",
        )

    if ssh:
        base = _ssh_command(ssh)
        return ResolvedAgent(
            command=base + ["qwenpaw", "acp"] + suffix,
            description=f"ssh: {ssh}",
        )

    if _bundled_qwenpaw():
        return ResolvedAgent(
            command=[sys.executable, "-m", "qwenpaw", "acp"] + suffix,
            description="bundled qwenpaw",
        )

    found = shutil.which("qwenpaw")
    if found:
        return ResolvedAgent(
            command=[found, "acp"] + suffix,
            description=f"qwenpaw on PATH ({found})",
        )

    raise AgentResolutionError(
        "QwenPaw not found. Either install it alongside paw "
        "(`pip install paw[bundled]` or `pip install qwenpaw`), point paw "
        "remote with `--remote ssh://host`, or pass `--agent-cmd '<command>'`."
    )
