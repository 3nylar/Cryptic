"""Configuration and logging setup.

Settings come from three places, each overriding the one before it:

1. the defaults in :class:`Settings`,
2. a JSON file (``config.json`` next to ``main.py``, or ``--config PATH``),
3. command-line flags.

That order is the usual convention: files hold your habits, flags hold your
exceptions. A missing or malformed config file is a warning, never a crash —
the tool must always start.
"""

from __future__ import annotations

import json
import logging
import sys
from dataclasses import asdict, dataclass, fields
from pathlib import Path

DEFAULT_CONFIG_PATH = Path(__file__).resolve().parent.parent / "config.json"


@dataclass
class Settings:
    """Runtime settings for one invocation of the tool."""

    max_key_length: int = 20
    """Largest Vigenere key length the breaker will consider."""

    top_candidates: int = 5
    """How many candidate plaintexts to display for a Caesar break."""

    no_color: bool = False
    """Force plain ASCII output."""

    log_level: str = "WARNING"
    """One of DEBUG, INFO, WARNING, ERROR."""

    log_file: str | None = None
    """If set, logs are written here as well as to stderr."""

    explain: bool = True
    """Print the step-by-step explanation after an attack."""

    @classmethod
    def load(cls, path: Path | None = None) -> "Settings":
        """Load settings from JSON, falling back to defaults.

        Unknown keys are ignored with a warning rather than raising, so a
        config written for a newer version still works.
        """
        settings = cls()
        target = path or DEFAULT_CONFIG_PATH
        if not target.exists():
            return settings
        try:
            data = json.loads(target.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError) as exc:
            logging.getLogger(__name__).warning(
                "Ignoring unreadable config %s: %s", target, exc
            )
            return settings
        known = {f.name for f in fields(cls)}
        for key, value in data.items():
            if key in known:
                setattr(settings, key, value)
            else:
                logging.getLogger(__name__).warning(
                    "Unknown config key ignored: %s", key
                )
        return settings

    def to_dict(self) -> dict:
        return asdict(self)


def setup_logging(level: str = "WARNING", log_file: str | None = None) -> None:
    """Configure logging for the whole application.

    Logs go to stderr so that they never contaminate piped plaintext on stdout
    — an important detail for a tool people will use in shell pipelines.
    """
    handlers: list[logging.Handler] = [logging.StreamHandler(sys.stderr)]
    if log_file:
        handlers.append(logging.FileHandler(log_file, encoding="utf-8"))
    logging.basicConfig(
        level=getattr(logging, str(level).upper(), logging.WARNING),
        format="%(asctime)s %(levelname)-7s %(name)s: %(message)s",
        datefmt="%H:%M:%S",
        handlers=handlers,
        force=True,
    )
