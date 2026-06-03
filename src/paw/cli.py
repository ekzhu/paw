# -*- coding: utf-8 -*-
"""The ``paw`` command.

``paw``                       open an interactive chat with a QwenPaw agent
``paw -p "..."``              run a single turn, print the answer, exit
``paw --remote ssh://host``   drive a QwenPaw on a remote host over SSH (ACP)
``paw --remote https://...``  attach to a running ``qwenpaw app`` (HTTP/SSE)
``paw --agent-cmd "..."``     drive an explicit ACP agent command

Textual is imported lazily so ``paw --help`` and one-shot mode stay snappy.
"""

from __future__ import annotations

import asyncio
import sys

import click

from .__version__ import __version__
from .resolve import AgentResolutionError, resolve_agent_command


def _build_transport(
    *,
    agent: str | None,
    agent_cmd: str | None,
    remote: str | None,
):
    """Return a started-on-demand transport for the requested target."""
    if remote and remote.startswith(("http://", "https://")):
        raise click.ClickException(
            "remote HTTP/SSE transport (to `qwenpaw app`) is not implemented "
            "yet; use `--remote ssh://host` for a remote agent over SSH, "
            "or run paw against a local/bundled QwenPaw."
        )

    ssh = remote if (remote and remote.startswith("ssh://")) else None
    if remote and not ssh and not remote.startswith(("http://", "https://")):
        # Bare host given: treat as ssh://host.
        ssh = f"ssh://{remote}"

    try:
        resolved = resolve_agent_command(
            agent=agent, agent_cmd=agent_cmd, ssh=ssh
        )
    except AgentResolutionError as exc:
        raise click.ClickException(str(exc)) from exc

    from .transport.acp import AcpTransport

    return AcpTransport(agent=agent, command=resolved.command), resolved


async def _run_oneshot(transport, prompt: str) -> int:
    """Send one prompt, stream the answer to stdout, return an exit code."""
    from .events import TextDelta, TransportError, TurnEnded

    rc = 0
    try:
        await transport.start()
        await transport.send(prompt)
        async for event in transport.events():
            if isinstance(event, TextDelta):
                sys.stdout.write(event.text)
                sys.stdout.flush()
            elif isinstance(event, TransportError):
                sys.stderr.write(f"\nerror: {event.message}\n")
                rc = 1
            elif isinstance(event, TurnEnded):
                break
        sys.stdout.write("\n")
    finally:
        await transport.close()
    return rc


@click.command("paw", context_settings={"help_option_names": ["-h", "--help"]})
@click.option("--agent", default=None, help="Agent ID to chat with.")
@click.option(
    "-p",
    "--prompt",
    default=None,
    help="Run a single turn non-interactively and print the answer.",
)
@click.option(
    "--remote",
    default=None,
    metavar="TARGET",
    help="ssh://[user@]host[:port] for a remote QwenPaw over SSH "
    "(https://host for a `qwenpaw app` server — not yet implemented).",
)
@click.option(
    "--agent-cmd",
    default=None,
    metavar="COMMAND",
    help="Explicit command that speaks ACP over stdio "
    "(e.g. 'qwenpaw acp'). Overrides discovery.",
)
@click.version_option(version=__version__, prog_name="paw")
def main(
    agent: str | None,
    prompt: str | None,
    remote: str | None,
    agent_cmd: str | None,
) -> None:
    """paw — a terminal chat UI for QwenPaw."""
    transport, resolved = _build_transport(
        agent=agent, agent_cmd=agent_cmd, remote=remote
    )

    if prompt is not None:
        rc = asyncio.run(_run_oneshot(transport, prompt))
        if rc:
            sys.exit(rc)
        return

    from .app import PawApp

    PawApp(
        transport, agent=agent or "default", target=resolved.description
    ).run()


if __name__ == "__main__":
    main()
