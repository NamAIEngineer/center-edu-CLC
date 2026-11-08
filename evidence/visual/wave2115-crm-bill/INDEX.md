# CRM bill visual evidence — wave2115

Route: `/report/crm/bill/index`  
Viewport: `1440x900`  
Runtime: disposable local SQLite, synthetic rich demo, ADMIN session  
Capture: Playwright 1.63.0 via `/Users/nam/claude-center-audit/node_modules/playwright`

## Artifacts

| Artifact | SHA-256 | Result |
|---|---|---|
| `before-1440x900.png` | `d0762db6e1cba11a8caf69f254597e08b54c8b416a66462c8ae36bad81d83012` | captured before final source edit |
| `after-1440x900.png` | `d0762db6e1cba11a8caf69f254597e08b54c8b416a66462c8ae36bad81d83012` | captured after final source edit |
| `before-dom.json` | `d6a715140ce39061132951d08b5f5fa533b81d87da4b2bbdc33958dfdaa452a5` | route DOM/payload readback |
| `after-dom.json` | `c2656a2f033893b4664adb6202eea50723477e819ba19a02439a46b46ac39a85` | route DOM/payload readback |

The local fixture payload already projected the invoice child keys, so the final alias fallback is behavior preserving in this capture. The after DOM confirms the invoice child labels and two-level header are present, with absent summary fields rendered as `—`.

## Verification limits

Reference-private API semantics, reference RBAC, production state, persistence across restart, and live parity remain **UNKNOWN**. Finance verifier reports likewise limit summary claims to explicit backend keys and mark reference/live browser parity UNKNOWN; no reference write or credential was used.
