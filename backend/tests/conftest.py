import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.core.config import settings
from app.core.database import Base, get_db
from app.main import app


@pytest.fixture
def client(tmp_path, monkeypatch):
    db_path = tmp_path / "test.db"
    upload_dir = tmp_path / "uploads" / "windows"
    upload_dir.mkdir(parents=True, exist_ok=True)

    monkeypatch.setattr(settings, "database_url", f"sqlite:///{db_path}")
    monkeypatch.setattr(settings, "windows_upload_dir", str(upload_dir))

    new_engine = create_engine(
        settings.database_url,
        connect_args={"check_same_thread": False},
    )
    import app.core.database as db_mod

    db_mod.engine = new_engine
    db_mod.SessionLocal = sessionmaker(
        autocommit=False,
        autoflush=False,
        bind=new_engine,
    )

    Base.metadata.create_all(bind=new_engine)

    def _get_db():
        db = db_mod.SessionLocal()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = _get_db

    from fastapi.testclient import TestClient

    with TestClient(app) as test_client:
        yield test_client

    app.dependency_overrides.clear()
