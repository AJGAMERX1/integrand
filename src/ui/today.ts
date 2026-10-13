// Today (#/today): the one assignment for today, a Start/Continue session button, Daily Integral only,
// this week's plan, the Flowmodoro timer and the minutes logged today. The learner never has to decide what to study.
import type { DailyRecord, SessionRecord, Settings, SkillState, StudyLog } from '../types';
import type { Screen } from './screens';
import { h, clear, toast } from './dom';
import { navigate } from './router';
import { flowTimer, type FlowTimerHandle } from './timer';
import { tierLabel } from './daily';
import { curriculum, getNode, problemsFor } from '../data/load';
import { getSettings, saveSettings } from '../db/db';
import { loadDaily, loadReading, loadSessions, loadSkillStates, loadStudyLog, logStudy } from '../db/state';
import { prettyDate, today } from '../lib/date';
import { buildAssignment, buildWeekPlan, currentIntegralTier, dueReviews, type Assignment } from '../engine';
import { computeStreak } from '../daily';
import { BLOCK_TITLES, blocksFor, currentBlock, describeReading, isComplete, progress, totalMinutes } from '../session/machine';

let flow: FlowTimerHandle | null = null;

function welcome(c: HTMLElement) {
  c.append(
    h('h1', null, 'Welcome to Integrand'),
    h('div', { class: 'card' },
      h('p', null, 'Integrand runs one 30-minute calculus session a day: a quick review, a few pages of Stewart, three or four problems, and a Daily Integral.'),
      h('p', null, 'It tracks what you have mastered and decides what to study next, so you never have to.'),
      h('p', null, 'A short placement tells it where to start; skip it to begin at the very beginning.'),
      h('div', { class: 'stack' },
        h('button', { type: 'button', class: 'btn block', onclick: () => navigate('placement') }, 'Take the 5-minute placement'),
        h('button', {
          type: 'button', class: 'btn ghost block',
          onclick: async () => { await saveSettings({ placementDone: true }); toast('Starting from the beginning.'); clear(c); await todayScreen.render(c, []); },
        }, 'Skip, start from the beginning'),
      ),
    ),
  );
}

function minutesToday(log: StudyLog[], date: string): number {
  return log.filter((l) => l.date === date).reduce((s, l) => s + (l.minutes || 0), 0);
}

