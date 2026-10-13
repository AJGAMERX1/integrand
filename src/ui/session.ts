// Session (#/session): runs today's blocks in order (review -> read -> problems -> daily -> exit) with a block timer
// and a progress strip. Every block is persisted when completed, so leaving and coming back resumes where you were.
import type { CurriculumNode, Problem, ReadingRecord, SessionBlock, SessionRecord, SkillState } from '../types';
import type { Screen } from './screens';
import { h, append, clear, toast } from './dom';
import { navigate } from './router';
import { richText } from './math';
import { renderProblem, type ProblemCardHandle } from './problemCard';
import { blockTimer, type BlockTimer } from './timer';
import { renderDailyIntegral, type DailyHandle } from './daily';
import { conceptFor, curriculum, getNode, problemsFor } from '../data/load';
import { getSettings } from '../db/db';
import { loadAttempts, loadDaily, loadReading, loadSessions, loadSkillStates, markRead, saveSkillState, seenProblemIds } from '../db/state';
import { today } from '../lib/date';
import { CONFIG } from '../lib/config';
import { applyAttempt, buildAssignment, initialSkillState, masteryLabel, pickProblems, type Assignment } from '../engine';
import { computeStreak } from '../daily';
import {
  BLOCK_TITLES, blockMinutes, blocksFor, completeBlock, currentBlock, describeReading, finishSession, minutesSpent, startSession,
} from '../session/machine';

interface Live {
  container: HTMLElement;
  assignment: Assignment;
  rec: SessionRecord;
  states: Map<string, SkillState>;
  reading: ReadingRecord[];
  seen: Set<string>;
  /** Mastery before this visit, for the exit summary. */
  before: Map<string, number>;
  timer: BlockTimer | null;
  card: ProblemCardHandle | null;
  daily: DailyHandle | null;
}

let live: Live | null = null;

function teardownBlock() {
  if (!live) return;
  live.timer?.stop(); live.timer = null;
  live.card?.destroy(); live.card = null;
  live.daily?.destroy(); live.daily = null;
}

function stateFor(nodeId: string): SkillState {
  const s = live?.states.get(nodeId);
  if (s) return s;
  try { return initialSkillState(nodeId); }
  catch {
    return { nodeId, mastery: 0, attempts: 0, firstTryStreak: 0, missStreak: 0, difficulty: 1, dueDate: null, intervalIndex: 0, lastPracticed: null };
  }
}

export const sessionScreen: Screen = {
  async render(c) {
    teardownBlock(); live = null;
    const settings = await getSettings();
    if (!settings.placementDone) { navigate('today'); return; }
    const [states, reading, sessions, seen] = await Promise.all([loadSkillStates(), loadReading(), loadSessions(), seenProblemIds()]);
    let assignment: Assignment;
    try { assignment = buildAssignment({ today: today(), curriculum, states, reading, sessions }); }
    catch (err) {
      console.error(err);
      c.appendChild(h('div', { class: 'card' },
        h('h2', null, 'Session unavailable'),
        h('p', { class: 'muted' }, 'The study engine could not build today’s assignment. Try the Daily Integral instead.'),
        h('button', { type: 'button', class: 'btn int block', onclick: () => navigate('daily') }, 'Daily Integral'),
      ));
      return;
    }
    const rec = await startSession(assignment, 'full');
    const before = new Map<string, number>();
    for (const id of [...assignment.reviewNodeIds, ...assignment.problemNodeIds]) before.set(id, states.get(id)?.mastery ?? 0);
    live = { container: c, assignment, rec, states, reading, seen, before, timer: null, card: null, daily: null };
    renderCurrent();
  },
  unmount() { teardownBlock(); live = null; },
};

