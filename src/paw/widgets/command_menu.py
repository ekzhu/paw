# -*- coding: utf-8 -*-
"""Slash-command auto-suggestion: an inline ghost completion plus a
filtered dropdown list.

The agent advertises its commands over ACP (``available_commands_update``);
:class:`CommandSuggester` drives the single inline ghost completion on the
``Input`` and :class:`CommandMenu` renders the navigable dropdown. Both share
the same command list, set via :meth:`set_commands`.
"""

from __future__ import annotations

from rich.text import Text
from textual import events
from textual.suggester import Suggester
from textual.widgets import Input, OptionList
from textual.widgets.option_list import Option

from ..events import SlashCommand


def _query(value: str) -> str | None:
    """The command prefix being typed, or ``None`` if not applicable.

    Active only while the input is a single ``/token`` with no space yet —
    once an argument is started (``/model x``) the command is chosen and
    suggestions step out of the way.
    """
    if not value.startswith("/") or " " in value:
        return None
    return value[1:]


def _matches(commands: list[SlashCommand], query: str) -> list[SlashCommand]:
    q = query.lower()
    return [c for c in commands if c.name.lower().startswith(q)]


class CommandSuggester(Suggester):
    """Inline ghost completion for the top matching command."""

    def __init__(self) -> None:
        super().__init__(use_cache=False, case_sensitive=False)
        self._commands: list[SlashCommand] = []

    def set_commands(self, commands: list[SlashCommand]) -> None:
        self._commands = list(commands)

    async def get_suggestion(self, value: str) -> str | None:
        query = _query(value)
        if not query:  # empty query → nothing to complete yet
            return None
        hits = _matches(self._commands, query)
        return f"/{hits[0].name}" if hits else None


class CommandMenu(OptionList):
    """Dropdown of matching commands, navigated from the focused input.

    Focus stays on the ``Input``; the owning app routes ↑/↓/⏎/⇥/esc here
    via :meth:`cursor_up`, :meth:`cursor_down` and :attr:`selected`.
    """

    # The input keeps focus so typing continues uninterrupted.
    can_focus = False

    DEFAULT_CSS = """
    CommandMenu {
        dock: bottom;
        height: auto;
        max-height: 8;
        margin: 0 0 3 0;
        border: round #3a3a4a;
        background: #1c1c28;
        display: none;
    }
    CommandMenu > .option-list--option-highlighted {
        background: #2a2a3a;
    }
    """

    def __init__(self) -> None:
        super().__init__(id="cmd-menu")
        self._commands: list[SlashCommand] = []

    def set_commands(self, commands: list[SlashCommand]) -> None:
        self._commands = list(commands)

    def update_for(self, value: str) -> None:
        """Refilter and show/hide the dropdown for the current input."""
        query = _query(value)
        hits = _matches(self._commands, query) if query is not None else []
        if not hits:
            self.display = False
            return
        self.clear_options()
        for cmd in hits:
            label = Text()
            label.append(f"/{cmd.name}", style="bold #b48cff")
            if cmd.description:
                label.append(f"  {cmd.description}", style="#8a8a8a")
            self.add_option(Option(label, id=cmd.name))
        self.highlighted = 0
        self.display = True

    @property
    def selected(self) -> str | None:
        """The highlighted command name, or ``None`` when empty."""
        if not self.display or self.highlighted is None:
            return None
        return self.get_option_at_index(self.highlighted).id

    def cursor_up(self) -> None:
        self.action_cursor_up()

    def cursor_down(self) -> None:
        self.action_cursor_down()


class PromptInput(Input):
    """The chat input, wired to drive an open :class:`CommandMenu`.

    ``on_key`` runs before ``Input``'s own bindings, so intercepting the
    navigation keys here (and stopping them) keeps ⏎/⇥/↑/↓/esc from reaching
    submit, focus-change or interrupt while the dropdown is open.
    """

    def __init__(self, menu: CommandMenu, **kwargs) -> None:
        super().__init__(**kwargs)
        self._menu = menu

    def on_key(self, event: events.Key) -> None:
        if not self._menu.display:
            return
        if event.key == "down":
            self._menu.cursor_down()
        elif event.key == "up":
            self._menu.cursor_up()
        elif event.key == "escape":
            self._menu.display = False
        elif event.key in ("enter", "tab"):
            name = self._menu.selected
            if name is None:
                return
            self.value = f"/{name} "
            self.cursor_position = len(self.value)
            self._menu.display = False
        else:
            return
        event.prevent_default()
        event.stop()
