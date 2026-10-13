import { h } from './dom';
import type { Screen } from './screens';
export const dailyScreen: Screen = {
  render(c) { c.appendChild(h('div', { class: 'card' }, h('h2', null, 'daily'), h('p', { class: 'muted' }, 'Screen not built yet.'))); },
};
