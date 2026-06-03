# -*- coding: utf-8 -*-
"""Transcript message widgets (user / assistant / thinking / errors)."""

from __future__ import annotations

from rich.text import Text
from textual.app import ComposeResult
from textual.widget import Widget
from textual.widgets import Collapsible, Markdown, Static


class UserMessage(Static):
    """A user turn, shown with a prompt glyph."""

    def __init__(self, text: str) -> None:
        body = Text()
        body.append("❯ ", style="bold #6db8ff")
        body.append(text)
        super().__init__(body, classes="msg user")


class AssistantMessage(Widget):
    """Streaming assistant answer rendered as markdown.

    ``append()`` accumulates deltas and re-renders; the lane label is shown
    once above the body.
    """

    DEFAULT_CSS = """
    AssistantMessage { height: auto; }
    AssistantMessage > .label { color: #b48cff; text-style: bold; }
    AssistantMessage > Markdown { height: auto; margin: 0; }
    """

    def __init__(self) -> None:
        super().__init__(classes="msg assistant")
        self._text = ""
        self._md = Markdown("")

    def compose(self) -> ComposeResult:
        yield Static("qwenpaw", classes="label")
        yield self._md

    async def append(self, delta: str) -> None:
        self._text += delta
        await self._md.update(self._text)

    @property
    def text(self) -> str:
        return self._text


class ThoughtMessage(Collapsible):
    """Dimmed agent thinking lane, collapsed by default.

    The reasoning streams into the (hidden) body; the user can expand the
    header to read it. Reused for plan summaries via the ``title`` argument.
    """

    def __init__(
        self, title: str = "💭 thinking", collapsed: bool = True
    ) -> None:
        self._text = ""
        self._body = Static(Text("", style="italic #8a8a8a"))
        super().__init__(
            self._body,
            title=title,
            collapsed=collapsed,
            classes="msg thought",
        )

    def append(self, delta: str) -> None:
        self._text += delta
        self._body.update(Text(self._text, style="italic #8a8a8a"))


class PushMessageBox(Static):
    """A server-initiated proactive message."""

    def __init__(self, text: str) -> None:
        body = Text()
        body.append("✦ ", style="bold #ffcf6d")
        body.append(text, style="#ffcf6d")
        super().__init__(body, classes="msg push")


class ErrorMessage(Static):
    """A transport/agent error."""

    def __init__(self, text: str) -> None:
        body = Text()
        body.append("⚠ ", style="bold #ff6d6d")
        body.append(text, style="#ff9d9d")
        super().__init__(body, classes="msg error")
