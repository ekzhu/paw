# -*- coding: utf-8 -*-
"""Model/provider selection screens."""

from __future__ import annotations

from rich.markup import escape
from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import Horizontal, Vertical
from textual.screen import ModalScreen
from textual.widgets import Button, Input, Label, ListItem, ListView, Static

from ..providers import ProviderInfo, default_model


class ModelPicker(ModalScreen[tuple[str, str] | None]):
    """Two-column provider/model picker."""

    BINDINGS = [Binding("escape", "cancel", "Cancel")]

    CSS = """
    ModelPicker {
        align: center middle;
        background: transparent;
    }
    #model-modal {
        width: 70%;
        height: 28;
        background: #182433;
        border: thick #68d391;
    }
    #model-modal-title {
        height: 1;
        padding: 0 1;
        background: #21463c;
        color: #f4fff8;
    }
    #model-modal-body { height: 1fr; }
    #provider-column {
        width: 28;
        border-right: solid #68d391;
    }
    #model-column { width: 1fr; }
    .column-title {
        height: 1;
        padding: 0 1;
        background: #223042;
        color: #b8f7d0;
    }
    #provider-list, #model-list { height: 1fr; }
    #model-search { margin: 0 1; }
    #model-help {
        height: 2;
        padding: 0 1;
        color: #9fb0c2;
    }
    """

    def __init__(
        self,
        providers: list[ProviderInfo],
        selected_provider: str,
        selected_model: str,
    ) -> None:
        super().__init__()
        self.providers = providers
        provider_ids = {info.id for info in providers}
        if providers and selected_provider not in provider_ids:
            selected_provider = providers[0].id
            selected_model = default_model(providers[0])
        self.selected_provider = selected_provider
        self.selected_model = selected_model
        self.model_item_ids: dict[str, str] = {}

    def compose(self) -> ComposeResult:
        with Vertical(id="model-modal"):
            yield Static("Choose model", id="model-modal-title")
            with Horizontal(id="model-modal-body"):
                with Vertical(id="provider-column"):
                    yield Static("Provider", classes="column-title")
                    yield ListView(*self._provider_items(), id="provider-list")
                with Vertical(id="model-column"):
                    yield Static("Model", classes="column-title")
                    yield Input(placeholder="Search models", id="model-search")
                    yield ListView(*self._model_items(), id="model-list")
                    yield Static(
                        "Enter selects. Providers marked 'needs key' can be "
                        "configured with /providers.",
                        id="model-help",
                    )

    async def on_mount(self) -> None:
        self.query_one("#provider-list", ListView).index = (
            self._provider_index(self.selected_provider)
        )
        self.query_one("#model-list", ListView).index = self._model_index(
            self.selected_model
        )
        self.query_one("#model-search", Input).focus()

    async def on_input_changed(self, event: Input.Changed) -> None:
        if event.input.id != "model-search":
            return
        event.stop()
        await self._refresh_model_list(event.value)

    async def on_input_submitted(self, event: Input.Submitted) -> None:
        if event.input.id != "model-search":
            return
        event.stop()
        self._select_highlighted_model()

    async def on_list_view_selected(self, event: ListView.Selected) -> None:
        event.stop()
        if event.list_view.id == "provider-list":
            provider_id = event.item.id.removeprefix("provider-")
            if provider_id != self.selected_provider:
                self.selected_provider = provider_id
                self.selected_model = default_model(
                    self._provider_info(provider_id)
                )
                self.query_one("#model-search", Input).value = ""
                await self._refresh_model_list("")
            return
        if event.list_view.id == "model-list":
            self._select_highlighted_model()

    def action_cancel(self) -> None:
        self.dismiss(None)

    def _select_highlighted_model(self) -> None:
        model_list = self.query_one("#model-list", ListView)
        item = model_list.highlighted_child
        if item and item.id in self.model_item_ids:
            self.dismiss(
                (self.selected_provider, self.model_item_ids[item.id])
            )

    async def _refresh_model_list(self, query: str) -> None:
        model_list = self.query_one("#model-list", ListView)
        await model_list.clear()
        for item in self._model_items(query):
            await model_list.append(item)
        model_list.index = 0 if model_list.children else None

    def _provider_items(self) -> list[ListItem]:
        items = []
        for info in self.providers:
            suffix = "" if info.configured else " (needs key)"
            label = f"{info.label}{suffix}"
            items.append(ListItem(Label(label), id=f"provider-{info.id}"))
        return items

    def _model_items(self, query: str = "") -> list[ListItem]:
        info = self._provider_info(self.selected_provider)
        needle = query.casefold().strip()
        models = [model for model in info.models if needle in model.casefold()]
        self.model_item_ids = {}
        if not models:
            return [ListItem(Label("No models match"), disabled=True)]
        items = []
        for index, model in enumerate(models):
            item_id = f"model-{index}"
            self.model_item_ids[item_id] = model
            items.append(ListItem(Label(model), id=item_id))
        return items

    def _provider_info(self, provider_id: str) -> ProviderInfo:
        return next(
            (info for info in self.providers if info.id == provider_id),
            self.providers[0],
        )

    def _provider_index(self, provider_id: str) -> int:
        return next(
            (
                index
                for index, info in enumerate(self.providers)
                if info.id == provider_id
            ),
            0,
        )

    def _model_index(self, model: str) -> int:
        info = self._provider_info(self.selected_provider)
        return next(
            (
                index
                for index, model_name in enumerate(info.models)
                if model_name == model
            ),
            0,
        )


