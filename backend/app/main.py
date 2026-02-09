from fastapi import FastAPI
from .routes import health, services, metrics, seed
from .db import init_db


def create_app() -> FastAPI:
    app = FastAPI(
        title="Service Integration Monitoring Dashboard API",
        version="1.0.0",
    )

    # Routers
    app.include_router(health.router)
    app.include_router(services.router)
    app.include_router(metrics.router)
    app.include_router(seed.router)

    @app.on_event("startup")
    def on_startup() -> None:
        # Apply schema, views, and optionally seed data
        init_db()

    return app


app = create_app()

