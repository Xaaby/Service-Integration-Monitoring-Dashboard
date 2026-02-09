from datetime import datetime
from typing import Any, Dict

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from ..db import get_db
from ..metrics import (
    get_error_metrics,
    get_latency_timeseries,
    get_overview_metrics,
    get_throughput_timeseries,
)


router = APIRouter(prefix="/metrics", tags=["metrics"])


def _parse_ts(value: str) -> str:
    # Ensure ISO format; FastAPI gives us strings already, so we just validate.
    datetime.fromisoformat(value)
    return value


@router.get("/overview")
def metrics_overview(
    service_id: str = Query(...),
    env: str = Query("prod"),
    from_ts: str = Query(..., alias="from"),
    to_ts: str = Query(..., alias="to"),
    db: Session = Depends(get_db),
) -> Dict[str, Any]:
    start = _parse_ts(from_ts)
    end = _parse_ts(to_ts)
    overview = get_overview_metrics(db, service_id=service_id, env=env, start=start, end=end)
    return {
        "service_id": service_id,
        "environment": env,
        "from": start,
        "to": end,
        "success_rate": overview.success_rate,
        "error_rate_per_1k": overview.error_rate_per_1k,
        "p95_latency": overview.p95_latency,
        "throughput_per_day": overview.throughput_per_day,
        "health_score": overview.health_score,
    }


@router.get("/latency")
def metrics_latency(
    service_id: str = Query(...),
    env: str = Query("prod"),
    from_ts: str = Query(..., alias="from"),
    to_ts: str = Query(..., alias="to"),
    bucket: str = Query("day", regex="^(day|hour)$"),
    db: Session = Depends(get_db),
) -> Dict[str, Any]:
    start = _parse_ts(from_ts)
    end = _parse_ts(to_ts)
    series = get_latency_timeseries(
        db,
        service_id=service_id,
        env=env,
        start=start,
        end=end,
        bucket=bucket,
    )
    return {
        "service_id": service_id,
        "environment": env,
        "from": start,
        "to": end,
        "bucket": bucket,
        "series": series,
    }


@router.get("/errors")
def metrics_errors(
    service_id: str = Query(...),
    env: str = Query("prod"),
    from_ts: str = Query(..., alias="from"),
    to_ts: str = Query(..., alias="to"),
    db: Session = Depends(get_db),
) -> Dict[str, Any]:
    start = _parse_ts(from_ts)
    end = _parse_ts(to_ts)
    metrics = get_error_metrics(
        db,
        service_id=service_id,
        env=env,
        start=start,
        end=end,
    )
    return {
        "service_id": service_id,
        "environment": env,
        "from": start,
        "to": end,
        **metrics,
    }


@router.get("/throughput")
def metrics_throughput(
    service_id: str = Query(...),
    env: str = Query("prod"),
    from_ts: str = Query(..., alias="from"),
    to_ts: str = Query(..., alias="to"),
    bucket: str = Query("day", regex="^(day|hour)$"),
    db: Session = Depends(get_db),
) -> Dict[str, Any]:
    start = _parse_ts(from_ts)
    end = _parse_ts(to_ts)
    series = get_throughput_timeseries(
        db,
        service_id=service_id,
        env=env,
        start=start,
        end=end,
        bucket=bucket,
    )
    return {
        "service_id": service_id,
        "environment": env,
        "from": start,
        "to": end,
        "bucket": bucket,
        "series": series,
    }

