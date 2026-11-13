import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';

const lane = readFileSync('modules/center_lane.py', 'utf8');
const renderer = readFileSync('static/modules/w6_screen_utils.js', 'utf8');
for (const field of ['select_class_ignore', 'is_send_noti', 'send_at', 'content']) assert.match(lane, new RegExp(field));
assert.match(lane, /_f\("status", "Trạng thái", "radio"/);
assert.match(renderer, /function openHolidayForm/);
assert.match(renderer, /w6-holiday-modal/);
assert.match(renderer, /route === '\/center\/holiday\/index'/);
assert.match(renderer, /type === 'datetime-local'/);
assert.match(renderer, /record\.updated_at/);
console.log('batch5 holiday form UI contract: PASS');
