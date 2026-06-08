# -*- coding: utf-8 -*-
"""Provider metadata helpers for the TUI model picker.

The TUI stays independent from QwenPaw, but when QwenPaw is installed in the
same environment we can read its provider catalog and persist provider keys
through its public manager. Otherwise we fall back to a small static catalog so
the picker remains useful and ACP can still validate the final model switch.
"""

from __future__ import annotations

import asyncio
import os
from dataclasses import dataclass, field


@dataclass(frozen=True)
class ProviderInfo:
    id: str
    label: str
    configured: bool = False
    models: list[str] = field(default_factory=list)
    env_keys: tuple[str, ...] = ()
    needs_key: bool = True
    source: str = "fallback"


_ENV_KEYS: dict[str, tuple[str, ...]] = {
    "dashscope": ("DASHSCOPE_API_KEY",),
    "modelscope": ("MODELSCOPE_API_KEY",),
    "openai": ("OPENAI_API_KEY",),
    "anthropic": ("ANTHROPIC_API_KEY",),
    "gemini": ("GEMINI_API_KEY", "GOOGLE_API_KEY"),
    "openrouter": ("OPENROUTER_API_KEY",),
    "deepseek": ("DEEPSEEK_API_KEY",),
    "ollama": (),
    "lmstudio": (),
    "qwenpaw-local": (),
}

_FALLBACK_MODELS: dict[str, tuple[str, ...]] = {
    "dashscope": ("qwen3-max", "qwen3-235b-a22b-thinking-2507", "qwen-max"),
    "modelscope": ("Qwen/Qwen3.5-122B-A10B", "ZhipuAI/GLM-5"),
    "openai": ("gpt-5.2", "gpt-5", "gpt-4.1", "gpt-4o"),
    "gemini": ("gemini-2.5-pro", "gemini-2.5-flash", "gemini-2.0-flash"),
    "openrouter": (
        "anthropic/claude-sonnet-4.6",
        "openai/gpt-5.2",
        "google/gemini-3-pro-preview",
    ),
    "deepseek": ("deepseek-v4-pro", "deepseek-chat", "deepseek-reasoner"),
    "ollama": ("llama3.1",),
    "lmstudio": ("local-model",),
    "qwenpaw-local": ("qwenpaw-local",),
}


def _is_configured(provider_id: str, *, needs_key: bool) -> bool:
    if not needs_key:
        return True
    return any(os.getenv(key) for key in _ENV_KEYS.get(provider_id, ()))


def fallback_providers() -> list[ProviderInfo]:
    providers: list[ProviderInfo] = []
    labels = {
        "dashscope": "DashScope",
        "modelscope": "ModelScope",
        "openai": "OpenAI",
        "gemini": "Google Gemini",
        "openrouter": "OpenRouter",
        "deepseek": "DeepSeek",
        "ollama": "Ollama",
        "lmstudio": "LM Studio",
        "qwenpaw-local": "QwenPaw Local",
    }
    for provider_id, models in _FALLBACK_MODELS.items():
        needs_key = bool(_ENV_KEYS.get(provider_id))
        providers.append(
            ProviderInfo(
                id=provider_id,
                label=labels.get(provider_id, provider_id),
                configured=_is_configured(provider_id, needs_key=needs_key),
                models=list(models),
                env_keys=_ENV_KEYS.get(provider_id, ()),
                needs_key=needs_key,
            )
        )
    return providers


async def discover_providers() -> list[ProviderInfo]:
    """Return QwenPaw providers when importable, otherwise a fallback catalog."""
    return await asyncio.to_thread(_discover_providers_sync)


def _discover_providers_sync() -> list[ProviderInfo]:
    try:
        from qwenpaw.providers.provider_manager import ProviderManager
    except Exception:  # noqa: BLE001 - optional dependency
        return fallback_providers()

    try:
        manager = ProviderManager.get_instance()
    except AttributeError:
        manager = ProviderManager()
    except Exception:  # noqa: BLE001
        return fallback_providers()

    async def _list() -> list[object]:
        return await manager.list_provider_info()

    try:
        raw_infos = asyncio.run(_list())
    except Exception:  # noqa: BLE001
        return fallback_providers()

    providers: list[ProviderInfo] = []
    for info in raw_infos:
        provider_id = str(getattr(info, "id", "") or "")
        if not provider_id:
            continue
        models = [
            str(getattr(model, "id", "") or "")
            for model in (
                list(getattr(info, "models", []) or [])
                + list(getattr(info, "extra_models", []) or [])
            )
        ]
        models = [model for model in models if model]
        needs_key = bool(getattr(info, "require_api_key", True))
        api_key = str(getattr(info, "api_key", "") or "")
        providers.append(
            ProviderInfo(
                id=provider_id,
                label=str(getattr(info, "name", "") or provider_id),
                configured=(not needs_key) or bool(api_key),
                models=models or list(_FALLBACK_MODELS.get(provider_id, ())),
                env_keys=_ENV_KEYS.get(provider_id, ()),
                needs_key=needs_key,
                source="qwenpaw",
            )
        )
    return providers or fallback_providers()


async def configure_provider_key(provider_id: str, api_key: str) -> str:
    """Persist a provider API key via QwenPaw when available."""
    api_key = api_key.strip()
    if not api_key:
        raise ValueError("API key is empty")
    return await asyncio.to_thread(
        _configure_provider_key_sync, provider_id, api_key
    )


def _configure_provider_key_sync(provider_id: str, api_key: str) -> str:
    try:
        from qwenpaw.providers.provider_manager import ProviderManager
    except Exception as exc:  # noqa: BLE001
        keys = ", ".join(_ENV_KEYS.get(provider_id, ())) or "the provider key"
        raise RuntimeError(
            "QwenPaw is not importable in this environment; set "
            f"{keys} before starting paw, or install qwenpaw-tui[bundled]."
        ) from exc

    manager = ProviderManager.get_instance()
    if not manager.update_provider(provider_id, {"api_key": api_key}):
        raise RuntimeError(
            f"Provider {provider_id!r} was not found by QwenPaw."
        )
    return f"Saved API key for {provider_id}."


def default_provider(providers: list[ProviderInfo]) -> ProviderInfo:
    for provider in providers:
        if provider.configured and provider.models:
            return provider
    return providers[0]


def default_model(provider: ProviderInfo) -> str:
    return provider.models[0] if provider.models else ""
