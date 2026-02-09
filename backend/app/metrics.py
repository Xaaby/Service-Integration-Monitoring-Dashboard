from dataclasses import dataclass
from typing import Any, Dict, List, Optional

from sqlalchemy import text
from sqlalchemy.orm import Session


@dataclass
class OverviewMetrics:
    success_rate: float
    error_rate_per_1k: float
    p95_latency: Optional[float]
    throughput_per_day: float
    health_score: int


def calculate_health_score(p95_latency: Optional[float], error_rate_per_1k: float) -> int:
    score = 100

    if p95_latency is not None:
        if p95_latency > 1500:
            score -= 30
        elif p95_latency > 1000:
            score -= 20
        elif p95_latency > 700:
            score -= 10

    if error_rate_per_1k > 50:
        score -= 40
    elif error_rate_per_1k > 20:
        score -= 25
    elif error_rate_per_1k > 5:
        score -= 10

    return max(0, min(100, score))


def get_overview_metrics(
    db: Session,
    service_id: str,
    env: str,
    start: str,
    end: str,
) -> OverviewMetrics:
    sql = text(
        """
        SELECT
            COUNT(*) AS total,
            COUNT(*) FILTER (WHERE status = 'success') AS success_count,
            COUNT(*) FILTER (WHERE status = 'failure') AS failure_count,
            percentile_cont(0.95) WITHIN GROUP (ORDER BY latency_ms)
                FILTER (WHERE event_type = 'request' AND latency_ms IS NOT NULL) AS p95_latency,
            COUNT(*)::decimal / GREATEST(1, DATE_PART('day', (:end_ts - :start_ts)) + 1) AS throughput_per_day
        FROM service_events se
        JOIN services s ON s.id = se.service_id
        WHERE se.service_id = :service_id
          AND s.environment = :env
          AND se.ts >= :start_ts AND se.ts < :end_ts
        """
    )
    row = db.execute(
        sql,
        {
            "service_id": service_id,
            "env": env,
            "start_ts": start,
            "end_ts": end,
        },
    ).one()

    total = row.total or 0
    success_count = row.success_count or 0
    failure_count = row.failure_count or 0
    success_rate = (success_count / total) if total > 0 else 0.0
    error_rate_per_1k = (failure_count * 1000.0 / total) if total > 0 else 0.0
    p95_latency = float(row.p95_latency) if row.p95_latency is not None else None
    throughput_per_day = float(row.throughput_per_day or 0.0)

    health_score = calculate_health_score(p95_latency, error_rate_per_1k)

    return OverviewMetrics(
        success_rate=success_rate,
        error_rate_per_1k=error_rate_per_1k,
        p95_latency=p95_latency,
        throughput_per_day=throughput_per_day,
        health_score=health_score,
    )


def get_latency_timeseries(
    db: Session,
    service_id: str,
    env: str,
    start: str,
    end: str,
    bucket: str = "day",
) -> List[Dict[str, Any]]:
    truncate = "day" if bucket == "day" else "hour"
    sql = text(
        f"""
        SELECT
            date_trunc('{truncate}', se.ts) AS bucket,
            percentile_cont(0.5) WITHIN GROUP (ORDER BY latency_ms)
                FILTER (WHERE event_type = 'request' AND latency_ms IS NOT NULL) AS p50_latency,
            percentile_cont(0.95) WITHIN GROUP (ORDER BY latency_ms)
                FILTER (WHERE event_type = 'request' AND latency_ms IS NOT NULL) AS p95_latency
        FROM service_events se
        JOIN services s ON s.id = se.service_id
        WHERE se.service_id = :service_id
          AND s.environment = :env
          AND se.ts >= :start_ts AND se.ts < :end_ts
        GROUP BY bucket
        ORDER BY bucket
        """
    )
    rows = db.execute(
        sql,
        {
            "service_id": service_id,
            "env": env,
            "start_ts": start,
            "end_ts": end,
        },
    ).all()
    return [
        {
            "bucket": r.bucket.isoformat(),
            "p50_latency": float(r.p50_latency) if r.p50_latency is not None else None,
            "p95_latency": float(r.p95_latency) if r.p95_latency is not None else None,
        }
        for r in rows
    ]


def get_error_metrics(
    db: Session,
    service_id: str,
    env: str,
    start: str,
    end: str,
) -> Dict[str, Any]:
    top_codes_sql = text(
        """
        SELECT error_code, COUNT(*) AS count
        FROM service_events se
        JOIN services s ON s.id = se.service_id
        WHERE se.service_id = :service_id
          AND s.environment = :env
          AND se.ts >= :start_ts AND se.ts < :end_ts
          AND status = 'failure'
          AND error_code IS NOT NULL
        GROUP BY error_code
        ORDER BY count DESC
        LIMIT 10
        """
    )
    series_sql = text(
        """
        SELECT
            date_trunc('day', se.ts) AS bucket,
            COUNT(*) AS failures
        FROM service_events se
        JOIN services s ON s.id = se.service_id
        WHERE se.service_id = :service_id
          AND s.environment = :env
          AND se.ts >= :start_ts AND se.ts < :end_ts
          AND status = 'failure'
        GROUP BY bucket
        ORDER BY bucket
        """
    )
    params = {
        "service_id": service_id,
        "env": env,
        "start_ts": start,
        "end_ts": end,
    }
    top_rows = db.execute(top_codes_sql, params).all()
    series_rows = db.execute(series_sql, params).all()
    return {
        "top_error_codes": [
            {"error_code": r.error_code, "count": r.count} for r in top_rows
        ],
        "failures_timeseries": [
            {"bucket": r.bucket.isoformat(), "failures": r.failures}
            for r in series_rows
        ],
    }


def get_throughput_timeseries(
    db: Session,
    service_id: str,
    env: str,
    start: str,
    end: str,
    bucket: str = "day",
) -> List[Dict[str, Any]]:
    truncate = "day" if bucket == "day" else "hour"
    sql = text(
        f"""
        SELECT
            date_trunc('{truncate}', se.ts) AS bucket,
            COUNT(*) AS throughput
        FROM service_events se
        JOIN services s ON s.id = se.service_id
        WHERE se.service_id = :service_id
          AND s.environment = :env
          AND se.ts >= :start_ts AND se.ts < :end_ts
        GROUP BY bucket
        ORDER BY bucket
        """
    )
    rows = db.execute(
        sql,
        {
            "service_id": service_id,
            "env": env,
            "start_ts": start,
            "end_ts": end,
        },
    ).all()
    return [
        {"bucket": r.bucket.isoformat(), "throughput": r.throughput} for r in rows
    ]

