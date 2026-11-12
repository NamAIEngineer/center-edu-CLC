import assert from 'node:assert/strict';
import {filterCallStatistics} from '../static/modules/call_statistic.js';
const rows=[{data:{direction:'inbound',from_date:'2026-11-10'}},{data:{direction:'outbound',from_date:'2026-11-10'}},{data:{direction:'inbound',from_date:'2026-11-09'}}];
assert.deepEqual(filterCallStatistics(rows,{from:'10/11/2026',to:'10-11-2026'}),[rows[0]]);
assert.deepEqual(filterCallStatistics(rows,{direction:'outbound'}),[rows[1]]);
assert.deepEqual(filterCallStatistics(rows,{from:'11/11/2026'}),[]);
