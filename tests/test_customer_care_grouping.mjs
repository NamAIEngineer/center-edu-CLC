import assert from 'node:assert/strict';
import { customerCareCenterRows } from '../static/modules/report_crm_center.js';
const records = [
  { branch:'Cơ sở A', sale_owner:'Sale A', status:'NEW' },
  { branch:'Cơ sở A', sale_owner:'Sale B', status:'CONTACTED' },
  { branch:'Cơ sở A', sale_owner:'Sale B', status:'UNKNOWN' },
  { branch:'Cơ sở B', sale_owner:'Sale C', status:'CONVERTED' },
];
const centers=customerCareCenterRows(records,'center');
assert.deepEqual(centers[0],{label:'Cơ sở A',total:3,processed:1,pending:1,rate:100/3});
assert.equal(centers[1].processed,1);
assert.deepEqual(customerCareCenterRows(records,'team'),[]);
const teams=customerCareCenterRows(records,'team',[{data:{full_name:'Sale A',team_name:'Nhóm A'}},{data:{full_name:'Sale B',team_name:'Nhóm A'}}]);
assert.equal(teams.length,1);
assert.equal(teams[0].total,3);
assert.equal(teams[0].pending,1);
assert.equal(customerCareCenterRows(records,'sale').find(row=>row.label==='Sale B').processed,1);
console.log('customer care explicit grouping: PASS');
