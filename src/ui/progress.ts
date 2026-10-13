// Progress screen: study time, streak, 14-day charts (pure SVG), mastery by group, due reviews, recent sessions.
import { h, clear } from './dom';
import { navigate } from './router';
import type { Screen } from './screens';
import { isNodeMastered, masteryBar, stewartLabel } from './map';
import { curriculum, getNode } from '../data/load';
import { getSettings } from '../db/db';
import { loadAttempts, loadDaily, loadSessions, loadSkillStates, loadStudyLog } from '../db/state';
import { addDays, diffDays, prettyDate, today } from '../lib/date';
import { computeStreak } from '../daily';
import { dueReviews, masteryLabel } from '../engine';
import type { AttemptRecord, CurriculumNode, SessionRecord, SkillState, StudyKind, StudyLog } from '../types';

const SVG_NS = 'http://www.w3.org/2000/svg';

function svg<K extends keyof SVGElementTagNameMap>(tag: K, attrs: Record<string, string | number> = {}, ...children: (Node | string)[]): SVGElementTagNameMap[K] {
  const el = document.createElementNS(SVG_NS, tag);
  for (const [k, v] of Object.entries(attrs)) el.setAttribute(k, String(v));
  for (const c of children) el.appendChild(typeof c === 'string' ? document.createTextNode(c) : c);
  return el;
}

const KINDS: StudyKind[] = ['read', 'problems', 'review', 'daily', 'flow', 'concept', 'manual'];
const KIND_LABEL: Record<StudyKind, string> = { read: 'Reading', problems: 'Problems', review: 'Review', daily: 'Daily Integral', flow: 'Flow timer', concept: 'Concept', manual: 'Manual' };
/** Colors come from CSS variables set in styles.css under ui-more. */
const KIND_VAR: Record<StudyKind, string> = { read: '--k-read', problems: '--k-problems', review: '--k-review', daily: '--k-daily', flow: '--k-flow', concept: '--k-concept', manual: '--k-manual' };

function lastNDays(n: number, end: string): string[] {
  const out: string[] = [];
  for (let i = n - 1; i >= 0; i--) out.push(addDays(end, -i));
  return out;
}

function fmtHours(min: number): string {
  if (min < 60) return `${Math.round(min)}m`;
  const hrs = min / 60;
  return hrs >= 10 ? `${Math.round(hrs)}h` : `${hrs.toFixed(1)}h`;
}

/** ---------- Big stats ---------- */

function bigStats(logs: StudyLog[], sessions: SessionRecord[], streak: { current: number; best: number }, date: string): HTMLElement {
  const totalMin = logs.reduce((a, l) => a + l.minutes, 0);
  const days14 = new Set(lastNDays(14, date));
  const min14 = logs.filter((l) => days14.has(l.date)).reduce((a, l) => a + l.minutes, 0);
  const month = date.slice(0, 7);
  const monthDays = new Set(sessions.filter((s) => s.completedAt !== null && s.date.startsWith(month)).map((s) => s.date)).size;
  const stat = (n: string, l: string, sub?: string) => h('div', null, h('div', { class: 'n' }, n), h('div', { class: 'l' }, l), sub ? h('div', { class: 'l muted' }, sub) : null);
  return h('div', { class: 'card' },
    h('div', { class: 'bigstat progress-stats' },
      stat(fmtHours(totalMin), 'logged all-time'),
      stat(`${Math.round(min14 / 14)}`, 'avg min/day', 'last 14 days'),
      stat(`${streak.current}`, 'integral streak', `best ${streak.best}`),
      stat(`${monthDays}`, 'session days', 'this month'),
    ),
  );
}

/** ---------- 14-day minutes bar chart ---------- */

