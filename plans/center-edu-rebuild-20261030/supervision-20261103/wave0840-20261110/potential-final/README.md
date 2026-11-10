# Potential period tabs — brief 08:40

Latest explicit brief replaces the archived summary/raw/care contract with five period/status tabs and seven columns. Screenshots retain the archive next to the latest implementation; they are not a pixel-parity claim.

Fresh :19369 browser evidence: both routes show the requested five tabs and seven columns. All nonbaseline clicks update period query state. Pending filters to persisted NEW records. Today/week/month have identical rows in this fixture because created_at timestamps are on the same day. Pure behavioral tests cover day, Monday-week, month boundaries, missing dates and NEW-only pending status.

Source-backed API is /api/potential-customers; Sale preserves scope=sale. No records padded. Browser errors: zero.
