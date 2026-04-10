from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.database import get_db
from app.models.window import Window
from app.schemas.windows import (
    SimilarWindowsResponse,
    SimilarWindowItem,
    WindowListItem,
    WindowUploadResponse,
)
from app.services import window_storage
from app.utils.dhash import dhash_from_bytes, hamming_distance_hex

router = APIRouter()


@router.get("/windows", response_model=list[WindowListItem])
def list_windows(db: Session = Depends(get_db)) -> list[WindowListItem]:
    rows = (
        db.execute(select(Window).order_by(Window.created_at.desc()))
        .scalars()
        .all()
    )
    return [WindowListItem.model_validate(r) for r in rows]


@router.get(
    "/windows/{window_id}/similar",
    response_model=SimilarWindowsResponse,
)
def list_similar_windows(
    window_id: int,
    threshold: int = Query(
        64,
        ge=0,
        le=64,
        description="Incluye otras ventanas cuya distancia de Hamming del dHash respecto a la referencia sea como máximo este valor.",
    ),
    db: Session = Depends(get_db),
) -> SimilarWindowsResponse:
    ref = db.get(Window, window_id)
    if ref is None:
        raise HTTPException(status_code=404, detail="Ventana no encontrada")

    others = db.execute(select(Window).where(Window.id != window_id)).scalars().all()
    scored: list[tuple[int, Window]] = []
    for w in others:
        dist = hamming_distance_hex(ref.perceptual_hash, w.perceptual_hash)
        if dist <= threshold:
            scored.append((dist, w))

    scored.sort(key=lambda t: (t[0], t[1].id))
    items = [
        SimilarWindowItem(
            id=w.id,
            hamming_distance=d,
            sha256=w.sha256,
            image_path=w.image_path,
            perceptual_hash=w.perceptual_hash,
        )
        for d, w in scored
    ]
    return SimilarWindowsResponse(
        reference_id=window_id,
        threshold=threshold,
        items=items,
    )


@router.post(
    "/windows",
    status_code=201,
    response_model=WindowUploadResponse,
)
async def upload_window_image(
    image: UploadFile = File(..., description="Archivo de imagen (multipart)"),
    db: Session = Depends(get_db),
) -> WindowUploadResponse:
    window_storage.validate_image_mime(image.content_type)
    data = await window_storage.read_upload_limited(
        image,
        10 * 1024 * 1024,
    )
    digest = window_storage.sha256_hex(data)
    path = window_storage.save_image(data, digest)
    rel = window_storage.image_path_for_api(digest)
    perceptual = dhash_from_bytes(data)
    row = Window(
        image_path=rel,
        sha256=digest,
        perceptual_hash=perceptual,
        description=None,
        structured_data=None,
    )
    db.add(row)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        path.unlink(missing_ok=True)
        raise HTTPException(
            status_code=409,
            detail="Imagen duplicada: SHA-256 ya almacenado",
        ) from None
    db.refresh(row)
    return WindowUploadResponse(
        id=row.id,
        sha256=digest,
        size_bytes=len(data),
        path=rel,
    )
