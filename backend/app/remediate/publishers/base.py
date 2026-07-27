"""Publisher seam — where a generated fix goes.

v1 has only ExportPublisher (download/copy). CMS adapters (WordPress, Webflow, AEM)
implement the same protocol so "push to your site" is a drop-in later — the
workflow integration that builds switching costs.
"""
from __future__ import annotations

import json
from typing import Protocol


class Publisher(Protocol):
    name: str

    async def publish(self, artifact: dict) -> dict:
        ...


class ExportPublisher:
    """No-integration publisher: returns the artifact in downloadable formats."""

    name = "export"

    async def publish(self, artifact: dict) -> dict:
        return {
            "publisher": self.name,
            "formats": {
                "markdown": artifact.get("body_markdown", ""),
                "html": artifact.get("body_html", ""),
                "schema_json": json.dumps(artifact.get("schema_jsonld", {}), indent=2),
            },
        }


# CMS adapters go here later, e.g.:
# class WordPressPublisher: name = "wordpress"; async def publish(...): POST to WP REST API