export const todayScreen: Screen = {
  async render(c) {
    flow?.destroy(); flow = null;
    const date = today();
    const settings: Settings = await getSettings();
    if (!settings.placementDone) { welcome(c); return; }

    const [states, reading, sessions, dailyRecords, studyLog] = await Promise.all([
      loadSkillStates(), loadReading(), loadSessions(), loadDaily(), loadStudyLog(),
    ]);
    const ctx = { today: date, curriculum, states, reading, sessions };

    let assignment: Assignment | null = null;
    let engineError: string | null = null;
    try { assignment = buildAssignment(ctx); } catch (err) { console.error(err); engineError = String((err as Error)?.message ?? err); }

    const rec: SessionRecord | undefined = sessions.find((s) => s.date === date);
    const todayDaily: DailyRecord | undefined = dailyRecords.find((r) => r.date === date && !r.isArchive);

    c.appendChild(h('div', { class: 'row spread today-head' },
      h('h1', { style: { margin: 0 } }, prettyDate(date)),
      h('span', { class: 'small muted' }, `${minutesToday(studyLog, date)} min logged`),
    ));

    if (!assignment) {
      c.appendChild(h('div', { class: 'card' },
        h('h2', null, 'No assignment yet'),
        h('p', { class: 'muted' }, engineError && /not implemented/i.test(engineError)
          ? 'The study engine is not wired up yet. You can still do the Daily Integral or browse the Map.'
          : 'Could not build today’s assignment.'),
        engineError ? h('p', { class: 'small muted mono' }, engineError) : null,
        h('div', { class: 'stack' },
          h('button', { type: 'button', class: 'btn int block', onclick: () => navigate('daily') }, 'Daily Integral'),
          h('button', { type: 'button', class: 'btn ghost block', onclick: () => navigate('map') }, 'Open the map'),
        ),
      ));
    } else {
      c.appendChild(assignmentCard(assignment, states, rec, todayDaily));
      c.appendChild(weekCard(ctx));
    }

    // Daily Integral status + streak
    c.appendChild(dailyCard(dailyRecords, todayDaily, settings, states, date));

    // Flowmodoro timer: free study is logged as 'flow' against the focus node.
    const focusId = assignment?.focusNodeId ?? null;
    const focusTitle = focusId ? getNode(focusId)?.title : undefined;
    const loggedLine = h('div', { class: 'small muted logged-line' }, `Logged today: ${minutesToday(studyLog, date)} min`);
    const timerHost = h('div');
    c.appendChild(timerHost);
    flow = flowTimer(timerHost, {
      breakRatio: settings.flowBreakRatio,
      title: 'Free study timer',
      note: focusTitle ? `Logs to: ${focusTitle}` : 'Logs study time',
      onFocusEnd: async (minutes) => {
        if (minutes < 1) { toast('Under a minute; not logged.'); return; }
        try {
          await logStudy({ minutes, kind: 'flow', nodeId: focusId, note: '' });
          const log = await loadStudyLog();
          loggedLine.textContent = `Logged today: ${minutesToday(log, date)} min`;
          toast(`Logged ${minutes} min`);
        } catch (err) { console.error(err); toast('Could not log that time.'); }
      },
    });
    timerHost.querySelector('.flow')?.appendChild(loggedLine);
  },
  unmount() { flow?.destroy(); flow = null; },
};

function assignmentCard(a: Assignment, states: Map<string, SkillState>, rec: SessionRecord | undefined, todayDaily: DailyRecord | undefined): HTMLElement {
  const focus = getNode(a.focusNodeId);
  const readingInfo = describeReading(a);
  let due = 0;
  try { due = dueReviews(states, a.date).length; } catch { due = a.reviewNodeIds.length; }
  let tier = 0;
  try { tier = currentIntegralTier(states, curriculum); } catch { /* stub */ }
  const problemCount = Math.min(4, a.problemNodeIds.reduce((s, id) => s + problemsFor(id).length, 0));
  const focusHasProblems = problemsFor(a.focusNodeId).length > 0;

  // Session progress
  const fullRec = rec && rec.mode === 'full' ? rec : undefined;
  const prog = fullRec ? progress(fullRec) : { done: 0, total: blocksFor('full').length, blocks: blocksFor('full').map((block) => ({ block, done: false })) };
  const dailyDoneViaRecord = !!todayDaily && todayDaily.outcome !== 'incomplete';
  const strip = h('div', { class: 'blocks-progress' }, ...prog.blocks.map((b) => {
    const done = b.done || (b.block === 'daily' && dailyDoneViaRecord);
    return h('div', { class: `block-pill${done ? ' done' : ''}` }, h('span', { class: 'tick' }, done ? '✓' : ''), BLOCK_TITLES[b.block]);
  }));

  let mainLabel = 'Start session';
  let mainClass = 'btn block';
  if (fullRec && isComplete(fullRec)) { mainLabel = 'Session done — see summary'; mainClass = 'btn ghost block'; }
  else if (fullRec && fullRec.blocksCompleted.length > 0) { mainLabel = `Continue session (${BLOCK_TITLES[currentBlock(fullRec) ?? 'review']})`; }

  const card = h('div', { class: 'card today-assignment' },
    h('div', { class: 'small muted' }, 'Today'),
    h('h2', { class: 'today-title' }, focus ? focus.title : a.focusNodeId),
    focus?.group ? h('div', { class: 'small muted' }, focus.group) : null,
    h('p', { class: 'reading-line' },
      h('strong', null, readingInfo.sentence),
      readingInfo.nodeId && readingInfo.nodeId !== a.focusNodeId ? h('span', { class: 'muted' }, ` (${readingInfo.title})`) : null,
    ),
    h('div', { class: 'row chips' },
      h('span', { class: `chip${due > 0 ? ' warn' : ''}` }, `Review: ${due} due`),
      h('span', { class: 'chip accent' }, `Problems: ${problemCount}`),
      h('span', { class: 'chip int' }, `Integral I${tier}`),
      h('span', { class: 'chip' }, `~${a.estimatedMinutes || totalMinutes('full')} min`),
    ),
    !focusHasProblems ? h('p', { class: 'small muted' }, 'No problems for this skill yet; the session will use reading and review.') : null,
    a.rationale.length ? h('ul', { class: 'rationale small muted' }, ...a.rationale.map((r) => h('li', null, r))) : null,
    strip,
    h('div', { class: 'stack' },
      h('button', { type: 'button', class: mainClass, onclick: () => navigate('session') }, mainLabel),
      h('button', { type: 'button', class: 'btn int block', onclick: () => navigate('daily') }, dailyDoneViaRecord ? 'Daily Integral (done today)' : 'Daily Integral only'),
    ),
  );
  if (focus) card.appendChild(h('p', { class: 'small', style: { marginTop: '10px' } }, h('a', { href: `#/node/${encodeURIComponent(focus.id)}` }, 'Read the concept page')));
  return card;
}

