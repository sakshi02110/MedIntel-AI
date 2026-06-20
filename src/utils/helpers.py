"""
General-purpose helper utilities for MedIntel AI.
"""

import json
import re
from datetime import datetime
from typing import Any, Dict, List, Optional

from src.utils.logger import get_logger

logger = get_logger("medintel.helpers")


# ── JSON Extraction ────────────────────────────────────────────────────────────

def extract_json_from_text(text: str) -> Optional[Dict[str, Any]]:
    """
    Robustly extract a JSON object from an LLM response string.

    Tries (in order):
    1. JSON inside ```json ... ``` or ``` ... ``` code fences.
    2. Direct json.loads of the whole text.
    3. Regex scan for the first ``{ ... }`` block.

    Args:
        text: Raw LLM response string.

    Returns:
        Parsed ``dict`` or ``None`` if no valid JSON found.
    """
    if not text:
        return None

    # Strategy 1 – markdown code fences
    fence_pattern = r"```(?:json)?\s*([\s\S]*?)```"
    for match in re.findall(fence_pattern, text, re.IGNORECASE):
        try:
            return json.loads(match.strip())
        except json.JSONDecodeError:
            continue

    # Strategy 2 – entire text
    try:
        return json.loads(text.strip())
    except json.JSONDecodeError:
        pass

    # Strategy 3 – first { … } block (greedy from outermost brace)
    start = text.find("{")
    if start != -1:
        # Walk chars to find matching closing brace
        depth = 0
        for i, ch in enumerate(text[start:], start):
            if ch == "{":
                depth += 1
            elif ch == "}":
                depth -= 1
                if depth == 0:
                    try:
                        return json.loads(text[start : i + 1])
                    except json.JSONDecodeError:
                        break

    logger.warning("extract_json_from_text: no valid JSON found in response.")
    return None


# ── Text Utilities ─────────────────────────────────────────────────────────────

def truncate_text(text: str, max_chars: int = 4_000) -> str:
    """
    Truncate *text* to at most *max_chars* characters, preserving word boundaries.

    Args:
        text:      Input text.
        max_chars: Maximum allowed length.

    Returns:
        Original text if short enough, otherwise truncated text with notice.
    """
    if len(text) <= max_chars:
        return text
    truncated = text[:max_chars]
    last_space = truncated.rfind(" ")
    if last_space > int(max_chars * 0.85):
        truncated = truncated[:last_space]
    return truncated + "\n\n[... content truncated for processing ...]"


def clean_text(text: str) -> str:
    """Remove excessive whitespace and normalize newlines."""
    text = re.sub(r"\r\n", "\n", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    text = re.sub(r" {2,}", " ", text)
    return text.strip()


def sanitize_filename(filename: str) -> str:
    """Strip unsafe characters from a filename."""
    return re.sub(r"[^\w\s\-\.]", "_", filename).strip()


# ── Formatting ─────────────────────────────────────────────────────────────────

def format_datetime(dt: Optional[datetime] = None, fmt: str = "%B %d, %Y at %I:%M %p") -> str:
    """Format a datetime object as a human-readable string."""
    return (dt or datetime.now()).strftime(fmt)


def format_file_size(size_bytes: int) -> str:
    """Return a human-readable file-size string."""
    if size_bytes < 1024:
        return f"{size_bytes} B"
    elif size_bytes < 1024 ** 2:
        return f"{size_bytes / 1024:.1f} KB"
    else:
        return f"{size_bytes / (1024 ** 2):.1f} MB"


# ── Status Helpers ─────────────────────────────────────────────────────────────

STATUS_EMOJI: Dict[str, str] = {
    "NORMAL": "✅",
    "LOW": "🔵",
    "HIGH": "🔴",
    "BORDERLINE_LOW": "🟡",
    "BORDERLINE_HIGH": "🟠",
    "CRITICAL_LOW": "🚨",
    "CRITICAL_HIGH": "🚨",
    "UNKNOWN": "⬜",
}

STATUS_COLOR: Dict[str, str] = {
    "NORMAL": "#22c55e",
    "LOW": "#60a5fa",
    "HIGH": "#ef4444",
    "BORDERLINE_LOW": "#facc15",
    "BORDERLINE_HIGH": "#f97316",
    "CRITICAL_LOW": "#dc2626",
    "CRITICAL_HIGH": "#dc2626",
    "UNKNOWN": "#94a3b8",
}


def get_status_emoji(status: str) -> str:
    """Return the display emoji for a biomarker status string."""
    return STATUS_EMOJI.get(status.upper(), "⬜")


def get_status_color(status: str) -> str:
    """Return the hex color for a biomarker status string."""
    return STATUS_COLOR.get(status.upper(), "#94a3b8")


def build_abnormal_summary(biomarkers: List[Dict[str, Any]]) -> str:
    """
    Build a concise plain-text summary of abnormal biomarkers.

    Args:
        biomarkers: List of biomarker dicts with 'name', 'status', 'value', 'unit'.

    Returns:
        Multi-line summary string, or 'All values within normal range.' if none.
    """
    abnormal = [
        b for b in biomarkers
        if b.get("status", "NORMAL").upper() not in ("NORMAL", "UNKNOWN")
    ]
    if not abnormal:
        return "All values within normal range."
    lines = []
    for b in abnormal:
        emoji = get_status_emoji(b.get("status", ""))
        lines.append(
            f"{emoji} {b['name']}: {b.get('value', 'N/A')} {b.get('unit', '')} "
            f"({b.get('status', '').replace('_', ' ').title()})"
        )
    return "\n".join(lines)
