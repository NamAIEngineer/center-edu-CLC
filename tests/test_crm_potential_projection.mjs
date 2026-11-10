import assert from 'node:assert/strict';
import { POTENTIAL_PERIOD_TABS, potentialPeriodMatch } from '../static/modules/crm_potential_period.js';

assert.deepEqual(POTENTIAL_PERIOD_TABS, ['Tất cả', 'Hôm nay', 'Tuần này', 'Tháng này', 'Chưa xử lý']);
const anchor = new Date(2026, 10, 10, 15);
const records = [
  { id: 1, created_at: '2026-11-10 08:00:00', status: 'NEW' },
  { id: 2, created_at: '2026-11-09 17:00:00', status: 'CONTACTED' },
  { id: 3, created_at: '2026-11-08', status: 'QUALIFIED' },
  { id: 4, created_at: '2026-10-31', status: 'CONVERTED' },
  { id: 5, created_at: '', status: 'NEW' },
];
const ids = period => records.filter(row => potentialPeriodMatch(row, period, anchor)).map(row => row.id);
assert.deepEqual(ids('all'), [1, 2, 3, 4, 5]);
assert.deepEqual(ids('today'), [1]);
assert.deepEqual(ids('week'), [1, 2]);
assert.deepEqual(ids('month'), [1, 2, 3]);
assert.deepEqual(ids('pending'), [1, 5]);
assert.equal(potentialPeriodMatch({ created_at: '2026-11-16' }, 'week', anchor), false);
assert.equal(potentialPeriodMatch({ created_at: 'not-a-date' }, 'today', anchor), false);
console.log('crm potential period boundaries: PASS');
