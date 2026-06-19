"""M_Master_Standard material instance parameter wiring."""

from __future__ import annotations

from typing import FrozenSet, List

import unreal


def orma_switch_name(channel: str) -> str:
    if channel == "metallic":
        return "Use Metalness Texture?"
    if channel == "ao":
        return "Use AO?"
    return "Use {} Texture?".format(channel.capitalize())


def set_material_instance_toggle(
    material_instance: unreal.MaterialInstanceConstant,
    parameter_name: str,
    enabled: bool,
) -> None:
    """Enable a material instance toggle via static switch or scalar bool fallback."""
    mel = unreal.MaterialEditingLibrary
    try:
        mel.set_material_instance_static_switch_parameter_value(
            material_instance,
            parameter_name,
            enabled,
        )
        return
    except Exception:
        pass

    try:
        mel.set_material_instance_scalar_parameter_value(
            material_instance,
            parameter_name,
            1.0 if enabled else 0.0,
        )
    except Exception as exc:
        unreal.log_warning(
            "Could not set material toggle '{}' on {}: {}".format(
                parameter_name,
                material_instance.get_name(),
                exc,
            )
        )


def set_material_instance_texture(
    material_instance: unreal.MaterialInstanceConstant,
    candidate_names: List[str],
    texture: unreal.Texture,
) -> bool:
    mel = unreal.MaterialEditingLibrary
    for parameter_name in candidate_names:
        try:
            mel.set_material_instance_texture_parameter_value(
                material_instance,
                parameter_name,
                texture,
            )
            return True
        except Exception:
            continue
    unreal.log_warning(
        "Could not assign texture {} to {} (tried: {})".format(
            texture.get_name(),
            material_instance.get_name(),
            ", ".join(candidate_names),
        )
    )
    return False


def classify_texture_map(texture_name: str) -> str:
    lower = texture_name.lower()
    if "_orma" in lower:
        return "orma"
    if "diffuse" in lower or "albedo" in lower:
        return "albedo"
    if lower.endswith("_d") or ".d." in lower or "_d." in lower:
        return "albedo"

    suffix = texture_name.rsplit("_", 1)[-1].lower()
    suffix = suffix.split(".", 1)[0]
    suffix_map = {
        "d": "albedo",
        "diffuse": "albedo",
        "albedo": "albedo",
        "n": "normal",
        "normal": "normal",
        "ao": "ao",
        "roughness": "roughness",
        "metallic": "metallic",
        "metalness": "metallic",
        "opacity": "opacity",
        "emissive": "emissive",
    }
    return suffix_map.get(suffix, suffix)


def apply_orma_texture_to_material_instance(
    material_instance: unreal.MaterialInstanceConstant,
    texture: unreal.Texture,
    *,
    orma_channels: FrozenSet[str],
) -> None:
    vt_suffix = ""
    if texture.get_editor_property("virtual_texture_streaming"):
        vt_suffix = " VT"
        set_material_instance_toggle(material_instance, "Use VT", True)

    texture.set_editor_property("srgb", False)
    set_material_instance_texture(
        material_instance,
        ["Packed ORMA" + vt_suffix, "Packed ORMA"],
        texture,
    )

    for channel in orma_channels:
        set_material_instance_toggle(material_instance, orma_switch_name(channel), True)


def set_material_instance_vector(
    material_instance: unreal.MaterialInstanceConstant,
    candidate_names: List[str],
    linear_color: unreal.LinearColor,
) -> bool:
    mel = unreal.MaterialEditingLibrary
    for parameter_name in candidate_names:
        try:
            mel.set_material_instance_vector_parameter_value(
                material_instance,
                parameter_name,
                linear_color,
            )
            return True
        except Exception:
            continue
    return False


def set_material_instance_scalar(
    material_instance: unreal.MaterialInstanceConstant,
    candidate_names: List[str],
    value: float,
) -> bool:
    mel = unreal.MaterialEditingLibrary
    for parameter_name in candidate_names:
        try:
            mel.set_material_instance_scalar_parameter_value(
                material_instance,
                parameter_name,
                value,
            )
            return True
        except Exception:
            continue
    return False


def apply_scalar_values_to_material_instance(
    material_instance: unreal.MaterialInstanceConstant,
    scalar_values: dict,
) -> None:
    if "albedo_color" in scalar_values:
        red, green, blue = scalar_values["albedo_color"][:3]
        set_material_instance_vector(
            material_instance,
            ["Albedo Colour", "Albedo Color"],
            unreal.LinearColor(float(red), float(green), float(blue), 1.0),
        )

    if "emissive_color" in scalar_values:
        red, green, blue = scalar_values["emissive_color"][:3]
        set_material_instance_vector(
            material_instance,
            ["Emissive Colour", "Emissive Color", "Emissive"],
            unreal.LinearColor(float(red), float(green), float(blue), 1.0),
        )

    if "metallic" in scalar_values:
        set_material_instance_scalar(
            material_instance,
            ["Metalness Scalar", "Metallic Scalar", "Metalness"],
            float(scalar_values["metallic"]),
        )

    if "roughness" in scalar_values:
        set_material_instance_scalar(
            material_instance,
            ["Roughness Scalar", "Roughness"],
            float(scalar_values["roughness"]),
        )


def apply_texture_to_material_instance(
    material_instance: unreal.MaterialInstanceConstant,
    texture: unreal.Texture,
) -> None:
    texture_name = texture.get_name()
    map_kind = classify_texture_map(texture_name)

    vt_suffix = ""
    if texture.get_editor_property("virtual_texture_streaming"):
        vt_suffix = " VT"
        set_material_instance_toggle(material_instance, "Use VT", True)

    if map_kind == "albedo":
        texture.set_editor_property("srgb", True)
        set_material_instance_toggle(material_instance, "Use Albedo Texture?", True)
        set_material_instance_texture(
            material_instance,
            ["Albedo" + vt_suffix, "Albedo", "Albedo Texture" + vt_suffix, "Albedo Texture"],
            texture,
        )
        return

    if map_kind == "ao":
        switch_name = "Use AO?"
        param_names = ["AO" + vt_suffix, "AO"]
    elif map_kind in ("metallic", "metalness"):
        switch_name = "Use Metalness Texture?"
        param_names = ["Metalness" + vt_suffix, "Metalness"]
    elif map_kind == "normal":
        switch_name = "Use Normal Texture?"
        param_names = ["Normal" + vt_suffix, "Normal"]
    elif map_kind == "roughness":
        switch_name = "Use Roughness Texture?"
        param_names = ["Roughness" + vt_suffix, "Roughness"]
    elif map_kind == "opacity":
        switch_name = "Use Opacity Texture?"
        param_names = ["Opacity" + vt_suffix, "Opacity"]
    elif map_kind == "emissive":
        switch_name = "Use Emissive Texture?"
        param_names = ["Emissive" + vt_suffix, "Emissive"]
    else:
        label = map_kind.capitalize()
        switch_name = "Use {} Texture?".format(label)
        param_names = [label + vt_suffix, label]

    if map_kind in ("ao", "metallic", "metalness", "roughness", "opacity", "normal"):
        texture.set_editor_property("srgb", False)

    set_material_instance_toggle(material_instance, switch_name, True)
    set_material_instance_texture(material_instance, param_names, texture)
