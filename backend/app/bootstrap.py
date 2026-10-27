"""Start-up work shared by the API and the command-line tools."""

from __future__ import annotations

import logging

from app.container import Container
from app.core.clock import today_in
from app.db.seed import is_seeded, seed_database
from app.db.session import init_db

logger = logging.getLogger(__name__)


def prepare(container: Container) -> None:
    """Create tables, seed demo data on first run, and bring the document index up to date."""
    settings = container.settings
    init_db(container.engine)

    if settings.auto_seed:
        with container.session_factory() as session:
            if not is_seeded(session):
                report = seed_database(
                    session,
                    settings.seed_dir,
                    today=today_in(settings.timezone),
                    demo_password=settings.demo_password.get_secret_value(),
                    bcrypt_rounds=settings.bcrypt_rounds,
                )
                logger.info("Seeded %d students and %d drives", report.students, report.drives)

    if settings.auto_ingest:
        try:
            container.ingestor.sync()
        except Exception:
            # The API should still come up, and /api/health will report an empty index.
            logger.exception("Document indexing failed at startup")
    container.retriever.refresh()
