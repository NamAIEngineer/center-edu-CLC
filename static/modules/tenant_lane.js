/* W6 tenant configuration route contract. */
export const TENANT_LANE_ROUTES = Object.freeze(["/tenant/config_excel"]);
export const TENANT_EXPORT_LABEL = "Bật xuất Excel báo cáo";

export function register(centerEdu = globalThis.CenterEdu) {
  if (!centerEdu) return { routes: TENANT_LANE_ROUTES };
  centerEdu.w6LaneMetadata = {
    ...(centerEdu.w6LaneMetadata || {}),
    tenant: {
      routes: TENANT_LANE_ROUTES,
      status: "PERSISTENT_LOCAL_CONTRACT",
      source: "/api/reports/catalog",
      persistence: "/api/generated/screens?route=/tenant/config_excel",
    },
  };
  // The actual projection is owned by w6_screen_utils.js. Keep this lane
  // registration as metadata only; synthetic checkbox grids and an extra
  // unsupported column previously advertised controls with no API backing.
  for (const route of TENANT_LANE_ROUTES) centerEdu.registerScreen?.(route, async () => false);
  return { routes: TENANT_LANE_ROUTES, status: "PERSISTENT_LOCAL_CONTRACT" };
}

