"""Deterministic Windows-compatible filesystem names."""
from __future__ import annotations
import re

_INVALID = re.compile(r'[<>:"/\\|?*\x00-\x1f]')
_RESERVED = re.compile(r"^(?:CON|PRN|AUX|NUL|COM[1-9]|LPT[1-9])(?:\..*)?$", re.IGNORECASE)

def safe_filename(value: str, *, max_length: int = 180, fallback: str = "Untitled") -> str:
    """Sanitize a filename component for Windows and common portable filesystems."""
    cleaned = _INVALID.sub("_", value)
    cleaned = re.sub(r"\s+", " ", cleaned).strip(" .")
    if not cleaned:
        cleaned = fallback
    if _RESERVED.fullmatch(cleaned):
        cleaned = "_" + cleaned
    if len(cleaned) > max_length:
        cleaned = cleaned[:max_length].rstrip(" .") or fallback
    return cleaned

def unique_filename(value: str, used: set[str], *, max_length: int = 180) -> str:
    """Return a deterministic filename component unique within a case-insensitive set."""
    candidate = safe_filename(value, max_length=max_length)
    if candidate.casefold() not in used:
        used.add(candidate.casefold())
        return candidate
    number = 2
    while True:
        suffix = " (" + str(number) + ")"
        candidate = candidate[:max_length-len(suffix)].rstrip(" .") + suffix
        key = candidate.casefold()
        if key not in used:
            used.add(key)
            return candidate
        number += 1
