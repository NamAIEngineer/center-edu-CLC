import assert from 'node:assert/strict';
import test from 'node:test';
import { courseDetailModal, renderCourseRoute } from '../static/modules/training_routes.js';

class Node {
  constructor(tag = 'div') { this.tagName = tag.toUpperCase(); this.children = []; this.parentNode = null; this.listeners = {}; this.dataset = {}; this.attributes = {}; this.className = ''; this.value = ''; this.hidden = false; }
  append(...nodes) { for (const node of nodes) { if (node == null) continue; node.parentNode = this; this.children.push(node); } }
  replaceChildren(...nodes) { this.children = []; this.append(...nodes); }
  remove() { this.parentNode?.children.splice(this.parentNode.children.indexOf(this), 1); }
  addEventListener(type, fn) { (this.listeners[type] ||= []).push(fn); }
  async click() { for (const fn of this.listeners.click || []) await fn({ target: this }); }
  setAttribute(name, value) { this.attributes[name] = String(value); }
  matches(selector) { if (selector.startsWith('.')) return this.className.split(/\s+/).includes(selector.slice(1)); if (selector.startsWith('[')) return false; return this.tagName.toLowerCase() === selector.toLowerCase(); }
  querySelectorAll(selector) { return this.children.flatMap((child) => [ ...(child.matches?.(selector) ? [child] : []), ...(child.querySelectorAll?.(selector) || []) ]); }
  querySelector(selector) { return this.querySelectorAll(selector)[0] || null; }
  get textContent() { return this._text ?? this.children.map((child) => child.textContent).join(''); }
  set textContent(value) { this._text = String(value ?? ''); this.children = []; }
}

const documentShim = { body: new Node('body'), createElement: (tag) => new Node(tag) };

test('course actions use loaded row IDs and detail values stay text', async () => {
  const previousDocument = globalThis.document;
  globalThis.document = documentShim;
  const calls = [];
  const rows = [{ id: 17, name: 'Safe course', code: 'SAFE' }, { id: 23, name: 'Second', code: 'SECOND' }];
  const api = async (endpoint, options) => {
    calls.push([endpoint, options]);
    if (endpoint === '/api/courses') return { rows };
    if (endpoint === '/api/courses/17') return { data: { name: '<img src=x onerror=alert(1)>', code: '<b>evil</b>', subject: '<script>bad()</script>' } };
    return { ok: true };
  };
  try {
    const target = new Node('main');
    await renderCourseRoute(target, { api });
    const topDuplicate = target.querySelectorAll('button').find((button) => button.textContent === 'Nhân bản');
    await topDuplicate.click();
    const rowDuplicate = target.querySelectorAll('button').find((button) => button.className === 'small-action course-duplicate' && button.dataset.id === '23');
    await rowDuplicate.click();
    assert.deepEqual(calls.filter(([endpoint]) => endpoint.includes('/duplicate')).map(([endpoint]) => endpoint), ['/api/courses/17/duplicate', '/api/courses/23/duplicate']);

    await courseDetailModal(api, 17);
    await new Promise((resolve) => queueMicrotask(resolve));
    const modal = documentShim.body.querySelector('.modal-backdrop');
    assert.ok(modal);
    assert.equal(modal.querySelector('img'), null);
    assert.equal(modal.querySelector('script'), null);
    assert.match(modal.textContent, /<img src=x onerror=alert\(1\)>/);
    assert.match(modal.textContent, /<b>evil<\/b>/);
  } finally {
    // The renderer reconciles page-size controls after the shell's async pass.
    // Keep the owned document alive until that scheduled callback completes.
    await new Promise((resolve) => setTimeout(resolve, 250));
    globalThis.document = previousDocument; documentShim.body.replaceChildren();
  }
});
