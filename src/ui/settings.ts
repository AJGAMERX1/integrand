// Settings: theme, streak rule, flow timer, placement, backup (export / import), danger zone, about.
import { h, clear, toast } from './dom';
import { navigate } from './router';
import type { Screen } from './screens';
import { exportAll, getSettings, importAll, saveSettings, validateBundle, wipeAll } from '../db/db';
import { today } from '../lib/date';
import type { ExportBundle, Settings } from '../types';

const APP_VERSION = 'Integrand v0.1';

function notifySettingsChanged() { window.dispatchEvent(new Event('settings-changed')); }

function segmented<T extends string>(options: { id: T; label: string }[], value: T, onChange: (v: T) => void): HTMLElement {
  const row = h('div', { class: 'segmented', role: 'radiogroup' });
  for (const o of options) {
    const b = h('button', { type: 'button', class: `seg ${value === o.id ? 'active' : ''}`.trim(), role: 'radio', 'aria-checked': String(value === o.id) }, o.label);
    b.addEventListener('click', () => {
      for (const x of row.querySelectorAll('button')) { x.classList.toggle('active', x === b); x.setAttribute('aria-checked', String(x === b)); }
      onChange(o.id);
    });
    row.appendChild(b);
  }
  return row;
}

function setting(label: string, control: Node, help?: string): HTMLElement {
  return h('div', { class: 'setting' }, h('div', { class: 'setting-label' }, label), control, help ? h('div', { class: 'small muted setting-help' }, help) : null);
}

/** ---------- Preferences ---------- */

function preferencesCard(s: Settings): HTMLElement {
  const theme = segmented<Settings['theme']>([{ id: 'system', label: 'System' }, { id: 'light', label: 'Light' }, { id: 'dark', label: 'Dark' }], s.theme, async (v) => {
    await saveSettings({ theme: v }); notifySettingsChanged();
  });

  const streak = segmented<Settings['streakRule']>([{ id: 'completion', label: 'Completion' }, { id: 'solved', label: 'Solved only' }], s.streakRule, async (v) => {
    await saveSettings({ streakRule: v }); notifySettingsChanged(); toast(v === 'solved' ? 'Streak now counts solved days only' : 'Streak now counts completed days');
  });

  const ratio = h('input', { type: 'number', min: 4, max: 7, step: 1, value: String(s.flowBreakRatio), inputmode: 'numeric' }) as HTMLInputElement;
  const ratioHelp = h('div', { class: 'small muted setting-help' });
  const describeRatio = (r: number) => { ratioHelp.textContent = `Break = focus time ÷ ${r}. A 25-minute focus earns a ${Math.round(25 / r)}-minute break.`; };
  describeRatio(s.flowBreakRatio);
  ratio.addEventListener('change', async () => {
    let v = Math.round(Number(ratio.value));
    if (!Number.isFinite(v)) v = 5;
    v = Math.max(4, Math.min(7, v));
    ratio.value = String(v);
    await saveSettings({ flowBreakRatio: v }); notifySettingsChanged(); describeRatio(v);
  });

  return h('div', { class: 'card' },
    h('h3', null, 'Preferences'),
    setting('Theme', theme),
    setting('Daily Integral streak rule', streak, 'Completion: a day counts once the attempt ends, whether you solved it or saw the solution. Solved only: a day counts only when you got the integral right. A separate "solved" total is always shown.'),
    h('div', { class: 'setting' }, h('div', { class: 'setting-label' }, 'Flowmodoro break ratio (4-7)'), ratio, ratioHelp),
    setting('Daily budget', h('div', { class: 'setting-static' }, `${s.dailyBudgetMinutes} minutes`), 'The session is built around a 30-minute day: review, reading, problems, Daily Integral, exit.'),
  );
}

/** ---------- Placement ---------- */