function minutesChart(logs: StudyLog[], date: string): HTMLElement {
  const days = lastNDays(14, date);
  const perDay = new Map<string, Partial<Record<StudyKind, number>>>(days.map((d) => [d, {}]));
  for (const l of logs) {
    const bucket = perDay.get(l.date);
    if (!bucket) continue;
    bucket[l.kind] = (bucket[l.kind] ?? 0) + l.minutes;
  }
  const totals = days.map((d) => Object.values(perDay.get(d)!).reduce((a, b) => a + (b ?? 0), 0));
  const max = Math.max(30, ...totals);
  const usedKinds = KINDS.filter((k) => days.some((d) => (perDay.get(d)![k] ?? 0) > 0));

  const W = 340, H = 150, padL = 28, padB = 22, padT = 8;
  const chartW = W - padL - 6, chartH = H - padB - padT;
  const slot = chartW / 14, barW = slot * 0.62;
  const root = svg('svg', { viewBox: `0 0 ${W} ${H}`, class: 'chart', role: 'img', 'aria-label': 'Minutes studied per day, last 14 days' });

  // Gridlines at 0, max/2, max.
  for (const frac of [0, 0.5, 1]) {
    const y = padT + chartH - frac * chartH;
    root.appendChild(svg('line', { x1: padL, x2: W - 6, y1: y, y2: y, class: 'chart-grid' }));
    root.appendChild(svg('text', { x: padL - 4, y: y + 4, class: 'chart-tick', 'text-anchor': 'end' }, String(Math.round(max * frac))));
  }

  days.forEach((d, i) => {
    const x = padL + i * slot + (slot - barW) / 2;
    let yTop = padT + chartH;
    const isToday = d === date;
    if (isToday) root.appendChild(svg('rect', { x: padL + i * slot, y: padT, width: slot, height: chartH, class: 'chart-today' }));
    for (const k of KINDS) {
      const m = perDay.get(d)![k] ?? 0;
      if (m <= 0) continue;
      const hgt = (m / max) * chartH;
      yTop -= hgt;
      root.appendChild(svg('rect', { x, y: yTop, width: barW, height: hgt, rx: 2, style: `fill: var(${KIND_VAR[k]})` }, svg('title', {}, `${prettyDate(d)}: ${Math.round(m)} min ${KIND_LABEL[k]}`)));
    }
    if (totals[i] > 0) root.appendChild(svg('text', { x: x + barW / 2, y: Math.max(padT + 9, yTop - 3), class: 'chart-val', 'text-anchor': 'middle' }, String(Math.round(totals[i]))));
    const label = i === 13 ? 'today' : (i % 2 === 1 ? d.slice(8).replace(/^0/, '') : '');
    if (label) root.appendChild(svg('text', { x: x + barW / 2, y: H - 6, class: `chart-tick ${isToday ? 'chart-tick-today' : ''}`, 'text-anchor': 'middle' }, label));
  });

  const legend = h('div', { class: 'chart-legend' }, ...(usedKinds.length ? usedKinds : ['read' as StudyKind]).map((k) =>
    h('span', { class: 'legend-item' }, h('span', { class: 'legend-swatch', style: { background: `var(${KIND_VAR[k]})` } }), KIND_LABEL[k])));

  const sum14 = totals.reduce((a, b) => a + b, 0);
  return h('div', { class: 'card' },
    h('div', { class: 'row spread' }, h('h3', null, 'Minutes per day'), h('span', { class: 'small muted' }, `${Math.round(sum14)} min in 14 days`)),
    sum14 > 0 ? root : h('p', { class: 'muted small' }, 'No study time logged in the last 14 days yet. Minutes from the flow timer and sessions show up here.'),
    sum14 > 0 ? legend : null,
  );
}

/** ---------- 14-day accuracy line ---------- */

