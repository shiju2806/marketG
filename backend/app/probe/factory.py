"""Probe target factory — return the requested targets that actually have keys."""
from __future__ import annotations

from app.config import settings
from app.probe.base import ProbeTarget
from app.probe.providers import ChatGPTProbe, ClaudeProbe, PerplexityProbe

_KEY = {
    "chatgpt": lambda: bool(settings.openai_api_key),
    "claude": lambda: bool(settings.anthropic_api_key),
    "perplexity": lambda: bool(settings.perplexity_api_key),
}
_CTOR = {"chatgpt": ChatGPTProbe, "claude": ClaudeProbe, "perplexity": PerplexityProbe}


def available_targets(requested: list[str] | None = None) -> list[ProbeTarget]:
    names = requested or [t.strip() for t in settings.probe_targets.split(",") if t.strip()]
    return [_CTOR[n]() for n in names if n in _CTOR and _KEY[n]()]
