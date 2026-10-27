"""Index the documents folder into the vector store.

python -m app.cli.ingest             # add, update and remove only what changed
python -m app.cli.ingest --rebuild   # re-embed everything
"""

from __future__ import annotations

import argparse

from app.config import get_settings
from app.container import build_container
from app.logging import configure_logging


def main() -> None:
    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawTextHelpFormatter
    )
    parser.add_argument(
        "--rebuild", action="store_true", help="discard the index and re-embed all documents"
    )
    args = parser.parse_args()

    settings = get_settings()
    configure_logging(settings.log_level)
    container = build_container(settings)
    try:
        report = container.ingestor.sync(rebuild=args.rebuild)
    finally:
        container.close()
    print(report.summary())
    for doc_id, error in report.errors.items():
        print(f"  failed: {doc_id}: {error}")
    raise SystemExit(1 if report.errors else 0)


if __name__ == "__main__":
    main()
