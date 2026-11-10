# Prior authorized work — WIP checkpoint, not visual acceptance

These five routes were already modified before the final eight-route pass. This checkpoint preserves that work separately from acceptance of the latest 08:40 brief. Fresh paired captures use the isolated local fixture at `http://127.0.0.1:19369`, 1440×900. Controller and read-only reviewer inspected the pairs. No pixel-parity claim.

| Route | Preserved work | Observed remaining difference |
| --- | --- | --- |
| `/crm/packet` | One page-size owner; remove observer add/remove loop; route pricing tabs | Icons, action order/colors, row presentation still differ from archive. Row count is source-dependent. |
| `/crm/target/index` | Use existing annual/monthly target projection | Year/scope controls exist in DOM but are not visible in capture; year value was blank after shell normalization. |
| `/dashboard/crm` | Four-card layout over local API values | Thu - Nợ lacks archived grouped chart; promotion metadata absent. Finance-wide metrics require validation against the heading's today scope. |
| `/dashboard/sale` | Source-backed KPI and period selection | Calendar/header spacing and monthly section position differ. Shared date selection and collected-money semantics still require resource-contract verification. |
| `/dashboard/finance` | Card layout and observed inventory development message | Breadcrumb, chart structure, cramped chart labels and missing promotion metadata differ. |

The main eight-route fixes do not depend on visual acceptance of these routes. Known differences remain open. No fake records or reference totals were inserted to hide them.

Validation on the preserved working source: both changed modules pass `node --check`; `git diff --check` passes. Root Node suite exits successfully for all 13 scripts (one opt-in test skipped), module Python suite 25/25, application suite 90 tests with only the two documented baseline failures. Browser probe reported no page/console errors on these five routes; period interactions were not rechecked by this capture.
