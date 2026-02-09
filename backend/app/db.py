import os
from pathlib import Path

from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, Session

from data.seed import run_seed


DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql+psycopg2://postgres:postgres@db:5432/monitoring",
)

ROOT_DIR = Path(__file__).resolve().parents[2]
SQL_DIR = ROOT_DIR / "sql"

engine = create_engine(DATABASE_URL, future=True)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db() -> Session:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def _run_sql_file(path: Path) -> None:
    if not path.exists():
        return
    sql_text = path.read_text(encoding="utf-8")
    with engine.begin() as conn:
        for statement in filter(None, (s.strip() for s in sql_text.split(";"))):
            conn.execute(text(statement))


def init_db() -> None:
    """
    Initialize database schema, views, and optional seed data.
    Designed to be idempotent and safe on repeated startup.
    """
    schema_path = SQL_DIR / "schema.sql"
    metrics_views_path = SQL_DIR / "metrics_views.sql"

    _run_sql_file(schema_path)
    _run_sql_file(metrics_views_path)

    # Optionally auto-seed on startup (for local/dev use)
    if os.getenv("AUTO_SEED_ON_STARTUP", "true").lower() == "true":
        with SessionLocal() as db:
            run_seed(db)

