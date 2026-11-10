# Upload address after evidence

- Fresh local server: `127.0.0.1:19390`, current source, isolated rich DB.
- Tab labels after shell reconciliation: `Lịch sử import`, `Hướng dẫn`.
- Hướng dẫn tab changes visible panel (`Hướng dẫn import`) and empty prompt.
- Import tab file preview tested with source-like CSV: one row rendered, footer `Hiển thị 1 đến 1 của 1 bản ghi`.
- Paired image: `cmp_center_upload_address.png` (DEMO left, REBUILD right).
- Screenshots: `rebuild_upload_address.png`, `rebuild_upload_preview.png`.
- Guide tab exposes `Tải mẫu CSV` with download filename `mau_import_dia_chi.csv`; browser download event verified. Download content begins with UTF-8 BOM and the 15 observed headers.
- Upload observer now disconnects when the route changes; replacement tabs are bound once via `data-w6UploadBound`.
