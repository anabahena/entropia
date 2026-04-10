"""Difference hash (dHash) and Hamming distance — implemented without imagehash.

Pillow is used only to decode images and read RGB pixels. Resizing and grayscale
are implemented manually.
"""

from __future__ import annotations

import io
from typing import BinaryIO, Sequence

from PIL import Image

DHASH_BITS = 64
DHASH_WIDTH = 9
DHASH_HEIGHT = 8


def _rgb_to_gray_u8(r: int, g: int, b: int) -> int:
    """ITU-R BT.601 luma in fixed-point: Y = 0.299 R + 0.587 G + 0.114 B."""
    return (77 * r + 150 * g + 29 * b) >> 8


def _get_rgb(pixels: Sequence[tuple[int, int, int]], width: int, x: int, y: int) -> tuple[int, int, int]:
    return pixels[y * width + x]


def _bilinear_sample(
    pixels: Sequence[tuple[int, int, int]],
    src_w: int,
    src_h: int,
    sx: float,
    sy: float,
) -> tuple[int, int, int]:
    """Bilinear RGB sample; coordinates clamped to the image."""
    if src_w <= 1 or src_h <= 1:
        return _get_rgb(pixels, src_w, 0, 0)

    sx = min(max(sx, 0.0), float(src_w - 1))
    sy = min(max(sy, 0.0), float(src_h - 1))

    x0 = int(sx)
    y0 = int(sy)
    x1 = min(x0 + 1, src_w - 1)
    y1 = min(y0 + 1, src_h - 1)
    tx = sx - x0
    ty = sy - y0

    c00 = _get_rgb(pixels, src_w, x0, y0)
    c10 = _get_rgb(pixels, src_w, x1, y0)
    c01 = _get_rgb(pixels, src_w, x0, y1)
    c11 = _get_rgb(pixels, src_w, x1, y1)

    def ch(i: int) -> int:
        v00 = c00[i]
        v10 = c10[i]
        v01 = c01[i]
        v11 = c11[i]
        top = v00 + tx * (v10 - v00)
        bot = v01 + tx * (v11 - v01)
        return int(round(top + ty * (bot - top)))

    return ch(0), ch(1), ch(2)


def resize_to_gray_9x8(
    pixels: Sequence[tuple[int, int, int]],
    src_w: int,
    src_h: int,
) -> list[list[int]]:
    """Resize to 9×8 using bilinear sampling, then convert each sample to 8-bit gray."""
    out: list[list[int]] = []
    for oy in range(DHASH_HEIGHT):
        row: list[int] = []
        for ox in range(DHASH_WIDTH):
            sx = (ox + 0.5) * src_w / DHASH_WIDTH - 0.5
            sy = (oy + 0.5) * src_h / DHASH_HEIGHT - 0.5
            r, g, b = _bilinear_sample(pixels, src_w, src_h, sx, sy)
            row.append(_rgb_to_gray_u8(r, g, b))
        out.append(row)
    return out


def _adjacent_horizontal_bits(gray: list[list[int]]) -> list[int]:
    """8×8 comparisons: left pixel greater than right → 1, else 0 (row-major)."""
    bits: list[int] = []
    for y in range(DHASH_HEIGHT):
        for x in range(DHASH_WIDTH - 1):
            bits.append(1 if gray[y][x] > gray[y][x + 1] else 0)
    assert len(bits) == DHASH_BITS
    return bits


def bits_to_hex64(bits: Sequence[int]) -> str:
    """Pack 64 bits into a 16-character hex string (first bit → MSB of 64-bit value)."""
    if len(bits) != DHASH_BITS:
        raise ValueError(f"expected {DHASH_BITS} bits, got {len(bits)}")
    n = 0
    for i, b in enumerate(bits):
        if b:
            n |= 1 << (DHASH_BITS - 1 - i)
    return f"{n:016x}"


def dhash_from_gray_9x8(gray: list[list[int]]) -> str:
    """Steps 3–5: compare adjacent pixels, binary hash, hex string."""
    bits = _adjacent_horizontal_bits(gray)
    return bits_to_hex64(bits)


def dhash_from_rgb_pixels(
    pixels: Sequence[tuple[int, int, int]],
    width: int,
    height: int,
) -> str:
    """Full pipeline from raw RGB pixels (steps 1–5)."""
    gray = resize_to_gray_9x8(pixels, width, height)
    return dhash_from_gray_9x8(gray)


def dhash_from_pillow_image(image: Image.Image) -> str:
    """Read pixels with Pillow only; resize and grayscale are manual."""
    rgb = image.convert("RGB")
    w, h = rgb.size
    pixels = rgb.getdata()
    return dhash_from_rgb_pixels(list(pixels), w, h)


def dhash_from_bytes(data: bytes) -> str:
    """Decode image bytes with Pillow, then compute dHash."""
    with Image.open(io.BytesIO(data)) as img:
        return dhash_from_pillow_image(img)


def dhash_from_file(fp: BinaryIO) -> str:
    with Image.open(fp) as img:
        return dhash_from_pillow_image(img)


def hamming_distance_hex(a: str, b: str) -> int:
    """Hamming distance between two equal-length dHash hex strings."""
    if len(a) != len(b):
        raise ValueError("hex strings must have the same length")
    ai = int(a, 16)
    bi = int(b, 16)
    return (ai ^ bi).bit_count()


def hamming_distance_int(a: int, b: int) -> int:
    """Hamming distance between two 64-bit hashes."""
    return (a ^ b).bit_count()