function placementCard(s: Settings): HTMLElement {
  return h('div', { class: 'card' },
    h('h3', null, 'Placement'),
    h('p', { class: 'small muted' }, s.placementDone
      ? 'The placement diagnostic sets your starting mastery across the curriculum. Retaking it overwrites those starting values for the skills it covers.'
      : 'You have not taken the placement diagnostic yet. It takes about 15 minutes and places you in the curriculum.'),
    h('button', { type: 'button', class: 'btn ghost block', onclick: () => navigate('placement') }, s.placementDone ? 'Retake placement' : 'Take placement'),
  );
}

/** ---------- Backup ---------- */

function countSummary(b: ExportBundle): HTMLElement {
  const rows: [string, number | string][] = [
    ['Skills with progress', b.skillState.length],
    ['Problem attempts', b.attempts.length],
    ['Sessions', b.sessions.length],
    ['Reading records', b.reading.length],
    ['Daily Integral days', b.daily.length],
    ['Study log entries', b.studyLog.length],
    ['Settings', b.settings ? 'included' : 'not included'],
    ['Exported', b.exportedAt ? new Date(b.exportedAt).toLocaleString() : 'unknown'],
  ];
  return h('table', { class: 'summary-table' }, ...rows.map(([k, v]) => h('tr', null, h('td', { class: 'muted' }, k), h('td', null, String(v)))));
}

async function doExport() {
  const bundle = await exportAll();
  const blob = new Blob([JSON.stringify(bundle, null, 2)], { type: 'application/json' });
  const url = URL.createObjectURL(blob);
  const a = h('a', { href: url, download: `integrand-backup-${today()}.json` });
  document.body.appendChild(a);
  a.click();
  a.remove();
  setTimeout(() => URL.revokeObjectURL(url), 2000);
  toast('Backup exported');
}

function backupCard(): HTMLElement {
  const importHost = h('div', { class: 'import-host' });
  const fileInput = h('input', { type: 'file', accept: 'application/json,.json', class: 'hidden' }) as HTMLInputElement;

  fileInput.addEventListener('change', async () => {
    const file = fileInput.files?.[0];
    fileInput.value = '';
    if (!file) return;
    clear(importHost);
    let bundle: ExportBundle;
    try {
      bundle = validateBundle(JSON.parse(await file.text()));
    } catch (err) {
      importHost.appendChild(h('div', { class: 'card2 import-box' }, h('strong', null, 'Could not read that file'), h('div', { class: 'small muted' }, String((err as Error).message ?? err))));
      return;
    }
    const confirmBtn = h('button', { type: 'button', class: 'btn bad block' }, 'Replace my data with this backup');
    const cancelBtn = h('button', { type: 'button', class: 'btn ghost block', onclick: () => clear(importHost) }, 'Cancel');
    confirmBtn.addEventListener('click', async () => {
      confirmBtn.disabled = true; cancelBtn.disabled = true; confirmBtn.textContent = 'Importing…';
      try {
        await importAll(bundle);
        toast('Backup imported. Reloading…');
        setTimeout(() => location.reload(), 600);
      } catch (err) {
        confirmBtn.disabled = false; cancelBtn.disabled = false; confirmBtn.textContent = 'Replace my data with this backup';
        toast(`Import failed: ${String((err as Error).message ?? err)}`);
      }
    });
    importHost.appendChild(h('div', { class: 'card2 import-box' },
      h('strong', null, `Backup from ${file.name}`),
      countSummary(bundle),
      h('p', { class: 'small' }, 'Importing replaces everything currently stored in this browser: progress, attempts, sessions, streak, and settings. This cannot be undone.'),
      h('div', { class: 'stack' }, confirmBtn, cancelBtn),
    ));
  });

  return h('div', { class: 'card' },
    h('h3', null, 'Backup'),
    h('p', { class: 'small warn-box' }, 'Your progress lives only in this browser. Browsers can wipe site data at any time, and iOS Safari may clear it after about 7 days without use. Export a backup regularly and keep the file somewhere safe (Files, Drive, email to yourself).'),
    h('div', { class: 'stack' },
      h('button', { type: 'button', class: 'btn block', onclick: () => doExport().catch((e) => toast(`Export failed: ${String((e as Error).message ?? e)}`)) }, 'Export backup (.json)'),
      h('button', { type: 'button', class: 'btn ghost block', onclick: () => fileInput.click() }, 'Import backup…'),
      fileInput,
    ),
    importHost,
  );
}

