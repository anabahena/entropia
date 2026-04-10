import hashlib
from pathlib import Path

from fastapi import HTTPException, UploadFile

from app.core.config import settings


def _normalize_mime(content_type: str | None) -> str | None:
    if not content_type:
        return None
    return content_type.split(";", 1)[0].strip().lower()


def validate_image_mime(content_type: str | None) -> None:
    mime = _normalize_mime(content_type)
    if mime not in settings.allowed_image_mime_types:
        raise HTTPException(
            status_code=415,
            detail="Tipo de archivo no soportado; permitidos: image/jpeg, image/png, image/webp, image/gif",
        )


async def read_upload_limited(upload: UploadFile, max_bytes: int) -> bytes:
    chunks: list[bytes] = []
    total = 0
    while True:
        chunk = await upload.read(64 * 1024)
        if not chunk:
            break
        total += len(chunk)
        if total > max_bytes:
            raise HTTPException(
                status_code=413,
                detail=f"El archivo supera el tamaño máximo de {max_bytes} bytes",
            )
        chunks.append(chunk)
    data = b"".join(chunks)
    if not data:
        raise HTTPException(status_code=400, detail="Archivo vacío")
    return data


def sha256_hex(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def stored_file_path(sha256_hex: str) -> Path:
    return Path(settings.upload_dir) / sha256_hex


def image_path_for_api(sha256_hex: str) -> str:
    """Public path for URLs: ``{host}/uploads/...`` (matches StaticFiles mount)."""
    wd = Path(settings.upload_dir)
    full = wd / sha256_hex
    rel = full.relative_to(wd.parent)
    return f"{wd.parent.name}/{rel.as_posix()}"


def save_image(data: bytes, sha256_hex: str) -> Path:
    path = stored_file_path(sha256_hex)
    path.parent.mkdir(parents=True, exist_ok=True)
    try:
        with path.open("xb") as f:
            f.write(data)
    except FileExistsError:
        raise HTTPException(
            status_code=409,
            detail="Imagen duplicada: el mismo SHA-256 ya fue almacenado",
        ) from None
    return path