function accuracyChart(attempts: AttemptRecord[], date: string): HTMLElement {
  const days = lastNDays(14, date);
  const stats = days.map((d) => {
    const mine = attempts.filter((a) => a.date === d && a.context !== 'placement');
    const correct = mine.filter((a) => a.correct && !a.revealed).length;
    return { d, total: mine.length, correct };
  });
  const withData = stats.filter((s) => s.total > 0);
  const totalAll = withData.reduce((a, s) => a + s.total, 0);
  const correctAll = withData.reduce((a, s) => a + s.correct, 0);

  const card = h('div', { class: 'card' });
  card.appendChild(h('div', { class: 'row spread' }, h('h3', null, 'Accuracy'), totalAll > 0 ? h('span', { class: 'small muted' }, `${correctAll}/${totalAll} correct in 14 days`) : null));

  if (withData.length < 2 || totalAll < 5) {
    card.appendChild(h('p', { class: 'muted small' }, totalAll === 0
      ? 'No problems attempted in the last 14 days.'
      : `${correctAll} of ${totalAll} correct in the last 14 days. A line appears once there are a few more days of data.`));
    return card;
  }

  const W = 340, H = 120, padL = 32, padB = 20, padT = 8;
  const chartW = W - padL - 8, chartH = H - padB - padT;
  const root = svg('svg', { viewBox: `0 0 ${W} ${H}`, class: 'chart', role: 'img', 'aria-label': 'Daily accuracy, last 14 days' });
  for (const frac of [0, 0.5, 1]) {
    const y = padT + chartH - frac * chartH;
    root.appendChild(svg('line', { x1: padL, x2: W - 8, y1: y, y2: y, class: 'chart-grid' }));
    root.appendChild(svg('text', { x: padL - 4, y: y + 4, class: 'chart-tick', 'text-anchor': 'end' }, `${frac * 100}%`));
  }
  const xOf = (i: number) => padL + (i / 13) * chartW;
  const yOf = (p: number) => padT + chartH - p * chartH;
  let path = '';
  stats.forEach((s, i) => {
    if (s.total === 0) return;
    const p = s.correct / s.total;
    path += `${path ? ' L' : 'M'}${xOf(i).toFixed(1)} ${yOf(p).toFixed(1)}`;
  });
  root.appendChild(svg('path', { d: path, class: 'chart-line' }));
  stats.forEach((s, i) => {
    if (s.total === 0) return;
    const p = s.correct / s.total;
    root.appendChild(svg('circle', { cx: xOf(i), cy: yOf(p), r: s.d === date ? 4.5 : 3, class: `chart-dot ${s.d === date ? 'chart-dot-today' : ''}` },
      svg('title', {}, `${prettyDate(s.d)}: ${s.correct}/${s.total} (${Math.round(p * 100)}%)`)));
  });
  days.forEach((d, i) => {
    const label = i === 13 ? 'today' : (i % 2 === 1 ? d.slice(8).replace(/^0/, '') : '');
    if (label) root.appendChild(svg('text', { x: xOf(i), y: H - 5, class: 'chart-tick', 'text-anchor': 'middle' }, label));
  });
  card.appendChild(root);
  return card;
}

/** ---------- Mastery by group ---------- */

function masteryOverview(states: Map<string, SkillState>): HTMLElement {
  const groups: { name: string; nodes: CurriculumNode[] }[] = [];
  for (const n of curriculum.nodes) {
    const g = groups[groups.length - 1];
    if (!g || g.name !== n.group) groups.push({ name: n.group, nodes: [n] }); else g.nodes.push(n);
  }
  const card = h('div', { class: 'card' }, h('h3', null, 'Mastery by chapter'));
  for (const g of groups) {
    const avg = g.nodes.reduce((a, n) => a + (states.get(n.id)?.mastery ?? 0), 0) / g.nodes.length;
    const mastered = g.nodes.filter((n) => isNodeMastered(n, states.get(n.id))).length;
    const detail = h('div', { class: 'group-detail hidden list' }, ...g.nodes.map((n) => {
      const st = states.get(n.id);
      return h('div', { class: 'group-node', role: 'button', tabindex: 0, onclick: () => navigate(`node/${n.id}`) },
        h('div', { class: 'row spread' }, h('span', { class: 'group-node-title' }, n.title), h('span', { class: 'small muted' }, stewartLabel(n))),
        masteryBar(st?.mastery ?? 0, { small: true }),
      );
    }));
    const head = h('div', { class: 'group-row', role: 'button', tabindex: 0, 'aria-expanded': 'false' },
      h('div', { class: 'row spread' }, h('span', { class: 'group-name' }, g.name), h('span', { class: 'small muted' }, `${mastered}/${g.nodes.length} · ${Math.round(avg * 100)}%`)),
      masteryBar(avg, { label: false, small: true }),
    );
    const toggle = () => { const open = detail.classList.toggle('hidden'); head.setAttribute('aria-expanded', String(!open)); };
    head.addEventListener('click', toggle);
    head.addEventListener('keydown', (e) => { if (e.key === 'Enter' || e.key === ' ') { e.preventDefault(); toggle(); } });
    card.append(head, detail);
  }
  return card;
}

/** ---------- Due reviews ---------- */

