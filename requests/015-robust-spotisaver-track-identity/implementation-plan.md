# Implementation plan: Request 015

Implement deterministic layered matching in the import boundary. Preserve exact normalized title comparison and add conservative provider wrapper parsing. Use exact ID3 title as a fallback. Use embedded album plus track number only as a pair, with exact normalized album identity against the verified album title. Support alternate_titles only when present in trusted track metadata. Record matching evidence and rule identifiers in the manifest.

Never use fuzzy similarity for automatic assignment. Never use track number alone. Build the complete one-to-one mapping before copying canonical files. Retain duplicate hash rejection, checksum verification, and manifest order checks.

Harden logger startup by writing and flushing an initialization record and checking that the persistent log file exists before the browser starts.

Tests use synthetic ZIP archives and synthetic ID3 metadata. The user's preserved episode 150 ZIP remains a local end-to-end fixture and is not uploaded or used by CI.
