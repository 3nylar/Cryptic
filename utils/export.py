"""Exporting results to JSON, Markdown or plain text.

Break results are plain dataclasses with a ``to_dict()``, so exporting is a
formatting concern only — no analysis logic lives here. The format is chosen by
the file extension, which is what users expect from ``--export results.json``.
"""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path

SUPPORTED = (".json", ".md", ".txt")


class ExportError(ValueError):
    """Raised when a result cannot be written to the requested path."""


def export_result(result, path: str | Path) -> Path:
    """Write ``result`` to ``path``; the extension picks the format.

    Args:
        result: Any object with a ``to_dict()`` method (both break results have
            one).
        path: Destination ending in ``.json``, ``.md`` or ``.txt``.

    Returns:
        The resolved path written.

    Raises:
        ExportError: on an unsupported extension or an unwritable location.
    """
    target = Path(path).expanduser()
    suffix = target.suffix.lower()
    if suffix not in SUPPORTED:
        raise ExportError(
            f"unsupported export format {suffix!r}; use one of {', '.join(SUPPORTED)}"
        )
    data = result.to_dict()
    if suffix == ".json":
        text = json.dumps(data, indent=2, ensure_ascii=False)
    elif suffix == ".md":
        text = _to_markdown(data)
    else:
        text = _to_text(data)
    try:
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(text, encoding="utf-8")
    except OSError as exc:
        raise ExportError(f"could not write {target}: {exc}") from exc
    return target


def _to_markdown(data: dict) -> str:
    stamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    lines = [
        f"# Cryptanalysis report - {data['cipher'].title()} cipher",
        "",
        f"*Generated {stamp} by Cipher Breaker.*",
        "",
        "## Result",
        "",
        f"- **Recovered key:** `{data['recovered_key']}`",
        f"- **Confidence:** {data['confidence']:.0%}",
        f"- **Time taken:** {data['elapsed_seconds'] * 1000:.2f} ms",
        "",
        "## Recovered plaintext",
        "",
        "```",
        data["plaintext"].strip(),
        "```",
        "",
        "## How the attack worked",
        "",
    ]
    lines += [f"{i}. {step}" for i, step in enumerate(data["steps"], 1)]
    if data.get("warnings"):
        lines += ["", "## Warnings", ""] + [f"- {w}" for w in data["warnings"]]
    if data.get("candidates"):
        lines += [
            "",
            "## Candidate ranking",
            "",
            "| Shift | Chi-squared | Score | Preview |",
            "|------:|------------:|------:|---------|",
        ]
        for c in data["candidates"][:10]:
            preview = c["preview"].replace("|", "\\|")
            lines.append(
                f"| {c['shift']} | {c['chi_squared']} | {c['score']} | {preview} |"
            )
    if data.get("key_length_guesses"):
        lines += [
            "",
            "## Key length evidence",
            "",
            "| Length | Average IC | Kasiski votes | Score |",
            "|-------:|-----------:|--------------:|------:|",
        ]
        for g in data["key_length_guesses"][:8]:
            lines.append(
                f"| {g['length']} | {g['average_ioc']} | {g['kasiski_votes']} "
                f"| {g['combined_score']} |"
            )
    return "\n".join(lines) + "\n"


def _to_text(data: dict) -> str:
    lines = [
        f"Cipher: {data['cipher']}",
        f"Recovered key: {data['recovered_key']}",
        f"Confidence: {data['confidence']:.0%}",
        f"Elapsed: {data['elapsed_seconds'] * 1000:.2f} ms",
        "",
        "Plaintext:",
        data["plaintext"],
        "",
        "Steps:",
    ]
    lines += [f"  {i}. {s}" for i, s in enumerate(data["steps"], 1)]
    return "\n".join(lines) + "\n"
