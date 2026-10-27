"""Create the schema and load demo students and placement drives.

python -m app.cli.seed            # only if the database is empty
python -m app.cli.seed --reset    # wipe users and drives, then reload (refreshes drive dates)
"""

from __future__ import annotations

import argparse

from app.config import get_settings
from app.core.clock import today_in
from app.db.seed import is_seeded, seed_database
from app.db.session import create_db_engine, create_session_factory, init_db
from app.logging import configure_logging


def main() -> None:
    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawTextHelpFormatter
    )
    parser.add_argument(
        "--reset", action="store_true", help="delete existing users and drives first"
    )
    args = parser.parse_args()

    settings = get_settings()
    configure_logging(settings.log_level)
    engine = create_db_engine(settings.database_url)
    init_db(engine)
    with create_session_factory(engine)() as session:
        if is_seeded(session) and not args.reset:
            print("Database already contains users. Use --reset to reload the demo data.")
            return
        report = seed_database(
            session,
            settings.seed_dir,
            today=today_in(settings.timezone),
            demo_password=settings.demo_password.get_secret_value(),
            bcrypt_rounds=settings.bcrypt_rounds,
            reset=args.reset,
        )
    print(f"Seeded {report.students} students and {report.drives} drives (plus the admin account).")


if __name__ == "__main__":
    main()
