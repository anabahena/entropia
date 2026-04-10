from contextlib import asynccontextmanager

from app.core.config import settings

import logging
import time
from datetime import UTC, datetime

from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from starlette.requests import Request

from app.api.v1.router import api_router
from app.api.windows import router as windows_router

_logger = logging.getLogger("entropia")


@asynccontextmanager
async def lifespan(_app: FastAPI):
    import app.models.window  # noqa: F401 - register Window model
    from app.core.database import Base, engine

    Base.metadata.create_all(bind=engine)
    yield


if not _logger.handlers:
    _handler = logging.StreamHandler()
    _handler.setFormatter(logging.Formatter("%(message)s"))
    _logger.addHandler(_handler)
    _logger.setLevel(logging.INFO)
    _logger.propagate = False

app = FastAPI(title=settings.app_name, lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://127.0.0.1:3000",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def entropia_request_middleware(request: Request, call_next):
    start = time.perf_counter()
    response = await call_next(request)
    duration_ms = round((time.perf_counter() - start) * 1000, 3)
    response.headers["X-Entropia-Version"] = "3.2.0"
    ts = datetime.now(UTC).isoformat()
    _logger.info(
        "[ENTROPIA-LOG] %s | %s | %s | %s | %s",
        ts,
        request.method,
        request.url.path,
        response.status_code,
        duration_ms,
    )
    return response


def _guess_image_mime(header: bytes) -> str:
    if header.startswith(b"\x89PNG\r\n\x1a\n"):
        return "image/png"
    if header.startswith(b"\xff\xd8\xff"):
        return "image/jpeg"
    if header.startswith(b"GIF87a") or header.startswith(b"GIF89a"):
        return "image/gif"
    # WEBP: RIFF....WEBP
    if len(header) >= 12 and header.startswith(b"RIFF") and header[8:12] == b"WEBP":
        return "image/webp"
    return "application/octet-stream"


@app.get("/uploads/windows/{sha256}")
def serve_window_image(sha256: str) -> FileResponse:
    img_path = Path(settings.upload_dir) / sha256
    if not img_path.is_file():
        raise HTTPException(status_code=404, detail="Image not found")

    with img_path.open("rb") as f:
        header = f.read(32)
    mime = _guess_image_mime(header)
    return FileResponse(str(img_path), media_type=mime)


app.include_router(api_router, prefix=settings.api_v1_prefix)
app.include_router(windows_router, prefix="/api")


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


# Mount remaining static files after custom image route.
_uploads_root = Path(settings.upload_dir).parent
_uploads_root.mkdir(parents=True, exist_ok=True)
app.mount("/uploads", StaticFiles(directory=str(_uploads_root)), name="uploads")
