import { h } from './dom';
import type { Screen } from './screens';
export const sessionScreen: Screen = {
  render(c) { c.appendChild(h('div', { class: 'card' }, h('h2', null, 'session'), h('p', { class: 'muted' }, 'Screen not built yet.'))); },
};
