/** Configuration driven report client. Backend remains the source of truth. */
export const reportEngine = {
  catalogUrl: '/api/reports/catalog',
  runUrl: '/api/reports/run',
  exportUrl: '/api/reports/export',
  async catalog() {
    const r = await fetch(this.catalogUrl);
    if (!r.ok) throw new Error(`Báo cáo không tải được (${r.status})`);
    return r.json();
  },
  async run(route, filters = {}, groupBy = '') {
    const q = new URLSearchParams({ route, ...filters });
    if (groupBy) q.set('group_by', groupBy);
    const r = await fetch(`${this.runUrl}?${q.toString()}`);
    if (!r.ok) throw new Error(`Báo cáo không chạy được (${r.status})`);
    return r.json();
  },
  exportUrlFor(route, filters = {}) {
    const q = new URLSearchParams({ route, ...filters });
    return `${this.exportUrl}?${q.toString()}`;
  },
};

export function reportColumns(definition) {
  return (definition?.columns || []).map(c => c.label || c.key);
}
