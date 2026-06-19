"""Pack AO/Roughness/Metallic/Opacity channels into one ORMA PNG."""

from __future__ import annotations

import os
from typing import Optional

from .png_io import read_png_as_grayscale, resize_grayscale, write_png_rgba


def _load_grayscale_channel(
    texture_path: Optional[str],
    default_value: int,
    default_size: Optional[tuple[int, int]],
):
    import numpy as np

    if texture_path:
        channel = read_png_as_grayscale(texture_path)
        if default_size is None:
            default_size = (channel.shape[1], channel.shape[0])
        else:
            channel = resize_grayscale(channel, default_size)
        return channel, default_size
    if default_size is None:
        return None, default_size
    width, height = default_size
    return np.full((height, width), default_value, dtype=np.uint8), default_size


def create_orma_texture(
    *,
    occlusion_path: Optional[str] = None,
    roughness_path: Optional[str] = None,
    metallic_path: Optional[str] = None,
    alpha_path: Optional[str] = None,
) -> str:
    """Pack AO/Roughness/Metallic/Opacity channels into one ORMA PNG on disk."""
    import numpy as np

    default_size = None
    for texture_path in (occlusion_path, roughness_path, metallic_path, alpha_path):
        if texture_path:
            sample = read_png_as_grayscale(texture_path)
            default_size = (sample.shape[1], sample.shape[0])
            break

    if default_size is None:
        raise ValueError(
            "Default size cannot be determined. At least one valid ORMA texture is required."
        )

    occlusion, default_size = _load_grayscale_channel(occlusion_path, 0, default_size)
    roughness, default_size = _load_grayscale_channel(roughness_path, 128, default_size)
    metallic, default_size = _load_grayscale_channel(metallic_path, 0, default_size)
    alpha, default_size = _load_grayscale_channel(alpha_path, 255, default_size)

    orma_texture = np.stack((occlusion, roughness, metallic, alpha), axis=-1)

    valid_path = occlusion_path or roughness_path or metallic_path or alpha_path
    if not valid_path:
        raise ValueError("No valid texture paths found for determining ORMA output name.")

    base_name = os.path.splitext(os.path.basename(valid_path))[0]
    base_name = "_".join(base_name.split("_")[:-1])
    output_name = "{}_ORMA.1001.png".format(base_name)
    output_path = os.path.join(os.path.dirname(valid_path), output_name)
    write_png_rgba(output_path, orma_texture)
    return output_path
