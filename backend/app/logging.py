"""Logging configuration."""

from __future__ import annotations

import logging

_FORMAT = "%(asctime)s %(levelname)-7s %(name)s: %(message)s"
_NOISY = ("chromadb", "httpx", "httpcore", "sentence_transformers", "urllib3")


def configure_logging(level: str = "INFO") -> None:
    logging.basicConfig(level=level.upper(), format=_FORMAT, datefmt="%H:%M:%S", force=True)
    quiet = logging.DEBUG if level.upper() == "DEBUG" else logging.WARNING
    for name in _NOISY:
        logging.getLogger(name).setLevel(quiet)
