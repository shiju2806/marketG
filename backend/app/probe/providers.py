"""Concrete probe targets: ChatGPT (OpenAI), Claude (Anthropic), Perplexity.

Only targets whose API key is set are usable; the factory filters accordingly.
Perplexity is the browsing/citation-oriented one and returns real cited sources.
"""
from __future__ import annotations

import httpx

from app.config import settings
from app.probe.base import ProbeAnswer

_SYSTEM = "Answer the user's question concisely, as a helpful assistant would."


class ChatGPTProbe:
    name = "chatgpt"

    async def ask(self, question: str) -> ProbeAnswer:
        async with httpx.AsyncClient() as client:
            resp = await client.post(
                "https://api.openai.com/v1/chat/completions",
                headers={"Authorization": f"Bearer {settings.openai_api_key}"},
                json={
                    "model": settings.openai_llm_model,
                    "messages": [
                        {"role": "system", "content": _SYSTEM},
                        {"role": "user", "content": question},
                    ],
                },
                timeout=60.0,
            )
            resp.raise_for_status()
            data = resp.json()
        text = data["choices"][0]["message"]["content"]
        u = data.get("usage", {})
        cost = round(
            u.get("prompt_tokens", 0) / 1_000_000 * 0.15
            + u.get("completion_tokens", 0) / 1_000_000 * 0.60, 6
        )
        return ProbeAnswer(text=text, tokens=u.get("total_tokens", 0), cost_usd=cost)


class ClaudeProbe:
    name = "claude"

    async def ask(self, question: str) -> ProbeAnswer:
        async with httpx.AsyncClient() as client:
            resp = await client.post(
                "https://api.anthropic.com/v1/messages",
                headers={
                    "x-api-key": settings.anthropic_api_key,
                    "anthropic-version": "2023-06-01",
                    "content-type": "application/json",
                },
                json={
                    "model": settings.anthropic_model,
                    "max_tokens": 512,
                    "system": _SYSTEM,
                    "messages": [{"role": "user", "content": question}],
                },
                timeout=60.0,
            )
            resp.raise_for_status()
            data = resp.json()
        text = "".join(b.get("text", "") for b in data.get("content", []))
        u = data.get("usage", {})
        cost = round(
            u.get("input_tokens", 0) / 1_000_000 * 3.0
            + u.get("output_tokens", 0) / 1_000_000 * 15.0, 6
        )
        return ProbeAnswer(
            text=text, tokens=u.get("input_tokens", 0) + u.get("output_tokens", 0), cost_usd=cost
        )


class PerplexityProbe:
    name = "perplexity"

    async def ask(self, question: str) -> ProbeAnswer:
        async with httpx.AsyncClient() as client:
            resp = await client.post(
                "https://api.perplexity.ai/chat/completions",
                headers={"Authorization": f"Bearer {settings.perplexity_api_key}"},
                json={
                    "model": settings.perplexity_model,
                    "messages": [
                        {"role": "system", "content": _SYSTEM},
                        {"role": "user", "content": question},
                    ],
                },
                timeout=60.0,
            )
            resp.raise_for_status()
            data = resp.json()
        text = data["choices"][0]["message"]["content"]
        citations = data.get("citations", []) or []
        u = data.get("usage", {})
        return ProbeAnswer(text=text, cited_sources=list(citations), tokens=u.get("total_tokens", 0))
