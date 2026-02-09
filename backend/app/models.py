import uuid
from datetime import datetime, date

from sqlalchemy import (
    Column,
    Date,
    DateTime,
    Enum,
    ForeignKey,
    Integer,
    String,
    Text,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import declarative_base, relationship


Base = declarative_base()


class Service(Base):
    __tablename__ = "services"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(255), nullable=False, unique=True)
    owner_team = Column(String(255), nullable=False)
    environment = Column(String(32), nullable=False)  # prod / stage
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    events = relationship("ServiceEvent", back_populates="service")
    incident_notes = relationship("IncidentNote", back_populates="service")


class ServiceEvent(Base):
    __tablename__ = "service_events"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    service_id = Column(UUID(as_uuid=True), ForeignKey("services.id"), nullable=False)
    ts = Column(DateTime, nullable=False, index=True)
    event_type = Column(
        Enum("request", "job_run", name="event_type_enum"),
        nullable=False,
    )
    status = Column(
        Enum("success", "failure", name="status_enum"),
        nullable=False,
    )
    latency_ms = Column(Integer, nullable=True)
    payload_size_bytes = Column(Integer, nullable=True)
    error_code = Column(Text, nullable=True)
    correlation_id = Column(Text, nullable=True)
    build_version = Column(Text, nullable=True)

    service = relationship("Service", back_populates="events")


class IncidentNote(Base):
    __tablename__ = "incident_notes"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    service_id = Column(UUID(as_uuid=True), ForeignKey("services.id"), nullable=False)
    incident_date = Column(Date, nullable=False)
    summary = Column(Text, nullable=False)
    root_cause = Column(Text, nullable=False)
    resolution = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    service = relationship("Service", back_populates="incident_notes")

