import random
from datetime import datetime, timedelta, date
from typing import List, Tuple

from sqlalchemy.orm import Session

from backend.app.models import Service, ServiceEvent, IncidentNote


SEED_VALUE = 42


def generate_seed_events() -> Tuple[List[Service], List[ServiceEvent], List[IncidentNote]]:
    random.seed(SEED_VALUE)

    services: List[Service] = []
    events: List[ServiceEvent] = []
    incidents: List[IncidentNote] = []

    base_date = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0) - timedelta(
        days=30
    )

    # Define 6 services with different behaviors
    service_specs = [
        ("payments-api", "payments", "prod"),
        ("user-service", "identity", "prod"),
        ("orders-api", "orders", "prod"),
        ("reporting-job", "analytics", "stage"),
        ("notifications", "messaging", "prod"),
        ("inventory-api", "supply", "stage"),
    ]

    for name, team, env in service_specs:
        svc = Service(name=name, owner_team=team, environment=env)
        services.append(svc)

    # Patterns:
    # - payments-api: intermittent failures
    # - user-service: latency regression after mid-point
    # - orders-api: higher weekday throughput
    for svc in services:
        for day_offset in range(30):
            day = base_date + timedelta(days=day_offset)
            is_weekend = day.weekday() >= 5

            # Base throughput
            if svc.name == "orders-api":
                # Busy on weekdays
                count = 800 if not is_weekend else 200
            else:
                count = 400 if not is_weekend else 150

            # Reporting job runs less frequently
            if svc.name == "reporting-job":
                count = 80 if not is_weekend else 20

            for _ in range(count):
                ts = day + timedelta(
                    seconds=random.randint(0, 86400 - 1),
                )
                event_type = "job_run" if svc.name == "reporting-job" else "request"

                # Latency behavior
                latency_ms = None
                if event_type == "request":
                    base_latency = 120
                    if svc.name == "user-service" and day_offset > 15:
                        # Regression after halfway
                        base_latency = 300
                    jitter = random.randint(-40, 200)
                    latency_ms = max(20, base_latency + jitter)

                # Failure patterns
                status = "success"
                error_code = None
                if svc.name == "payments-api":
                    # Intermittent failures
                    if random.random() < 0.04:
                        status = "failure"
                        error_code = random.choice(
                            ["PAYMENT_DECLINED", "GATEWAY_TIMEOUT", "CARD_VALIDATION"]
                        )
                elif svc.name == "reporting-job":
                    if random.random() < 0.02:
                        status = "failure"
                        error_code = random.choice(["JOB_TIMEOUT", "ETL_SCHEMA_MISMATCH"])
                else:
                    if random.random() < 0.01:
                        status = "failure"
                        error_code = random.choice(["UNEXPECTED_ERROR", "DOWNSTREAM_500"])

                payload_size = random.randint(500, 5000) if event_type == "request" else None
                build_version = f"v1.{1 + day_offset // 7}"

                ev = ServiceEvent(
                    service=svc,
                    ts=ts,
                    event_type=event_type,
                    status=status,
                    latency_ms=latency_ms,
                    payload_size_bytes=payload_size,
                    error_code=error_code,
                    correlation_id=f"corr-{random.randint(100000, 999999)}",
                    build_version=build_version,
                )
                events.append(ev)

        # Add a couple of incidents per service
        incidents.append(
            IncidentNote(
                service=svc,
                incident_date=date.today() - timedelta(days=10),
                summary=f"Degradation observed in {svc.name}",
                root_cause="Downstream dependency timeout",
                resolution="Increased timeout and added retries",
            )
        )
        incidents.append(
            IncidentNote(
                service=svc,
                incident_date=date.today() - timedelta(days=3),
                summary=f"Elevated error rates in {svc.name}",
                root_cause="Bad configuration rollout",
                resolution="Rolled back configuration and added safeguard checks",
            )
        )

    return services, events, incidents


def run_seed(db: Session) -> None:
    services, events, incidents = generate_seed_events()

    # Truncate tables for idempotent reseed
    db.execute("TRUNCATE TABLE incident_notes CASCADE")
    db.execute("TRUNCATE TABLE service_events CASCADE")
    db.execute("TRUNCATE TABLE services CASCADE")
    db.bulk_save_objects(services)
    db.flush()
    db.bulk_save_objects(events)
    db.bulk_save_objects(incidents)
    db.commit()

