# /setup/classroom — A1 verified, A3 bounded

Room/slot tabs now invoke distinct persisted renderers; returning restores the room table and actions. Slot create modal contains code, name, start/end time, status, Hủy/Lưu. Route-local controls remove unobserved Excel and match the compact toolbar.

Fresh 1440x900 local capture paired with reference: cmp_setup_classroom.png. Reviewed visually: layout is aligned; fixture row count differs (one persisted room vs seven reference rows), status text and row actions still differ. This is not full pixel acceptance.

Independent browser verification: wave0536_audit. No JS page errors; tab round trip and modal verified. Syntax and diff checks pass. Python 90 tests: 88 pass, exactly the two previously named baseline failures.