/** ---------- Danger zone ---------- */

function dangerCard(): HTMLElement {
  const host = h('div', { class: 'danger-host' });
  const start = h('button', { type: 'button', class: 'btn ghost block danger-btn' }, 'Wipe all data…');
  start.addEventListener('click', () => {
    clear(host);
    const input = h('input', { type: 'text', placeholder: 'type RESET', autocapitalize: 'characters', autocomplete: 'off', spellcheck: 'false' }) as HTMLInputElement;
    const go = h('button', { type: 'button', class: 'btn bad block', disabled: true }, 'Erase everything') as HTMLButtonElement;
    input.addEventListener('input', () => { go.disabled = input.value.trim() !== 'RESET'; });
    go.addEventListener('click', async () => {
      if (input.value.trim() !== 'RESET') return;
      go.disabled = true; go.textContent = 'Erasing…';
      try { await wipeAll(); toast('All data erased'); setTimeout(() => location.reload(), 600); }
      catch (err) { go.disabled = false; go.textContent = 'Erase everything'; toast(`Could not erase: ${String((err as Error).message ?? err)}`); }
    });
    host.appendChild(h('div', { class: 'card2 import-box' },
      h('strong', null, 'This erases all progress on this device'),
      h('p', { class: 'small' }, 'Mastery, attempts, sessions, the Daily Integral streak, study time, and settings will all be deleted. Export a backup first if you might want any of it back. Type RESET to confirm.'),
      input,
      h('div', { class: 'stack' }, go, h('button', { type: 'button', class: 'btn ghost block', onclick: () => { clear(host); host.appendChild(start); } }, 'Cancel')),
    ));
  });
  host.appendChild(start);
  return h('div', { class: 'card danger-card' }, h('h3', null, 'Danger zone'), host);
}

/** ---------- About ---------- */

function aboutCard(): HTMLElement {
  return h('div', { class: 'card' },
    h('h3', null, 'About'),
    h('p', null, h('strong', null, APP_VERSION)),
    h('p', { class: 'small' }, 'Integrand is a phone-first daily calculus coach. Each day it builds one 30-minute assignment: a short review of skills that are due, a few pages to read from the book, new problems tied to that reading, and one Daily Integral. It tracks mastery per skill, schedules spaced reviews, and unlocks the next topic when the prerequisites are solid, so you never have to decide what to study.'),
    h('p', { class: 'small muted' }, 'Book page numbers refer to Stewart, Calculus: Early Transcendentals, 8th edition, and are the printed page numbers in the physical book. Appendix pages are printed as A2, A10, and so on.'),
    h('p', { class: 'small muted' }, 'All problems and explanations are original. The app stores nothing but section titles and page numbers from the book.'),
    h('details', { class: 'guide' },
      h('summary', null, 'Install on your phone'),
      h('ul', { class: 'small install-tips' },
        h('li', null, h('strong', null, 'iPhone (Safari): '), 'tap the Share button, then "Add to Home Screen". Open it from the home screen so it runs full-screen and works offline.'),
        h('li', null, h('strong', null, 'Android (Chrome): '), 'tap the menu (three dots), then "Install app" or "Add to Home screen".'),
        h('li', null, 'Installed or not, your data stays in this browser only. Export a backup from the Backup section now and then.'),
      ),
    ),
  );
}

/** ---------- Screen ---------- */

export const settingsScreen: Screen = {
  async render(container) {
    const s = await getSettings();
    container.append(
      h('h1', null, 'Settings'),
      preferencesCard(s),
      placementCard(s),
      backupCard(),
      dangerCard(),
      aboutCard(),
    );
  },
};
