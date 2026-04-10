import io

from PIL import Image


def _make_png_bytes() -> bytes:
    buf = io.BytesIO()
    Image.new("RGB", (24, 24), (200, 50, 80)).save(buf, format="PNG")
    return buf.getvalue()


def test_upload_returns_201_and_body(client):
    png = _make_png_bytes()
    res = client.post(
        "/api/windows",
        files={"image": ("w.png", io.BytesIO(png), "image/png")},
    )
    assert res.status_code == 201
    body = res.json()
    assert "id" in body
    assert "sha256" in body
    assert "path" in body
    assert body["path"].startswith("uploads/windows/")
    assert res.headers.get("X-Entropia-Version") == "3.2.0"


def test_upload_duplicate_returns_409(client):
    png = _make_png_bytes()
    r1 = client.post(
        "/api/windows",
        files={"image": ("a.png", io.BytesIO(png), "image/png")},
    )
    assert r1.status_code == 201

    r2 = client.post(
        "/api/windows",
        files={"image": ("b.png", io.BytesIO(png), "image/png")},
    )
    assert r2.status_code == 409
    assert "detail" in r2.json()


def test_upload_rejects_non_image_mime(client):
    res = client.post(
        "/api/windows",
        files={
            "image": (
                "x.bin",
                io.BytesIO(b"not-an-image"),
                "application/octet-stream",
            )
        },
    )
    assert res.status_code == 415
