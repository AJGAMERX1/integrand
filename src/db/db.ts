// Thin IndexedDB layer. Stores mirror SPEC.md section 8. No library; keep it boring.
import { CONFIG } from '../lib/config';
import type {
  AttemptRecord, DailyRecord, ExportBundle, ReadingRecord, SessionRecord, Settings, SkillState, StudyLog,
} from '../types';

export type StoreName = 'settings' | 'skillState' | 'attempts' | 'sessions' | 'reading' | 'daily' | 'studyLog';

const KEY_PATHS: Record<StoreName, string> = {
  settings: 'id', skillState: 'nodeId', attempts: 'id', sessions: 'date', reading: 'nodeId', daily: 'date', studyLog: 'id',
};

let dbPromise: Promise<IDBDatabase> | null = null;

export function openDB(): Promise<IDBDatabase> {
  if (dbPromise) return dbPromise;
  dbPromise = new Promise((resolve, reject) => {
    const req = indexedDB.open(CONFIG.db.name, CONFIG.db.version);
    req.onupgradeneeded = () => {
      const db = req.result;
      for (const name of Object.keys(KEY_PATHS) as StoreName[]) {
        if (!db.objectStoreNames.contains(name)) {
          const store = db.createObjectStore(name, { keyPath: KEY_PATHS[name] });
          if (name === 'attempts' || name === 'studyLog') store.createIndex('date', 'date');
          if (name === 'attempts') store.createIndex('nodeId', 'nodeId');
        }
      }
    };
    req.onsuccess = () => resolve(req.result);
    req.onerror = () => reject(req.error);
  });
  return dbPromise;
}

function tx<T>(store: StoreName, mode: IDBTransactionMode, fn: (s: IDBObjectStore) => IDBRequest<T> | void): Promise<T> {
  return openDB().then((db) => new Promise<T>((resolve, reject) => {
    const t = db.transaction(store, mode);
    const s = t.objectStore(store);
    const r = fn(s);
    let result: T;
    if (r) r.onsuccess = () => { result = r.result; };
    t.oncomplete = () => resolve(result);
    t.onerror = () => reject(t.error);
    t.onabort = () => reject(t.error);
  }));
}

export const db = {
  get<T>(store: StoreName, key: IDBValidKey): Promise<T | undefined> {
    return tx<T | undefined>(store, 'readonly', (s) => s.get(key));
  },
  getAll<T>(store: StoreName): Promise<T[]> {
    return tx<T[]>(store, 'readonly', (s) => s.getAll());
  },
  getAllByIndex<T>(store: StoreName, index: string, value: IDBValidKey): Promise<T[]> {
    return tx<T[]>(store, 'readonly', (s) => s.index(index).getAll(value));
  },
  put<T>(store: StoreName, value: T): Promise<void> {
    return tx<void>(store, 'readwrite', (s) => { s.put(value); });
  },
  putMany<T>(store: StoreName, values: T[]): Promise<void> {
    return tx<void>(store, 'readwrite', (s) => { for (const v of values) s.put(v); });
  },
  delete(store: StoreName, key: IDBValidKey): Promise<void> {
    return tx<void>(store, 'readwrite', (s) => { s.delete(key); });
  },
  clear(store: StoreName): Promise<void> {
    return tx<void>(store, 'readwrite', (s) => { s.clear(); });
  },
};

export function defaultSettings(): Settings {
  return {
    id: 'settings', theme: 'system', placementDone: false, streakRule: CONFIG.daily.streakRule,
    flowBreakRatio: CONFIG.flow.breakRatio, dailyBudgetMinutes: 30, createdAt: Date.now(), schemaVersion: CONFIG.db.version,
  };
}

export async function getSettings(): Promise<Settings> {
  const s = await db.get<Settings>('settings', 'settings');
  if (s) return { ...defaultSettings(), ...s };
  const d = defaultSettings();
  await db.put('settings', d);
  return d;
}

export async function saveSettings(patch: Partial<Settings>): Promise<Settings> {
  const cur = await getSettings();
  const next = { ...cur, ...patch, id: 'settings' as const };
  await db.put('settings', next);
  return next;
}

/** ---------- Export / import (versioned) ---------- */

export async function exportAll(): Promise<ExportBundle> {
  const [settings, skillState, attempts, sessions, reading, daily, studyLog] = await Promise.all([
    db.get<Settings>('settings', 'settings'),
    db.getAll<SkillState>('skillState'), db.getAll<AttemptRecord>('attempts'), db.getAll<SessionRecord>('sessions'),
    db.getAll<ReadingRecord>('reading'), db.getAll<DailyRecord>('daily'), db.getAll<StudyLog>('studyLog'),
  ]);
  return {
    app: 'integrand', exportVersion: CONFIG.export.version, exportedAt: new Date().toISOString(),
    settings: settings ?? null, skillState, attempts, sessions, reading, daily, studyLog,
  };
}

export function validateBundle(raw: unknown): ExportBundle {
  if (!raw || typeof raw !== 'object') throw new Error('Not a JSON object');
  const b = raw as Partial<ExportBundle>;
  if (b.app !== 'integrand') throw new Error('Not an Integrand backup');
  if (typeof b.exportVersion !== 'number') throw new Error('Missing export version');
  if (b.exportVersion > CONFIG.export.version) throw new Error(`Backup version ${b.exportVersion} is newer than this app supports`);
  const arr = (k: keyof ExportBundle) => (Array.isArray(b[k]) ? (b[k] as unknown[]) : []);
  // Migrations for older export versions go here, keyed on b.exportVersion.
  return {
    app: 'integrand', exportVersion: CONFIG.export.version, exportedAt: String(b.exportedAt ?? new Date().toISOString()),
    settings: b.settings && typeof b.settings === 'object' ? { ...defaultSettings(), ...(b.settings as Settings), id: 'settings' } : null,
    skillState: arr('skillState') as SkillState[], attempts: arr('attempts') as AttemptRecord[], sessions: arr('sessions') as SessionRecord[],
    reading: arr('reading') as ReadingRecord[], daily: arr('daily') as DailyRecord[], studyLog: arr('studyLog') as StudyLog[],
  };
}

/** Replaces all local data with the bundle. Caller must confirm with the user first. */
export async function importAll(bundle: ExportBundle): Promise<void> {
  const stores: StoreName[] = ['settings', 'skillState', 'attempts', 'sessions', 'reading', 'daily', 'studyLog'];
  for (const s of stores) await db.clear(s);
  if (bundle.settings) await db.put('settings', bundle.settings);
  await db.putMany('skillState', bundle.skillState);
  await db.putMany('attempts', bundle.attempts);
  await db.putMany('sessions', bundle.sessions);
  await db.putMany('reading', bundle.reading);
  await db.putMany('daily', bundle.daily);
  await db.putMany('studyLog', bundle.studyLog);
}

export async function wipeAll(): Promise<void> {
  const stores: StoreName[] = ['settings', 'skillState', 'attempts', 'sessions', 'reading', 'daily', 'studyLog'];
  for (const s of stores) await db.clear(s);
}
