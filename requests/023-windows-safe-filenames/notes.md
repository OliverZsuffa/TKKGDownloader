# Implementation notes

Added reusable Windows-safe filename sanitization for imported tracks and final episode output names. Canonical titles and matching data remain unchanged. Added test coverage for forbidden characters, reserved device names, trailing spaces and dots, length limits, collisions, and unchanged titles. Verification pending.
