const STUDENT_ROUTE = '/center/upload_address';
const CUSTOMER_ROUTE = '/center/upload_address/index_customer';
const STUDENT_COLUMNS = [['branch','Chi nhánh'],['student_code','Mã học viên'],['student_name','Học viên'],['identity_code','Mã định danh'],['english_name','Tên tiếng anh'],['gender','Giới tính'],['dob','Ngày sinh'],['username','Tài khoản'],['phone','SĐT'],['email','Email'],['old_province','Tỉnh cũ'],['old_district','Huyện cũ'],['old_ward','Xã phường'],['new_province','Tỉnh mới'],['new_ward','Phường xã mới']];
const CUSTOMER_COLUMNS = [['branch','Chi nhánh'],['customer_name','Họ tên khách hàng'],['customer_dob','Ngày sinh khách hàng'],['customer_gender','Giới tính khách hàng'],['customer_code','Mã khách hàng'],['identity_code','Mã định danh'],['phone','SĐT'],['email','Email'],['old_province','Tỉnh cũ'],['old_district','Huyện cũ'],['old_ward','Xã phường'],['new_province','Tỉnh mới'],['new_ward','Phường xã mới']];
const h = value => String(value ?? '').replace(/[&<>"']/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
const routeTo = route => { if (location.pathname === route) return; history.pushState({}, '', route); dispatchEvent(new PopStateEvent('popstate')); };
export function bindAddressImport(route, screen, records = []) {
  if (![STUDENT_ROUTE,CUSTOMER_ROUTE].includes(route) || !screen) return false;
  const customer = route === CUSTOMER_ROUTE, columns = customer ? CUSTOMER_COLUMNS : STUDENT_COLUMNS;
  const required = customer ? ['branch','customer_name','customer_code'] : ['branch','student_code','student_name'];
  const labels = Object.fromEntries(columns);
  const headerMap = new Map(columns.map(([key,label]) => [label.toLocaleLowerCase('vi'),key]));
  const tabs = [...screen.querySelectorAll('.ref-tab')];
  tabs.forEach((tab,index) => {
    const active = customer ? index === 1 : index === 0;
    tab.classList.toggle('active',active); tab.setAttribute('aria-selected',String(active));
    if (tab.dataset.addressNavBound === 'true') return;
    tab.dataset.addressNavBound = 'true';
    tab.addEventListener('click',() => routeTo(index === 1 ? CUSTOMER_ROUTE : STUDENT_ROUTE));
  });
  const input = screen.querySelector('input[type=file]');
  if (input) input.setAttribute('aria-label', customer ? 'Tệp import địa chỉ khách hàng tiềm năng' : 'Tệp import địa chỉ học viên');
  const table = screen.querySelector('table'), head = table?.querySelector('thead tr:first-child'), body = table?.querySelector('tbody');
  if (head) head.innerHTML = [['no','No.'],...columns].map(([,label])=>`<th scope="col">${h(label)}</th>`).join('');
  const pageSizeControl = screen.querySelector('.upload-address-footer select');
  if (pageSizeControl) { pageSizeControl.value = '25'; pageSizeControl.setAttribute('aria-label','Hiển thị 5 10 25 50 bản ghi'); }
  if (!screen._addressImport || screen._addressImport.route !== route) screen._addressImport = {route,preview:null,saved:0,page:0,error:''};
  const state = screen._addressImport;
  const renderRows = rows => {
    if (!body) return;
    const size = Math.max(1,Number(pageSizeControl?.value || 25)), pages = Math.max(1,Math.ceil(rows.length/size));
    state.page = Math.min(state.page,pages-1); const start = state.page*size, shown = rows.slice(start,start+size);
    body.innerHTML = shown.length ? shown.map((item,i)=>`<tr${item.id?` data-record-id="${Number(item.id)}"`:''}><td>${start+i+1}</td>${columns.map(([key])=>`<td>${h(item.data?.[key] ?? item[key] ?? '')}</td>`).join('')}</tr>`).join('') : `<tr class="empty-row"><td colspan="${columns.length+1}">Không tìm thấy dữ liệu</td></tr>`;
    const count = screen.querySelector('.upload-address-footer > span'); if (count) count.textContent = `Hiển thị ${rows.length?start+1:0} đến ${Math.min(start+size,rows.length)} của ${rows.length} bản ghi`;
    const [prev,next] = screen.querySelectorAll('.upload-address-pagination button');
    if (prev && next) { prev.disabled=state.page===0; next.disabled=state.page>=pages-1; prev.onclick=()=>{state.page=Math.max(0,state.page-1);renderRows(rows)};next.onclick=()=>{state.page=Math.min(pages-1,state.page+1);renderRows(rows)}; }
  };
  if (pageSizeControl && pageSizeControl.dataset.addressPageBound !== 'true') { pageSizeControl.dataset.addressPageBound='true'; pageSizeControl.addEventListener('change',()=>{state.page=0;renderRows(state.preview||records)}); }
  const error = message => { state.error=message;let note=screen.querySelector('.address-import-error');if(!note){note=document.createElement('p');note.className='error address-import-error';screen.querySelector('.upload-address-save')?.before(note);}note.textContent=message; };
  renderRows(state.preview || records);
  screen._addressInputHandler = async event => {
    const file=event.target.closest?.('input[type=file]'); if(!file||!screen.contains(file))return;
    event.stopImmediatePropagation(); state.preview=null;state.saved=0;state.page=0;state.error='';
    try {
      const csv=parseCsv(await readText(file.files?.[0])); if(csv.length<2)throw new Error('Tệp CSV chưa có dòng dữ liệu.');
      const headers=csv[0].map(cell=>cell.trim().replace(/^\uFEFF/,''));
      const keys=headers.map(label=>headerMap.get(label.toLocaleLowerCase('vi'))||'');
      const unknown=headers.filter((_,i)=>!keys[i]); if(unknown.length)throw new Error(`Cột CSV không được hỗ trợ: ${unknown.join(', ')}`);
      const duplicates=keys.filter((key,i)=>keys.indexOf(key)!==i); if(duplicates.length)throw new Error(`Cột CSV bị trùng: ${duplicates.map(key=>labels[key]).join(', ')}`);
      const missing=required.filter(key=>!keys.includes(key)); if(missing.length)throw new Error(`Thiếu cột bắt buộc: ${missing.map(key=>labels[key]).join(', ')}`);
      const rows=csv.slice(1).filter(row=>row.some(cell=>cell.trim())).map((row,index)=>{
        if(row.length>headers.length)throw new Error(`Dòng ${index+2} có nhiều giá trị hơn tiêu đề.`);
        const data={};columns.forEach(([key])=>{const col=keys.indexOf(key);data[key]=col<0?'':String(row[col]||'').trim();});
        const missingValues=required.filter(key=>!data[key]);if(missingValues.length)throw new Error(`Dòng ${index+2} thiếu: ${missingValues.map(key=>labels[key]).join(', ')}`);return data;
      });
      if(!rows.length)throw new Error('Tệp CSV không có dòng dữ liệu hợp lệ.');state.preview=rows;renderRows(rows);const saveButton=screen.querySelector('[data-w6-action="save-address"]');if(saveButton)saveButton.disabled=false;
    } catch (cause) { renderRows([]); error(cause.message||'Không đọc được tệp CSV.'); }
  };
  if(!screen.dataset.addressImportDelegate){screen.dataset.addressImportDelegate='true';screen.addEventListener('change',event=>screen._addressInputHandler?.(event),true);}
  const save=screen.querySelector('[data-w6-action="save-address"]');
  if(save){save.disabled=!state.preview?.length;if(save.dataset.addressSaveBound!=='true'){save.dataset.addressSaveBound='true';save.addEventListener('click',async()=>{
    const rows=state.preview||[];if(!rows.length)return;save.disabled=true;
    try { for(let i=state.saved;i<rows.length;i++){await window.CenterEdu.api('/api/generated/screens',{method:'POST',body:{route,data:rows[i]}});state.saved=i+1;} state.preview=null;location.reload(); }
    catch(cause){save.disabled=false;error(`${cause.message||'Không thể lưu tệp địa chỉ'}${state.saved?` Đã lưu ${state.saved} dòng; lần nữa sẽ tiếp tục từ dòng ${state.saved+1}.`:''}`);}
  });}}
  if(state.error)error(state.error);
  return true;
}
async function readText(file){if(file?.text)return file.text();return new Promise((resolve,reject)=>{const reader=new FileReader();reader.onload=()=>resolve(String(reader.result||''));reader.onerror=()=>reject(reader.error||new Error('Không đọc được tệp CSV'));reader.readAsText(file);});}
function parseCsv(text){text=String(text??'').replace(/^\uFEFF/,'');const rows=[];let row=[],value='',quoted=false,closed=false;for(let i=0;i<text.length;i++){const ch=text[i];if(quoted){if(ch==='"'&&text[i+1]==='"'){value+='"';i++;}else if(ch==='"'){quoted=false;closed=true;}else value+=ch;continue;}if(ch==='"'){if(value.length||closed)throw new Error('Dấu ngoặc kép CSV không hợp lệ.');quoted=true;}else if(ch===','){row.push(value);value='';closed=false;}else if(ch==='\n'||ch==='\r'){if(ch==='\r'&&text[i+1]==='\n')i++;row.push(value);if(row.some(cell=>cell.trim()))rows.push(row);row=[];value='';closed=false;}else{if(closed&&!/\s/.test(ch))throw new Error('Có ký tự thừa sau dấu ngoặc kép CSV.');value+=ch;}}if(quoted)throw new Error('Tệp CSV có trường chưa đóng dấu ngoặc kép.');row.push(value);if(row.some(cell=>cell.trim()))rows.push(row);return rows;}
