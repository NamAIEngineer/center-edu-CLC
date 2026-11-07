import assert from "node:assert/strict";
import test from "node:test";

import { register as registerCenter, CENTER_LANE_ROUTES } from "../../static/modules/center_lane.js";
import { register as registerSurvey, SURVEY_CONTRACT } from "../../static/modules/survey.js";
import { register as registerCso, CSO_LANE_ROUTES } from "../../static/modules/cso_lane.js";
import { register as registerCallcenter, CALLCENTER_LANE_ROUTES } from "../../static/modules/callcenter_lane.js";
import { register as registerTenant, TENANT_LANE_ROUTES } from "../../static/modules/tenant_lane.js";
import { register as registerOverrides } from "../../static/modules/w6_overrides.js";

test("W6 frontend register hooks expose every owned route and defer rendering", async () => {
  const screens = new Map();
  const centerEdu = {
    registerScreen(route, renderer) { screens.set(route, renderer); return true; },
  };
  const metadata = [
    registerCenter(centerEdu), registerSurvey(centerEdu), registerCso(centerEdu),
    registerCallcenter(centerEdu), registerTenant(centerEdu),
  ];
  const expected = [
    ...CENTER_LANE_ROUTES, SURVEY_CONTRACT.route, SURVEY_CONTRACT.createRoute,
    ...CSO_LANE_ROUTES, ...CALLCENTER_LANE_ROUTES, ...TENANT_LANE_ROUTES,
  ];
  assert.deepEqual([...screens.keys()], expected);
  for (const route of expected) assert.equal(await screens.get(route)(), false);
  assert.equal(metadata.length, 5);
  assert.equal(centerEdu.w6LaneMetadata.survey.status, "PERSISTENT_LOCAL_CONTRACT");
});

test("classroom override preserves the dedicated domain renderer", () => {
  const screens = new Map([["/setup/classroom", () => "domain"]]);
  const centerEdu = {
    registerScreen(route, renderer) { screens.set(route, renderer); return true; },
  };
  registerOverrides(centerEdu);
  assert.equal(screens.get("/setup/classroom")(), "domain");
  assert.equal(screens.has("/center/holiday/index"), true);
});
