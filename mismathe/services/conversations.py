"""Conversation logging to the repo.

Every chat turn (user + assistant) gets appended as a JSON line to
memory/conversations/<external_id_short>/<YYYY-MM-DD>.jsonl. The nightly
GitHub sync commits + pushes the whole memory/ tree.

This is in addition to the SQLite ConversationMessage table — the JSONL
files give us a portable, human-readable, version-controlled record that
survives DB rebuilds.
"""
from __future__ import annotations

import json
import logging
from datetime import date, datetime
from pathlib import Path

from config import ROOT


logger = logging.getLogger(__name__)

CONVERSATIONS_DIR = ROOT / "memory" / "conversations"


def log_turn(
    *,
    external_id: str,
    role: str,
    content: str,
    metadata: dict | None = None,
) -> Path:
    """Append one turn to today's JSONL file for this student. Returns the path."""
    short = external_id[:12]
    user_dir = CONVERSATIONS_DIR / short
    user_dir.mkdir(parents=True, exist_ok=True)
    path = user_dir / f"{date.today().isoformat()}.jsonl"

    record = {
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "role": role,
        "content": content,
    }
    if metadata:
        record["metadata"] = metadata

    try:
        with path.open("a", encoding="utf-8") as f:
            f.write(json.dumps(record, ensure_ascii=False) + "\n")
    except OSError as exc:
        logger.warning("Failed to log conversation turn for %s: %s", short, exc)
    return path
