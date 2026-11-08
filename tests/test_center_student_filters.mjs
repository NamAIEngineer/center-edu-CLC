import assert from "node:assert/strict";
import fs from "node:fs";
import test from "node:test";
import { STUDENT_FILTERS } from "../static/modules/center_lane.js";

test("student route exposes observed compact multi-select filter contract", () => {
  assert.equal(STUDENT_FILTERS.length, 7);
  const multi = STUDENT_FILTERS.filter((filter) => filter.kind === "multi-select");
  assert.deepEqual(multi.map((filter) => filter.placeholder), ["Chọn trạng thái", "Chọn lớp học"]);
  assert.deepEqual(multi[0].options, [
    "Đang học", "Bảo lưu", "Chuyển lớp", "Đã xong", "Nghỉ học", "Chưa học", "Chưa có lớp",
  ]);
  assert.equal(multi[1].options, undefined);
  assert.deepEqual(STUDENT_FILTERS.map((filter) => filter.placeholder), [
    "Tìm kiếm...", "Tìm phụ huynh", "Chọn trạng thái", "Chọn lớp học",
    "Nguồn giới thiệu", "Chọn năm", "Chọn trường học",
  ]);
});

test("student renderer keeps the observed action and empty-note contract", () => {
  const source = fs.readFileSync(new URL("../static/app.js", import.meta.url), "utf8");
  const studentSection = source.slice(source.indexOf("async function students(el)"), source.indexOf("async function teachers(el)"));
  assert.match(studentSection, /center-student-observed-filters/);
  assert.match(studentSection, /id=\"export-students\"/);
  assert.match(studentSection, /id=\"import-students\"/);
  assert.match(studentSection, /id=\"add-student\"/);
  assert.doesNotMatch(studentSection, /student-filter-clear/);
  assert.match(studentSection, /esc\(x\.note\|\|''\)/);
  assert.match(studentSection, /student-more/);
  assert.match(studentSection, /student-edit/);
  assert.match(source, /center-student-observed-filters.*return;/s);
});
