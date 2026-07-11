"""Vertical pack registry — resolve a pack by an organization's vertical_pack_id."""
from __future__ import annotations

from app.verticals.automotive import AUTOMOTIVE
from app.verticals.base import VerticalPack

_PACKS: dict[str, VerticalPack] = {
    AUTOMOTIVE.pack_id: AUTOMOTIVE,
}


def get_vertical_pack(pack_id: str) -> VerticalPack:
    """Return the pack, falling back to automotive (the MVP default)."""
    return _PACKS.get(pack_id, AUTOMOTIVE)


def register_pack(pack: VerticalPack) -> None:
    _PACKS[pack.pack_id] = pack
