"""PNG read/write for ORMA packing without Pillow."""

from __future__ import annotations

import struct
import zlib


def _paeth_predictor(left: int, up: int, up_left: int) -> int:
    p = left + up - up_left
    pa = abs(p - left)
    pb = abs(p - up)
    pc = abs(p - up_left)
    if pa <= pb and pa <= pc:
        return left
    if pb <= pc:
        return up
    return up_left


def _unfilter_png_rows(raw: bytes, width: int, height: int, bytes_per_pixel: int) -> bytes:
    stride = width * bytes_per_pixel
    output = bytearray(height * stride)
    previous = bytearray(stride)
    offset = 0
    for row in range(height):
        filter_type = raw[offset]
        offset += 1
        current = bytearray(raw[offset : offset + stride])
        offset += stride

        if filter_type == 1:
            for col in range(bytes_per_pixel, stride):
                current[col] = (current[col] + current[col - bytes_per_pixel]) & 0xFF
        elif filter_type == 2:
            for col in range(stride):
                current[col] = (current[col] + previous[col]) & 0xFF
        elif filter_type == 3:
            for col in range(stride):
                left = current[col - bytes_per_pixel] if col >= bytes_per_pixel else 0
                up = previous[col]
                current[col] = (current[col] + ((left + up) // 2)) & 0xFF
        elif filter_type == 4:
            for col in range(stride):
                left = current[col - bytes_per_pixel] if col >= bytes_per_pixel else 0
                up = previous[col]
                up_left = previous[col - bytes_per_pixel] if col >= bytes_per_pixel else 0
                current[col] = (current[col] + _paeth_predictor(left, up, up_left)) & 0xFF

        output[row * stride : (row + 1) * stride] = current
        previous = current
    return bytes(output)


def read_png_as_grayscale(path: str):
    """Read an 8-bit PNG as a grayscale ``numpy`` array with shape ``(height, width)``."""
    import numpy as np

    with open(path, "rb") as handle:
        data = handle.read()
    if data[:8] != b"\x89PNG\r\n\x1a\n":
        raise ValueError("Not a PNG file: {}".format(path))

    width = height = None
    bit_depth = color_type = None
    idat = bytearray()
    offset = 8
    while offset + 8 <= len(data):
        chunk_length = struct.unpack(">I", data[offset : offset + 4])[0]
        chunk_type = data[offset + 4 : offset + 8]
        chunk_data = data[offset + 8 : offset + 8 + chunk_length]
        offset += 12 + chunk_length

        if chunk_type == b"IHDR":
            width, height, bit_depth, color_type, _, _, _ = struct.unpack(
                ">IIBBBBB", chunk_data
            )
        elif chunk_type == b"IDAT":
            idat.extend(chunk_data)

    if width is None or height is None:
        raise ValueError("PNG missing IHDR chunk: {}".format(path))
    if bit_depth != 8:
        raise ValueError("Only 8-bit PNG textures are supported: {}".format(path))

    bytes_per_pixel = {0: 1, 2: 3, 6: 4}.get(color_type)
    if bytes_per_pixel is None:
        raise ValueError("Unsupported PNG color type {} in {}".format(color_type, path))

    filtered = zlib.decompress(bytes(idat))
    pixels = _unfilter_png_rows(filtered, width, height, bytes_per_pixel)
    array = np.frombuffer(pixels, dtype=np.uint8)

    if color_type == 0:
        return array.reshape(height, width)
    if color_type == 2:
        rgb = array.reshape(height, width, 3).astype(np.float32)
        return (
            0.299 * rgb[:, :, 0] + 0.587 * rgb[:, :, 1] + 0.114 * rgb[:, :, 2]
        ).astype(np.uint8)
    rgba = array.reshape(height, width, 4).astype(np.float32)
    return (0.299 * rgba[:, :, 0] + 0.587 * rgba[:, :, 1] + 0.114 * rgba[:, :, 2]).astype(
        np.uint8
    )


def resize_grayscale(array, size: tuple[int, int]):
    import numpy as np

    target_width, target_height = size
    height, width = array.shape
    if (width, height) == (target_width, target_height):
        return array

    y_scale = height / target_height
    x_scale = width / target_width
    y_idx = np.minimum((np.arange(target_height) * y_scale).astype(int), height - 1)
    x_idx = np.minimum((np.arange(target_width) * x_scale).astype(int), width - 1)
    return array[y_idx[:, None], x_idx[None, :]]


def write_png_rgba(path: str, rgba) -> None:
    import numpy as np

    if rgba.dtype != np.uint8:
        rgba = rgba.astype(np.uint8)
    height, width, _ = rgba.shape
    raw = bytearray()
    row_bytes = width * 4
    flat = rgba.reshape(-1)
    for row in range(height):
        raw.append(0)
        start = row * row_bytes
        raw.extend(flat[start : start + row_bytes].tobytes())

    compressed = zlib.compress(bytes(raw), 9)

    def _chunk(tag: bytes, payload: bytes) -> bytes:
        crc = zlib.crc32(tag + payload) & 0xFFFFFFFF
        return struct.pack(">I", len(payload)) + tag + payload + struct.pack(">I", crc)

    ihdr = struct.pack(">IIBBBBB", width, height, 8, 6, 0, 0, 0)
    png = b"\x89PNG\r\n\x1a\n" + _chunk(b"IHDR", ihdr) + _chunk(b"IDAT", compressed) + _chunk(
        b"IEND", b""
    )
    with open(path, "wb") as handle:
        handle.write(png)