function renderCurrent() {
  if (!live) return;
  teardownBlock();
  const c = live.container;
  clear(c);
  const block = currentBlock(live.rec);
  if (block === null) { void renderSummary(c); return; }
  window.scrollTo(0, 0);

  c.appendChild(progressStrip(live.rec, block));
  const timer = blockTimer(blockMinutes(block), () => { /* tick */ }, () => toast('Time for this block is up. Wrap up when ready.'), {
    persistKey: `integrand.block.${live.rec.date}.${block}`,
  });
  live.timer = timer;
  const skip = block === 'exit' ? null
    : h('button', { type: 'button', class: 'linkbtn small', onclick: () => void advance(block, true) }, 'Skip');
  c.appendChild(h('div', { class: 'blockhead' },
    h('div', null, h('h2', { style: { margin: 0 } }, BLOCK_TITLES[block]), h('div', { class: 'small muted' }, `${blockMinutes(block)} min`)),
    h('div', { class: 'row' }, timer.el, skip),
  ));

  const body = h('div', { class: 'blockbody' });
  c.appendChild(body);
  switch (block) {
    case 'review': renderReview(body); break;
    case 'read': renderRead(body); break;
    case 'problems': renderProblems(body); break;
    case 'daily': void renderDaily(body); break;
    case 'exit': renderExit(body); break;
  }
}

function progressStrip(rec: SessionRecord, current: SessionBlock): HTMLElement {
  const blocks = blocksFor(rec.mode);
  return h('div', { class: 'strip' }, ...blocks.map((b) => {
    const done = rec.blocksCompleted.includes(b);
    return h('div', { class: `seg${done ? ' done' : ''}${b === current ? ' current' : ''}`, title: BLOCK_TITLES[b] });
  }));
}

function nextButton(label: string, block: SessionBlock, enabled = true): HTMLButtonElement {
  return h('button', { type: 'button', class: 'btn block', disabled: !enabled, onclick: () => void advance(block, false) }, label);
}

/** Completes the current block with the timer's minutes and renders the next one. */
async function advance(block: SessionBlock, skipped: boolean) {
  if (!live) return;
  const minutes = live.timer?.elapsedMinutes() ?? 0;
  const nodeId = block === 'read' ? live.rec.readingNodeId : block === 'daily' ? null : live.assignment.focusNodeId;
  live.timer?.destroy(); live.timer = null;
  try { live.rec = await completeBlock(live.rec, block, minutes, nodeId); }
  catch (err) { console.error(err); toast('Could not save progress.'); }
  if (skipped) toast(`${BLOCK_TITLES[block]} skipped`);
  renderCurrent();
}

/** Grades flow shared by review and problems: apply the outcome to the skill state and persist it. */
async function applyResult(problem: Problem, r: { correct: boolean; hintsUsed: number; revealed: boolean }) {
  if (!live) return;
  const prev = stateFor(problem.skill);
  try {
    const next = applyAttempt(prev, { correct: r.correct, hintsUsed: r.hintsUsed, revealed: r.revealed }, today());
    live.states.set(problem.skill, next);
    await saveSkillState(next);
  } catch (err) { console.error('applyAttempt/saveSkillState failed', err); }
  live.seen.add(problem.id);
}

/** Runs a queue of problems one at a time, then calls onFinished. */
function runQueue(body: HTMLElement, queue: Problem[], context: 'review' | 'problems', block: SessionBlock) {
  let i = 0;
  const host = h('div');
  body.appendChild(host);
  const show = () => {
    if (!live) return;
    live.card?.destroy(); live.card = null;
    clear(host);
    if (i >= queue.length) {
      host.appendChild(h('div', { class: 'card' }, h('p', null, `${BLOCK_TITLES[block]} done.`), nextButton('Next', block)));
      return;
    }
    const p = queue[i];
    const node = getNode(p.skill);
    live.card = renderProblem(host, p, {
      context,
      heading: `${i + 1} of ${queue.length} · ${node?.title ?? p.skill}`,
      continueLabel: i + 1 < queue.length ? 'Next problem' : 'Finish block',
      onDone: (r) => { void applyResult(p, r); },
      onContinue: () => { i++; show(); },
    });
    window.scrollTo(0, 0);
  };
  show();
}

