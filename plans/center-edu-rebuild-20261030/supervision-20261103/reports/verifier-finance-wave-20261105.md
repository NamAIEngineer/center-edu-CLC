# Independent verifier: FIN002 finance contract date controls

Date: 2026-11-05
Source: `/Users/nam/Documents/System-Agentic_AI/products/center-edu-rebuild`
Current HEAD: `fbcb75845fcffcb0406228464594e5f3a91c997e6` (`docs: record finance DOM fix checkpoint`)
Target fix commit: `f152d7375633a7407dfdc0fc1ce25aaab35b089f` (`fix: preserve finance contract text date filters`)
Working tree: `static/app.js` modified; verifier did not edit it.

## Commands

- `node --check static/app.js`: PASS.
- `git diff --check`: PASS.
- `python3 -m unittest test_app.CenterEduApiTests.test_health_and_public_shell tests.test_training_projection_correction tests.test_finance_contract_supervision`: **12 PASS**.
- Local runtime: `CENTER_EDU_DEMO_PASSWORD=... python3 app.py --host 127.0.0.1 --port 19028 --db /tmp/center-edu-finance-verify2-20261105.sqlite3`.
- Playwright-core 1.63.0 with installed Google Chrome for Testing executable; isolated contexts; viewports 1440x900 and 390x844.

## DOM evidence

Both viewports rendered 23 filter labels, 10 selects and 13 text inputs. Paired select/search controls are retained as observed reference behavior. One `#finance-contract-filter-apply` and one `#finance-contract-filter-clear` were present.

Four date filters were all `type=text`, with `data-date-text="1"`, `inputmode=numeric`, and observed Vietnamese placeholders:

- `Từ ngày tạo`
- `Đến ngày tạo`
- `Từ ngày hết hạn`
- `Đến ngày hết hạn`

Valid `05/11/2026` input produced request query `date_from=2026-11-05`; local filtered table read back one row. Clear reset the date value and reloaded the unfiltered local table. Invalid `31/02/2026` produced the expected local validation message `date_from must be YYYY-MM-DD` and HTTP 400. Reversed `10/11/2026` to `01/11/2026` produced `date_from must be before or equal to date_to` and HTTP 400. These 400 responses are expected fail-closed validation.

At 1440px the table wrapper did not overflow (`scrollWidth=1224`, `clientWidth=1224`). At 390px it overflowed horizontally (`scrollWidth=1165`, `clientWidth=338`), preserving access to wide contract columns.

No page exceptions occurred. The verifier run captured no 404 responses. An earlier pre-fix exploratory run had an unrelated optional-resource 404, but no reproducible URL/status/initiator remained in this post-fix run; no owned fix was made.

Screenshots:

- `/tmp/center-finance-verify05-1440.png` SHA-256 `920ed9643daedf7f61c8e29bf3027a001ca5d2fcec9c1a10e6987e3034ba93a9`
- `/tmp/center-finance-verify05-390.png` SHA-256 `60e4d1df89a77e5111129bd81c3cb591a2c062bf886660e9ec07d18f122b5a5f`

Current working `static/app.js` SHA-256: `83a4e92f1c986796c8ac2741cfd9f3c56a6f06a73566a7ac350caab46570cfd6`.

## Ordinary date controls

Source inspection confirms ordinary routes keep `data-date-input` without `data-date-text`; `/training/class` browser projection did not expose a date control within the bounded wait, so ordinary-route runtime behavior remains `UNKNOWN` for this run. No inference was made from the missing control.

## Verdict

`PASS_WITH_LIMITATIONS`: FIN002 date-text fix works on local isolated runtime at desktop and mobile sizes; validation and reset behavior are fail-closed; paired controls remain intact. Reference equal-state screenshots, private API semantics, and ordinary-date route runtime behavior remain `UNKNOWN`.
