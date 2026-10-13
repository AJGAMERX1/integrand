import { h } from './dom';
import type { Screen } from './screens';
export const progressScreen: Screen = {
  render(c) { c.appendChild(h('div', { class: 'card' }, h('h2', null, 'progress'), h('p', { class: 'muted' }, 'Screen not built yet.'))); },
};
