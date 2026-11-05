/* W6 tenant configuration route contract. */
export const TENANT_LANE_ROUTES = Object.freeze(["/tenant/config_excel"]);
export const TENANT_EXPORT_LABEL = "Bật xuất Excel báo cáo";

export function register(centerEdu = globalThis.CenterEdu) {
  if (!centerEdu) return { routes: TENANT_LANE_ROUTES };
  centerEdu.w6LaneMetadata = {
    ...(centerEdu.w6LaneMetadata || {}),
    tenant: { routes: TENANT_LANE_ROUTES, status: "PERSISTENT_LOCAL_CONTRACT" },
  };
  const configs = { "/tenant/config_excel": { title:"Cấu hình xuất excel báo cáo", columns:[{key:"no",label:"No."},{key:"report_name",label:"Báo cáo"},{key:"enabled",label:"Tắt/bật excel báo cáo"},{key:"all",label:"Tất cả"}], filters:Array.from({length:60},(_,i)=>({kind:"checkbox",name:i===0?"check_all":`publish_export_excel_${i}`,label:""})), tabs:["Cấu hình xuất excel báo cáo"], buttons:[], fields:[] } };
  for (const route of TENANT_LANE_ROUTES) centerEdu.registerScreen?.(route, async () => false);
  return { routes: TENANT_LANE_ROUTES, status: "PERSISTENT_LOCAL_CONTRACT" };
}

