import io

from PIL import Image

from app.utils.dhash import dhash_from_bytes, hamming_distance_hex


def _png_bytes(img: Image.Image) -> bytes:
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()


def test_same_image_identical_perceptual_hash():
    img = Image.new("RGB", (40, 40), (90, 120, 140))
    blob = _png_bytes(img)
    h1 = dhash_from_bytes(blob)
    h2 = dhash_from_bytes(blob)
    assert h1 == h2
    assert hamming_distance_hex(h1, h2) == 0


def test_similar_images_low_hamming_distance():
    """Nearly identical images should stay close in dHash space."""
    base = Image.new("RGB", (48, 48), (100, 110, 120))
    near = base.copy()
    near.putpixel((0, 0), (101, 110, 120))
    near.putpixel((1, 1), (100, 111, 120))

    ha = dhash_from_bytes(_png_bytes(base))
    hb = dhash_from_bytes(_png_bytes(near))
    dist = hamming_distance_hex(ha, hb)

    assert dist < 20


def test_different_images_higher_hamming_than_similar_pair():
    """Unrelated scenes should differ more than a near-duplicate pair."""
    base = Image.new("RGB", (48, 48), (100, 110, 120))
    near = base.copy()
    near.putpixel((0, 0), (105, 110, 120))

    unrelated = Image.new("RGB", (48, 48), (0, 255, 0))

    d_similar = hamming_distance_hex(
        dhash_from_bytes(_png_bytes(base)),
        dhash_from_bytes(_png_bytes(near)),
    )
    d_different = hamming_distance_hex(
        dhash_from_bytes(_png_bytes(base)),
        dhash_from_bytes(_png_bytes(unrelated)),
    )

    assert d_similar <= d_different
