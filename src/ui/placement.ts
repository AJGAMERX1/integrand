// Placement diagnostic (#/placement): one question per screen, 1 attempt, no hints, "I don't know" counts as wrong.
// At the end: scorePlacement -> saveSkillStates, placementDone = true, summary of what got unlocked.
import type { DiagnosticQuestion, Problem, SkillState } from '../types';
import type { Screen } from './screens';
import { h, append, clear, toast } from './dom';
import { navigate } from './router';
import { renderProblem, type ProblemCardHandle } from './problemCard';
import { curriculum, diagnostic, getNode } from '../data/load';
import { getSettings, saveSettings } from '../db/db';
import { loadReading, loadSessions, loadSkillStates, saveSkillStates } from '../db/state';
import { today } from '../lib/date';
import { buildAssignment, scorePlacement, unlockedNodes } from '../engine';

type Result = { question: DiagnosticQuestion; correct: boolean };

let card: ProblemCardHandle | null = null;

function toProblem(q: DiagnosticQuestion): Problem {
  return {
    id: q.id, skill: q.nodeId, difficulty: 2, statement: q.statement, checker: q.checker, answer: q.answer,
    choices: q.choices, variable: q.variable, domain: q.domain, hints: [], solution: [], verified: true,
  };
}

async function skipPlacement() {
  await saveSettings({ placementDone: true });
  toast('Starting from the beginning.');
  navigate('today');
}

function intro(c: HTMLElement, alreadyDone: boolean, count: number, onStart: () => void) {
  clear(c);
  c.append(
    h('h1', null, alreadyDone ? 'Retake placement' : 'Placement'),
    h('div', { class: 'card' },
      h('p', null, `${count} quick questions, about 5 minutes. One try each, no hints, and "I don't know" is a perfectly good answer.`),
      h('p', { class: 'muted' }, alreadyDone
        ? 'Retaking replaces the mastery of the skills the diagnostic covers. Your attempt history and streak are kept.'
        : 'This decides where your study plan starts so you are not stuck on things you already know.'),
      h('div', { class: 'stack' },
        h('button', { type: 'button', class: 'btn block', onclick: onStart }, alreadyDone ? 'Start the retake' : 'Start placement'),
        alreadyDone
          ? h('a', { class: 'btn ghost block', href: '#/settings' }, 'Back to settings')
          : h('button', { type: 'button', class: 'btn ghost block', onclick: () => void skipPlacement() }, 'Skip, start from the beginning'),
      ),
    ),
  );
}

export const placementScreen: Screen = {
  async render(c) {
    card?.destroy(); card = null;
    const settings = await getSettings();
    const questions = diagnostic.questions ?? [];

    if (questions.length === 0) {
      c.append(
        h('h1', null, 'Placement'),
        h('div', { class: 'card' },
          h('h3', null, 'No placement questions yet'),
          h('p', { class: 'muted' }, 'The diagnostic is still being written. You can start from the beginning and retake the placement later from Settings.'),
          h('button', { type: 'button', class: 'btn block', onclick: () => void skipPlacement() }, 'Start from the beginning'),
        ),
      );
      return;
    }

    const results: Result[] = [];
    let index = 0;

    const showQuestion = () => {
      card?.destroy(); card = null;
      clear(c);
      const q = questions[index];
      const node = getNode(q.nodeId);
      const pct = Math.round((index / questions.length) * 100);
      c.append(
        h('div', { class: 'row spread placement-head' },
          h('span', { class: 'small muted' }, `${index + 1} of ${questions.length}`),
          h('button', { type: 'button', class: 'btn ghost small', onclick: () => { if (confirm('Leave the placement? Progress is lost.')) navigate('today'); } }, 'Quit'),
        ),
        h('div', { class: 'progressbar', style: { marginBottom: '12px' } }, h('div', { style: { width: `${pct}%` } })),
      );
      const host = h('div'); c.appendChild(host);
      card = renderProblem(host, toProblem(q), {
        context: 'placement', maxAttempts: 1, allowReveal: false, allowHints: false, showSolution: false, explainLink: false,
        giveUpLabel: "I don't know", continueLabel: index + 1 < questions.length ? 'Next question' : 'See results',
        heading: node ? node.title : q.nodeId,
        onDone: (r) => { results.push({ question: q, correct: r.correct }); },
        onContinue: () => { index++; if (index < questions.length) showQuestion(); else void finish(); },
      });
      window.scrollTo(0, 0);
    };

    const finish = async () => {
      card?.destroy(); card = null;
      clear(c);
      c.append(h('h1', null, 'Placement results'));
      const correct = results.filter((r) => r.correct).length;
      let states: SkillState[] = [];
      let scoringFailed = false;
      try { states = scorePlacement(results, curriculum); }
      catch (err) { console.error('scorePlacement failed', err); scoringFailed = true; }
      try {
        if (states.length) await saveSkillStates(states);
        await saveSettings({ placementDone: true });
      } catch (err) { console.error(err); toast('Could not save placement results.'); }

      const summary = h('div', { class: 'card' },
        h('div', { class: 'bigstat' },
          h('div', null, h('div', { class: 'n' }, String(correct)), h('div', { class: 'l' }, 'correct')),
          h('div', null, h('div', { class: 'n' }, String(results.length - correct)), h('div', { class: 'l' }, 'missed')),
          h('div', null, h('div', { class: 'n' }, String(results.length)), h('div', { class: 'l' }, 'questions')),
        ),
      );
      if (scoringFailed) {
        summary.appendChild(h('p', { class: 'muted' }, 'Scoring is not available yet, so your plan starts from the beginning. You can retake the placement from Settings.'));
      } else {
        try {
          const stateMap = await loadSkillStates();
          const unlocked = unlockedNodes(stateMap, curriculum);
          const [reading, sessions] = await Promise.all([loadReading(), loadSessions()]);
          const a = buildAssignment({ today: today(), curriculum, states: stateMap, reading, sessions });
          const focus = getNode(a.focusNodeId);
          append(summary, [
            h('p', null, h('strong', null, `${unlocked.length} ${unlocked.length === 1 ? 'skill' : 'skills'} unlocked.`), ' Skills you answered correctly start partly mastered; the rest start fresh.'),
            focus ? h('p', null, 'Your first focus: ', h('strong', null, focus.title), focus.summary ? h('span', { class: 'muted' }, ` — ${focus.summary}`) : null) : null,
          ]);
        } catch (err) {
          console.error(err);
          summary.appendChild(h('p', { class: 'muted' }, 'Your skills are saved. Today will show your first assignment.'));
        }
      }
      summary.appendChild(h('button', { type: 'button', class: 'btn block', onclick: () => navigate('today') }, 'Go to Today'));
      c.appendChild(summary);
    };

    intro(c, settings.placementDone, questions.length, showQuestion);
  },
  unmount() { card?.destroy(); card = null; },
};