class ProviderSetup(ModalScreen[tuple[str, str, str] | None]):
    """Collect a provider key and optional model in the TUI."""

    BINDINGS = [Binding("escape", "cancel", "Cancel")]

    CSS = """
    ProviderSetup {
        align: center middle;
        background: transparent;
    }
    #provider-setup {
        width: 66%;
        height: auto;
        background: #182433;
        border: thick #ffcf6d;
        padding: 1 2;
    }
    #provider-setup-title {
        height: 1;
        color: #ffdf93;
    }
    .provider-field {
        margin-top: 1;
    }
    #provider-buttons {
        height: auto;
        margin-top: 1;
    }
    #provider-help {
        height: auto;
        color: #9fb0c2;
        margin-top: 1;
    }
    """

    def __init__(
        self,
        providers: list[ProviderInfo],
        selected_provider: str,
        selected_model: str,
    ) -> None:
        super().__init__()
        self.providers = providers
        self.selected_provider = selected_provider
        self.selected_model = selected_model

    def compose(self) -> ComposeResult:
        env_hint = self._env_hint(self.selected_provider)
        with Vertical(id="provider-setup"):
            yield Static("Configure provider", id="provider-setup-title")
            yield Input(
                value=self.selected_provider,
                placeholder="provider id, e.g. dashscope",
                id="setup-provider",
                classes="provider-field",
            )
            yield Input(
                placeholder=f"API key{env_hint}",
                password=True,
                id="setup-key",
                classes="provider-field",
            )
            yield Input(
                value=self.selected_model,
                placeholder="model id, optional",
                id="setup-model",
                classes="provider-field",
            )
            with Horizontal(id="provider-buttons"):
                yield Button("Save", id="save-provider", variant="primary")
                yield Button("Cancel", id="cancel-provider")
            yield Static(
                "Keys are saved through QwenPaw when it is importable. "
                "The model field is applied to this session after save.",
                id="provider-help",
            )

    async def on_mount(self) -> None:
        self.query_one("#setup-key", Input).focus()

    async def on_button_pressed(self, event: Button.Pressed) -> None:
        event.stop()
        if event.button.id == "cancel-provider":
            self.dismiss(None)
            return
        provider = self.query_one("#setup-provider", Input).value.strip()
        key = self.query_one("#setup-key", Input).value.strip()
        model = self.query_one("#setup-model", Input).value.strip()
        self.dismiss((provider, key, model))

    def action_cancel(self) -> None:
        self.dismiss(None)

    def _env_hint(self, provider_id: str) -> str:
        info = next(
            (
                provider
                for provider in self.providers
                if provider.id == provider_id
            ),
            None,
        )
        if info is None or not info.env_keys:
            return ""
        return f" ({escape(' or '.join(info.env_keys))})"
