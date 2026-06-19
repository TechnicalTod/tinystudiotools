"""Material slot name matching for texture assignment."""

from __future__ import annotations

from typing import Dict, FrozenSet, Optional


def material_match_tokens(name: str) -> set[str]:
    tokens: set[str] = set()
    if not name:
        return tokens
    normalized = str(name).strip()
    tokens.add(normalized.lower())
    if "_" in normalized:
        tokens.add(normalized.split("_", 1)[-1].lower())
    for prefix in ("M_", "m_", "MI_", "mi_", "MAT_", "mat_"):
        if normalized.startswith(prefix):
            tokens.add(normalized[len(prefix) :].lower())
    return {token for token in tokens if token}


def slots_equivalent(left: str, right: str) -> bool:
    left_tokens = material_match_tokens(left)
    right_tokens = material_match_tokens(right)
    return bool(left_tokens & right_tokens)


def texture_matches_material_slot(
    texture_name: str,
    slot_name: str,
    *,
    orma_channels_by_slot: Optional[Dict[str, FrozenSet[str]]] = None,
    single_material_slot: bool = False,
) -> bool:
    if single_material_slot:
        return True

    texture_lower = texture_name.lower()
    for token in material_match_tokens(slot_name):
        if token in texture_lower:
            return True

    if orma_channels_by_slot:
        for shader_name in orma_channels_by_slot:
            if not slots_equivalent(shader_name, slot_name):
                continue
            for token in material_match_tokens(shader_name):
                if token in texture_lower:
                    return True
    return False


def lookup_scalar_values_for_slot(
    scalar_values_by_slot: Optional[Dict[str, Dict[str, object]]],
    slot_name: str,
    *,
    single_material_slot: bool = False,
) -> Dict[str, object]:
    if not scalar_values_by_slot:
        return {}
    if single_material_slot and len(scalar_values_by_slot) == 1:
        return dict(next(iter(scalar_values_by_slot.values())))
    if slot_name in scalar_values_by_slot:
        return dict(scalar_values_by_slot[slot_name])
    slot_lower = slot_name.lower()
    for key, values in scalar_values_by_slot.items():
        if key.lower() == slot_lower or slots_equivalent(key, slot_name):
            return dict(values)
    return {}


def lookup_orma_channels_for_slot(
    orma_channels_by_slot: Optional[Dict[str, FrozenSet[str]]],
    slot_name: str,
    *,
    single_material_slot: bool = False,
) -> FrozenSet[str]:
    if not orma_channels_by_slot:
        return frozenset()
    if single_material_slot and len(orma_channels_by_slot) == 1:
        return next(iter(orma_channels_by_slot.values()))
    if slot_name in orma_channels_by_slot:
        return orma_channels_by_slot[slot_name]
    slot_lower = slot_name.lower()
    for key, channels in orma_channels_by_slot.items():
        if key.lower() == slot_lower:
            return channels
    return frozenset()
