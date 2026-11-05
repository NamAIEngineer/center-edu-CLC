# Independent rich-demo HTTP projection proof — 2026-11-05

Target: `/Users/nam/Documents/System-Agentic_AI/products/center-edu-rebuild`
Source commit: `224f2a2cee965dcbdc4037eadfc7bd65cd91f258`
Scope: disposable local process, synthetic SQLite only; no reference writes.

## Runtime

- Loopback: `127.0.0.1:19018`
- DB: `/tmp/center-edu-rich-proof-20261105-http.sqlite3`
- Environment: `CENTER_EDU_RICH_DEMO=1`; QA-only local seed password supplied through process environment and not recorded here.
- Runtime shut down cleanly after checks.

## HTTP/API and database evidence

- `POST /api/auth/login`: HTTP `200`, `ok=true`.
- `GET /api/generated/screens?route=/training/announcement`: HTTP `200`, `total=12`.
  - First record `data` contains persisted raw fields.
  - `display_data.thong_bao=Thông báo Demo 01`.
  - `display_data.trang_thai=Đang hoạt động`.
  - `display_data.tao_boi=Tạo bởi Demo 01`.
  - `display_data.a_xem_a_gui=Đã xem/Đã gửi Demo 01`.
  - Search `q=Demo 01`: `total=1`.
- `GET /api/generated/screens?route=/training/event`: HTTP `200`, `total=12`.
  - `display_data.noi_dung=Nội dung Demo 01`.
  - `display_data.trang_thai=Đang hoạt động`.
  - `display_data.a_xem_a_gui=Đã xem/Đã gửi Demo 01`.
  - Search `q=Demo 01`: `total=1`.
- `GET /api/generated/screens?route=/training/post`: HTTP `200`, `total=12`.
  - `display_data.noi_dung=Nội dung Demo 01`.
  - `display_data.trang_thai=Đang hoạt động`.
  - `display_data.ngay_tao=2026-01-01`.
  - `display_data.nguoi_tao=Người tạo Demo 01`.
  - Search `q=Demo 01`: `total=1`.
- Direct SQLite read-back from `generated_screen_records`:
  - announcement: `12` rows, first raw JSON `710` bytes, contains `title`.
  - event: `12` rows, first raw JSON `494` bytes, contains `title` and `noi_dung`.
  - post: `12` rows, first raw JSON `862` bytes, contains `noi_dung`.

This proves populated synthetic local API/DB projection and search. It does not prove reference parity or production data.

## Browser capability boundary

- `node -e "require('playwright')"` from SOURCE_ROOT: `NO_PLAYWRIGHT`.
- CUA capability inventory: `browsers: []`; `Browsers: Error: The browser access host is unavailable`.
- No install, profile restart, settings bypass, reference login, or reference mutation attempted.
- Finance duplicate-control/native-date behavior remains `IN_PROGRESS / UNKNOWN` pending a supported local DOM harness.
