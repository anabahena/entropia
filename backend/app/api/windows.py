from fastapi import (
    APIRouter,
    Depends,
    File,
    HTTPException,
    Query,
    UploadFile,
    BackgroundTasks,
)
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.database import get_db, SessionLocal
from app.models.window import Window
from app.schemas.windows import (
    SimilarWindowsResponse,
    SimilarWindowItem,
    WindowListItem,
    WindowUploadResponse,
)
from app.services import window_storage
from app.services.ollama_service import analyze_with_ventana
from app.utils.dhash import dhash_from_bytes, hamming_distance_hex
from fastapi.responses import JSONResponse
from pathlib import Path
import asyncio
import anyio

router = APIRouter()


# =========================
# BACKGROUND IA PROCESS (FIX FINAL)
# =========================
def process_with_ai(window_id: int):
    anyio.run(_process_with_ai_async, window_id)


async def _process_with_ai_async(window_id: int):
    db = SessionLocal()

    try:
        row = db.get(Window, window_id)
        if not row:
            return

        full_path = Path("/app") / row.image_path

        result = await analyze_with_ventana(
            user_prompt="Describe the image in detail.",
            image_path=str(full_path),
        )
        _logger.info("Analysis result for window %d: %s", window_id, result)
        row.description = result.description
        row.structured_data = result.structured_data

        db.commit()

    except Exception as e:
        print(f"IA ERROR for window {window_id}: {e}")
        try:
            row = db.get(Window, window_id)
            if row:
                row.description = "Procesamiento fallido"
                # row.ai_status = "failed"
                db.commit()
        except Exception as inner:
            print(f"Fallback error: {inner}")

    finally:
        db.close()


# =========================
# GET WINDOWS
# =========================
@router.get("/windows", response_model=list[WindowListItem])
async def list_windows(db: Session = Depends(get_db)) -> list[WindowListItem]:
    rows = (
        db.execute(select(Window).order_by(Window.created_at.desc()))
        .scalars()
        .all()
    )

    return [WindowListItem.model_validate(r) for r in rows]


# =========================
# SIMILAR WINDOWS
# =========================
@router.get(
    "/windows/{window_id}/similar",
    response_model=SimilarWindowsResponse,
)
def list_similar_windows(
    window_id: int,
    threshold: int = Query(64, ge=0, le=64),
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


# =========================
# POST WINDOWS (FINAL PRO)
# =========================
@router.post(
    "/windows",
    status_code=201,
    response_model=WindowUploadResponse,
)
async def upload_window_image(
    background_tasks: BackgroundTasks,
    image: UploadFile = File(...),
    db: Session = Depends(get_db),
) -> WindowUploadResponse:

    # =========================
    # VALIDACIÓN Y LECTURA
    # =========================
    if not image:
        raise HTTPException(status_code=422, detail="Archivo requerido")

    window_storage.validate_image_mime(image.content_type)

    data = await window_storage.read_upload_limited(
        image,
        10 * 1024 * 1024,
    )

    if not data:
        raise HTTPException(status_code=422, detail="Archivo vacío")

    # =========================
    # HASHES
    # =========================
    digest = window_storage.sha256_hex(data)
    perceptual = dhash_from_bytes(data)

    path = window_storage.save_image(data, digest)
    rel = window_storage.image_path_for_api(digest)

    # =========================
    # CREAR REGISTRO
    # =========================
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

        existing = db.query(Window).filter_by(sha256=digest).first()

        if existing:
            background_tasks.add_task(process_with_ai, existing.id)

        raise HTTPException(
            status_code=409,
            detail="Imagen duplicada: SHA-256 ya almacenado",
        ) from None

    db.refresh(row)

    # =========================
    # IA EN BACKGROUND 🚀
    # =========================
    background_tasks.add_task(process_with_ai, row.id)

    return JSONResponse(
        status_code=201,
        content=WindowUploadResponse(
            id=row.id,
            sha256=digest,
            size_bytes=len(data),
            path=rel,
        ).model_dump(),
        headers={"X-Entropia-Version": "3.2.0"},
    )