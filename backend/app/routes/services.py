from typing import List

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from ..db import get_db
from ..models import Service, IncidentNote


router = APIRouter(prefix="/services", tags=["services"])


@router.get("", response_model=List[dict])
def list_services(db: Session = Depends(get_db)) -> List[dict]:
    services = db.query(Service).order_by(Service.name).all()
    return [
        {
            "id": str(s.id),
            "name": s.name,
            "owner_team": s.owner_team,
            "environment": s.environment,
            "created_at": s.created_at.isoformat(),
        }
        for s in services
    ]


@router.get("/{service_id}/incidents", response_model=List[dict])
def list_incident_notes(service_id: str, db: Session = Depends(get_db)) -> List[dict]:
    notes = (
        db.query(IncidentNote)
        .filter(IncidentNote.service_id == service_id)
        .order_by(IncidentNote.incident_date.desc())
        .all()
    )
    return [
        {
            "id": str(n.id),
            "incident_date": n.incident_date.isoformat(),
            "summary": n.summary,
            "root_cause": n.root_cause,
            "resolution": n.resolution,
            "created_at": n.created_at.isoformat(),
        }
        for n in notes
    ]