/** ---------- Review ---------- */
function renderReview(body: HTMLElement) {
  if (!live) return;
  const a = live.assignment;
  const queue: Problem[] = [];
  const missing: string[] = [];
  for (const id of a.reviewNodeIds) {
    if (queue.length >= CONFIG.session.reviewProblems) break;
    const bank = problemsFor(id);
    if (!bank.length) { missing.push(getNode(id)?.title ?? id); continue; }
    try { queue.push(...pickProblems(bank, stateFor(id), live.seen, 1)); }
    catch (err) { console.error(err); queue.push(bank[Math.floor(Math.random() * bank.length)]); }
  }
  if (!queue.length) {
    body.appendChild(h('div', { class: 'card' },
      h('h3', null, a.reviewNodeIds.length ? 'No review problems available' : 'Nothing due for review'),
      h('p', { class: 'muted' }, a.reviewNodeIds.length
        ? `No problems written yet for: ${missing.join(', ')}. Moving on.`
        : 'Reviews appear here when a skill you missed comes due.'),
      nextButton('Next', 'review'),
    ));
    return;
  }
  if (missing.length) body.appendChild(h('p', { class: 'small muted' }, `No problems yet for ${missing.join(', ')}.`));
  runQueue(body, queue, 'review', 'review');
}

/** ---------- Read ---------- */
function renderRead(body: HTMLElement) {
  if (!live) return;
  const a = live.assignment;
  const info = describeReading(a);
  const node: CurriculumNode | undefined = info.nodeId ? getNode(info.nodeId) : undefined;
  if (!info.nodeId || !node) {
    body.appendChild(h('div', { class: 'card' }, h('h3', null, 'No reading today'), h('p', { class: 'muted' }, 'Nothing assigned; go straight to the problems.'), nextButton('Next', 'read')));
    return;
  }
  const concept = conceptFor(node.id);
  const alreadyRead = live.reading.some((r) => r.nodeId === node.id && r.date === today());
  const next = nextButton('Next', 'read', alreadyRead);
  const markBtn = h('button', {
    type: 'button', class: 'btn good block',
    onclick: async (e: Event) => {
      const b = e.currentTarget as HTMLButtonElement;
      b.disabled = true;
      try { await markRead(node.id); b.textContent = 'Marked read ✓'; next.disabled = false; toast('Reading marked'); }
      catch (err) { console.error(err); b.disabled = false; toast('Could not save.'); }
    },
  }, alreadyRead ? 'Mark read again' : 'Mark read');

  const card = h('div', { class: 'card read-card' },
    h('div', { class: 'small muted' }, node.group),
    h('h3', { class: 'read-title' }, node.title),
    h('p', { class: 'reading-line' }, h('strong', null, info.sentence)),
    info.section && info.pages ? h('p', { class: 'small muted' }, `Stewart, Calculus: Early Transcendentals, 8th ed. · ${info.section}, ${info.pages}`) : null,
    node.summary ? h('p', { class: 'muted' }, node.summary) : null,
  );
  if (concept?.readingGuide?.length) {
    card.appendChild(h('details', { class: 'guide', open: true },
      h('summary', null, 'What to look for while reading'),
      h('ul', { class: 'guide-list' }, ...concept.readingGuide.map((g) => h('li', null, richText(g)))),
    ));
  }
  if (!info.pages) {
    // Ramp node without Stewart pages: the concept page is the reading.
    if (concept) {
      card.appendChild(h('div', { class: 'concept-inline' }, richText(concept.overview)));
      if (concept.keyIdeas?.length) {
        card.appendChild(h('h3', null, 'Key ideas'));
        card.appendChild(h('ul', { class: 'guide-list' }, ...concept.keyIdeas.map((k) => h('li', null, richText(k)))));
      }
      card.appendChild(h('p', { class: 'small' }, h('a', { href: `#/node/${encodeURIComponent(node.id)}` }, 'Open the full concept page (worked examples, common mistakes)')));
    } else {
      card.appendChild(h('p', { class: 'muted' }, 'The concept page for this skill is not written yet. Read what you can about it, then mark read.'));
    }
  } else {
    card.appendChild(h('p', { class: 'small' }, h('a', { href: `#/node/${encodeURIComponent(node.id)}` }, concept ? 'Read the concept page too' : 'Concept page (not written yet)')));
  }
  card.append(h('div', { class: 'stack', style: { marginTop: '12px' } }, markBtn, next));
  body.appendChild(card);
}

