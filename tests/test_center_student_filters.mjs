import assert from "node:assert/strict";
import test from "node:test";
import { STUDENT_FILTERS } from "../static/modules/center_lane.js";

test("student route exposes observed compact multi-select filter contract", () => {
  const multi = STUDENT_FILTERS.filter((filter) => filter.kind === "multi-select");
  assert.deepEqual(multi.map((filter) => filter.placeholder), ["Chọn trạng thái", "Chọn lớp học", "Nguồn"]);
  assert.deepEqual(multi.map((filter) => filter.options), [
    ["Đang học", "Bảo lưu", "Chuyển lớp", "Đã xong", "Nghỉ học", "Chưa học", "Chưa có lớp"],
    ["Chọn lớp học", "Lớp Tiếng Anh giao tiếp A1", "Lớp IELTS Foundation"],
    ["Phụ huynh", "Giáo viên", "Nhân viên", "Học viên"],
  ]);
  assert.equal(STUDENT_FILTERS.at(-1).placeholder, "Hiển thị 10 25 50 100 bản ghi");
});
