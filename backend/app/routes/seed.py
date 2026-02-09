import os

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from ..db import get_db
from ...data.seed import run_seed


router = APIRouter(tags=["seed"])


@router.post("/seed")
def trigger_seed(db: Session = Depends(get_db)) -> dict:
    if os.getenv("ENABLE_DEV_SEED", "false").lower() != "true":
        raise HTTPException(status_code=403, detail="Seeding is disabled in this environment")

    run_seed(db)
    return {"status": "ok", "message": "Database reseeded"}