/** ---------- Problems ---------- */
function renderProblems(body: HTMLElement) {
  if (!live) return;
  const a = live.assignment;
  const ids = a.problemNodeIds.length ? a.problemNodeIds : [a.focusNodeId];
  const target = CONFIG.session.newProblemsMax;
  const queue: Problem[] = [];
  const pick = (id: string, n: number) => {
    if (n <= 0) return;
    const bank = problemsFor(id).filter((p) => !queue.some((q) => q.id === p.id));
    if (!bank.length) return;
    try { queue.push(...pickProblems(bank, stateFor(id), live!.seen, n)); }
    catch (err) { console.error(err); queue.push(...bank.slice(0, n)); }
  };
  // Focus node first (up to the minimum), then the other nodes, then back to the focus node to fill up.
  pick(ids[0], CONFIG.session.newProblemsMin);
  for (const id of ids.slice(1)) pick(id, target - queue.length);
  if (queue.length < target) pick(ids[0], target - queue.length);

  if (!queue.length) {
    body.appendChild(h('div', { class: 'card' },
      h('h3', null, 'No problems for this skill yet'),
      h('p', { class: 'muted' }, `The problem bank for ${getNode(ids[0])?.title ?? ids[0]} is still being written. Read the concept page instead, then move on.`),
      h('a', { class: 'btn ghost block', href: `#/node/${encodeURIComponent(ids[0])}`, style: { marginBottom: '10px' } }, 'Open the concept page'),
      nextButton('Next', 'problems'),
    ));
    return;
  }
  runQueue(body, queue, 'problems', 'problems');
}

/** ---------- Daily ---------- */
async function renderDaily(body: HTMLElement) {
  if (!live) return;
  const host = h('div');
  const next = nextButton('Next', 'daily');
  body.append(host, h('div', { class: 'card2 card', style: { marginTop: '4px' } }, next));
  live.daily = await renderDailyIntegral(host, today(), { embedded: true });
}

/** ---------- Exit ---------- */
function renderExit(body: HTMLElement) {
  if (!live) return;
  let confidence: SessionRecord['confidence'] = live.rec.confidence;
  const ta = h('textarea', { placeholder: 'e.g. The limit of a sum is the sum of the limits when both exist.', rows: 3 });
  ta.value = live.rec.learned ?? '';
  const confBtns = [1, 2, 3, 4, 5].map((n) => h('button', {
    type: 'button', class: `conf${confidence === n ? ' selected' : ''}`,
    onclick: () => { confidence = n as SessionRecord['confidence']; for (const b of confBtns) b.classList.toggle('selected', Number(b.dataset.n) === n); },
    'data-n': String(n),
  }, String(n)));
  const save = h('button', {
    type: 'button', class: 'btn block',
    onclick: async (e: Event) => {
      if (!live) return;
      const b = e.currentTarget as HTMLButtonElement;
      if (!ta.value.trim()) { toast('One sentence is enough.'); ta.focus(); return; }
      if (!confidence) { toast('Pick a confidence from 1 to 5.'); return; }
      b.disabled = true;
      const minutes = live.timer?.elapsedMinutes() ?? 0;
      live.timer?.destroy(); live.timer = null;
      try { live.rec = await finishSession(live.rec, { learned: ta.value, confidence }, minutes, live.assignment.focusNodeId); }
      catch (err) { console.error(err); toast('Could not save.'); b.disabled = false; return; }
      renderCurrent();
    },
  }, 'Save and finish');
  body.appendChild(h('div', { class: 'card' },
    h('h3', null, 'One sentence: what did you learn?'),
    ta,
    h('h3', { style: { marginTop: '14px' } }, 'How confident do you feel?'),
    h('div', { class: 'conf-row' }, ...confBtns),
    h('div', { class: 'row spread small muted', style: { marginBottom: '12px' } }, h('span', null, 'lost'), h('span', null, 'got it')),
    save,
  ));
}

