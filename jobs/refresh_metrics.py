import logging
import os

from sqlalchemy import text, create_engine


logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)


def main() -> None:
    database_url = os.getenv(
        "DATABASE_URL",
        "postgresql+psycopg2://postgres:postgres@db:5432/monitoring",
    )
    logger.info("Starting refresh_metrics job")
    engine = create_engine(database_url, future=True)

    with engine.begin() as conn:
        # Example: touch a lightweight query to verify connectivity and warm views
        logger.info("Running health query against database")
        conn.execute(text("SELECT 1"))
        # If using materialized views, you could refresh them here, e.g.:
        # conn.execute(text('REFRESH MATERIALIZED VIEW CONCURRENTLY service_event_daily_agg'))

    logger.info("refresh_metrics job completed successfully")


if __name__ == "__main__":
    main()