function weekCard(ctx: Parameters<typeof buildWeekPlan>[0]): HTMLElement {
  const card = h('div', { class: 'card week' }, h('h3', null, 'This week'));
  let plan: Assignment[] = [];
  try { plan = buildWeekPlan(ctx, 7); } catch (err) { console.error(err); }
  if (!plan.length) { card.appendChild(h('p', { class: 'muted small' }, 'The weekly projection is not available yet.')); return card; }
  const rows = plan.slice(0, 7).map((a, i) => {
    const node = getNode(a.focusNodeId);
    const r = describeReading(a);
    return h('div', { class: `week-row${i === 0 ? ' today' : ''}` },
      h('span', { class: 'week-day' }, i === 0 ? 'Today' : prettyDate(a.date).split(',')[0]),
      h('span', { class: 'week-focus' }, node?.title ?? a.focusNodeId),
      h('span', { class: 'week-pages small muted' }, r.pages ?? (r.nodeId ? 'concept' : '')),
    );
  });
  card.append(...rows, h('p', { class: 'small muted', style: { margin: '8px 0 0' } }, 'Projection, assuming each day gets done. It adapts to what you miss.'));
  return card;
}

function dailyCard(records: DailyRecord[], todayDaily: DailyRecord | undefined, settings: Settings, states: Map<string, SkillState>, date: string): HTMLElement {
  let streak = { current: 0, best: 0, solved: 0, completed: 0 };
  try { streak = computeStreak(records, date, settings.streakRule); } catch { /* stub */ }
  let tier = 0;
  try { tier = currentIntegralTier(states, curriculum); } catch { /* stub */ }
  const done = !!todayDaily && todayDaily.outcome !== 'incomplete';
  const status = done
    ? (todayDaily?.outcome === 'solved' ? 'Solved today' : 'Done today (revealed)')
    : todayDaily ? 'In progress' : 'Not done yet';
  return h('div', { class: 'card daily-mini', onclick: () => navigate('daily') },
    h('div', { class: 'row spread' },
      h('div', null, h('h3', { style: { margin: 0 } }, 'Daily Integral'), h('div', { class: 'small muted' }, `Tier I${tier}: ${tierLabel(tier)}`)),
      h('span', { class: `chip ${done ? 'good' : 'int'}` }, status),
    ),
    h('div', { class: 'row small muted', style: { marginTop: '8px' } },
      h('span', null, h('strong', null, String(streak.current)), ' day streak'),
      h('span', null, 'best ', h('strong', null, String(streak.best))),
      h('span', null, h('strong', null, String(streak.solved)), ' solved'),
    ),
  );
}

