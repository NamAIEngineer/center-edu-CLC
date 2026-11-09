import { financePresentation, bindFinanceRouteTabs } from './finance_tab_views.js';
/* Finance pricing assessment screen contract for /finance/assessment. */
export const financeAssessment = {
  route: '/finance/assessment',
  tabs: ['Ưu đãi - Khuyến mãi', 'Gói học phí', 'Định giá', 'Định giá gói học phí'],
  columns: ['No.', 'Tên', 'Ngày áp dụng', 'Nhân viên định giá', 'Khóa học liên quan'],
  filters: ['q', 'status'],
  pageSizes: [5, 10, 25, 50],
  statusLabels: Object.freeze({ ACTIVE: 'Đang áp dụng', INACTIVE: 'Tạm khóa' }),
  actions: ['Lưu định giá', 'Excel'],
  form: [
    { name: 'fullname', label: 'Tên định giá', required: true },
    { name: 'date_apply', label: 'Ngày áp dụng', type: 'date-text', required: true },
    { name: 'course_id', label: 'Khóa học liên quan', type: 'select' },
    { name: 'old_price', label: 'Giá cũ', type: 'number' },
    { name: 'new_price', label: 'Giá mới', type: 'number' },
  ],
  permissions: { read: ['ADMIN', 'STAFF', 'TEACHER'], write: ['ADMIN', 'STAFF'] },
};

export const assessmentQuery = (filters = {}) => {
  const params = new URLSearchParams();
  financeAssessment.filters.forEach((key) => {
    const value = String(filters[key] ?? '').trim();
    if (value) params.set(key, value);
  });
  return params;
};

export const assessmentStatusLabel = (value) =>
  financeAssessment.statusLabels[String(value || '').toUpperCase()] || '';

export const loadAssessments = (apiFetch, filters = {}) =>
  apiFetch(`/api/finance/assessments?${assessmentQuery(filters)}`);

export const exportAssessments = (apiFetch, filters = {}) =>
  apiFetch(`/api/export/finance-assessments?${assessmentQuery(filters)}`);

function bindFinanceTabState(screen) { bindFinanceRouteTabs(screen, 'assessment'); }

export function register(global) {
  const host = global || {};
  host.financeAssessment = financeAssessment;
  const render = async (screen, context) => {
    const fn = globalThis.financeAssessments;
    if (typeof fn !== 'function') return false;
    await fn(screen, context);
    const packet = new URLSearchParams(location.search).get('view') === 'packet';
    const card = screen.querySelector('[data-table-card]');
    const registry = globalThis.CenterEdu?.state?.tableRegistry?.[card?.dataset.tableCard];
    if (registry) {
      const payload = await context.api('/api/finance/assessments?page_size=100');
      registry.rows = (payload.data?.items || []).filter(row => (row.assessment_scope || 'course') === (packet ? 'packet' : 'course'));
      if (packet) {
        registry.columns = registry.columns.map((column,index) => index === 4 ? {label:'Gói học phí liên quan',key:'packet_name'} : column);
        screen.querySelector('thead').innerHTML = `<tr>${registry.columns.map(column=>`<th>${column.label}</th>`).join('')}</tr>`;
        const create = screen.querySelector('#add-finance-assessment');
        create?.addEventListener('click',event=>{
          event.preventDefault();event.stopImmediatePropagation();
          const fields=globalThis.financeAssessmentFields().map(field=>field.name==='course_name'?{...field,name:'packet_name',label:'Gói học phí liên quan'}:field);
          globalThis.openJsonForm('Tạo định giá gói học phí','/api/finance/assessments',fields,()=>globalThis.render(),value=>({...value,assessment_scope:'packet'}));
        },true);
      }
      registry.render();
    }
    financePresentation(screen, 'assessment');
    bindFinanceTabState(screen);
    return true;
  };
  if (typeof host.registerScreen === 'function') host.registerScreen(financeAssessment.route, render);
  return financeAssessment;
}