/** ---------- Summary ---------- */
async function renderSummary(c: HTMLElement) {
  if (!live) return;
  const rec = live.rec;
  const date = rec.date;
  const [attempts, dailyRecords, settings, states] = await Promise.all([loadAttempts(), loadDaily(), getSettings(), loadSkillStates()]);
  const mine = attempts.filter((x) => x.date === date && (x.context === 'review' || x.context === 'problems'));
  const correct = mine.filter((x) => x.correct && !x.revealed).length;
  let streak = { current: 0, best: 0, solved: 0, completed: 0 };
  try { streak = computeStreak(dailyRecords, date, settings.streakRule); } catch { /* stub */ }
  const label = (m: number) => { try { return masteryLabel(m); } catch { return m >= 0.9 ? 'mastered' : m >= 0.7 ? 'solid' : m > 0 ? 'learning' : 'new'; } };

  const touched = [...new Set([...live.assignment.reviewNodeIds, ...live.assignment.problemNodeIds])];
  const changes = touched.map((id) => {
    const b = live!.before.get(id) ?? 0;
    const after = states.get(id)?.mastery ?? b;
    return { id, title: getNode(id)?.title ?? id, before: b, after };
  }).filter((x) => mine.some((m) => m.nodeId === x.id) || Math.abs(x.after - x.before) > 1e-9);

  const dailyToday = dailyRecords.find((r) => r.date === date && !r.isArchive);
  append(c, [
    h('h1', null, rec.mode === 'dailyOnly' ? 'Daily Integral done' : 'Session complete'),
    h('div', { class: 'card' },
      h('div', { class: 'bigstat' },
        h('div', null, h('div', { class: 'n' }, `${correct}/${mine.length}`), h('div', { class: 'l' }, 'problems')),
        h('div', null, h('div', { class: 'n' }, String(minutesSpent(rec))), h('div', { class: 'l' }, 'minutes')),
        h('div', null, h('div', { class: 'n' }, String(streak.current)), h('div', { class: 'l' }, 'day streak')),
      ),
      dailyToday ? h('p', { class: 'small muted', style: { marginTop: '10px', textAlign: 'center' } },
        `Daily Integral: ${dailyToday.outcome === 'solved' ? 'solved' : dailyToday.outcome === 'revealed' ? 'revealed' : 'not finished'}`) : null,
    ),
    changes.length ? h('div', { class: 'card' },
      h('h3', null, 'Skills touched'),
      h('div', { class: 'list' }, ...changes.map((x) => h('div', { class: 'listitem', onclick: () => navigate(`node/${x.id}`) },
        h('span', null, x.title),
        h('span', { class: 'small muted mono' }, `${label(x.before)} → ${label(x.after)} (${Math.round(x.before * 100)}% → ${Math.round(x.after * 100)}%)`),
      ))),
    ) : null,
    rec.learned ? h('div', { class: 'card card2' }, h('div', { class: 'small muted' }, 'You wrote'), h('p', { style: { margin: 0 } }, rec.learned), rec.confidence ? h('div', { class: 'small muted' }, `Confidence ${rec.confidence}/5`) : null) : null,
    h('button', { type: 'button', class: 'btn block', onclick: () => navigate('today') }, 'Done'),
  ]);
}