function dueList(states: Map<string, SkillState>, date: string): HTMLElement {
  const due = dueReviews(states, date).filter((s) => getNode(s.nodeId));
  const card = h('div', { class: 'card' }, h('div', { class: 'row spread' }, h('h3', null, 'Due for review'), h('span', { class: 'small muted' }, due.length ? `${due.length} skill${due.length === 1 ? '' : 's'}` : '')));
  if (due.length === 0) { card.appendChild(h('p', { class: 'muted small' }, 'Nothing is due. Reviews are scheduled 1, 3, 7, 14, and 30 days apart as you get them right.')); return card; }
  card.appendChild(h('div', { class: 'list' }, ...due.slice(0, 12).map((s) => {
    const n = getNode(s.nodeId)!;
    const overdue = diffDays(s.dueDate!, date);
    return h('div', { class: 'listitem', role: 'button', tabindex: 0, onclick: () => navigate(`node/${n.id}`) },
      h('div', null, h('div', null, n.title), h('div', { class: 'small muted' }, `${masteryLabel(s.mastery)} · ${overdue <= 0 ? 'due today' : `${overdue} day${overdue === 1 ? '' : 's'} overdue`}`)),
      h('span', { class: `chip ${overdue > 0 ? 'warn' : ''}`.trim() }, 'review'),
    );
  })));
  return card;
}

/** ---------- Recent sessions ---------- */

function recentSessions(sessions: SessionRecord[]): HTMLElement {
  const recent = sessions.slice().sort((a, b) => (a.date < b.date ? 1 : -1)).slice(0, 10);
  const card = h('div', { class: 'card' }, h('h3', null, 'Recent sessions'));
  if (recent.length === 0) { card.appendChild(h('p', { class: 'muted small' }, 'No sessions yet. Your first one is waiting on the Today screen.')); return card; }
  card.appendChild(h('div', { class: 'list' }, ...recent.map((s) => {
    const mins = Object.values(s.minutes).reduce((a, b) => a + (b ?? 0), 0);
    const blocks = s.blocksCompleted.length ? s.blocksCompleted.join(' · ') : 'no blocks completed';
    return h('div', { class: 'session-row' },
      h('div', { class: 'row spread' },
        h('span', null, prettyDate(s.date), h('span', { class: 'small muted' }, s.mode === 'dailyOnly' ? ' · integral only' : '')),
        h('span', { class: 'small muted' }, [mins > 0 ? `${Math.round(mins)} min` : null, s.confidence ? `confidence ${s.confidence}/5` : null].filter(Boolean).join(' · ')),
      ),
      h('div', { class: 'small muted' }, blocks),
      s.learned ? h('div', { class: 'session-learned' }, `“${s.learned}”`) : null,
    );
  })));
  return card;
}

/** ---------- Weekly summary ---------- */

function weeklyLine(logs: StudyLog[], date: string): HTMLElement {
  // Weeks start on Monday, per the local (Chicago) calendar date.
  const [y, m, d] = date.split('-').map(Number);
  const dow = (new Date(Date.UTC(y, m - 1, d)).getUTCDay() + 6) % 7; // 0 = Monday
  const thisStart = addDays(date, -dow);
  const lastStart = addDays(thisStart, -7);
  const sum = (from: string, to: string) => logs.filter((l) => l.date >= from && l.date < to).reduce((a, l) => a + l.minutes, 0);
  const thisWeek = sum(thisStart, addDays(thisStart, 7));
  const lastWeek = sum(lastStart, thisStart);
  const delta = thisWeek - lastWeek;
  const deltaText = lastWeek === 0 && thisWeek === 0 ? '' : delta === 0 ? ' · same as last week' : ` · ${delta > 0 ? '+' : '−'}${Math.round(Math.abs(delta))} min vs last week`;
  return h('div', { class: 'card card2 weekly-line' },
    h('div', { class: 'small muted' }, 'This week'),
    h('div', null, h('strong', null, `${Math.round(thisWeek)} min`), h('span', { class: 'muted' }, ` (last week ${Math.round(lastWeek)} min)${deltaText}`)),
  );
}

/** ---------- Screen ---------- */

export const progressScreen: Screen = {
  async render(container) {
    const date = today();
    const [states, attempts, sessions, logs, daily, settings] = await Promise.all([
      loadSkillStates(), loadAttempts(), loadSessions(), loadStudyLog(), loadDaily(), getSettings(),
    ]);
    const streak = computeStreak(daily, date, settings.streakRule);
    clear(container);
    container.append(
      h('h1', null, 'Progress'),
      bigStats(logs, sessions, streak, date),
      weeklyLine(logs, date),
      minutesChart(logs, date),
      accuracyChart(attempts, date),
      dueList(states, date),
      masteryOverview(states),
      recentSessions(sessions),
      h('p', { class: 'small muted progress-foot' }, `Streak rule: ${settings.streakRule === 'solved' ? 'solved only' : 'completion'} · ${streak.solved} solved, ${streak.completed} completed all-time. Change it in Settings.`),
    );
  },
};
