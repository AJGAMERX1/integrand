// The one place date logic lives. Everything "today" goes through America/Chicago, never UTC midnight.
import { CONFIG } from './config';

const TZ = CONFIG.timezone;

const fmt = new Intl.DateTimeFormat('en-CA', {
  timeZone: TZ, year: 'numeric', month: '2-digit', day: '2-digit',
});
const partsFmt = new Intl.DateTimeFormat('en-US', {
  timeZone: TZ, hour12: false, year: 'numeric', month: '2-digit', day: '2-digit', hour: '2-digit', minute: '2-digit', second: '2-digit',
});

/** YYYY-MM-DD for the given instant in America/Chicago. */
export function toLocalDate(d: Date = new Date()): string {
  return fmt.format(d); // en-CA yields YYYY-MM-DD
}

/** Today's date string in America/Chicago. */
export function today(): string {
  return toLocalDate(new Date());
}

/** Add n calendar days to a YYYY-MM-DD string (pure calendar arithmetic, timezone-free). */
export function addDays(date: string, n: number): string {
  const [y, m, d] = date.split('-').map(Number);
  const t = Date.UTC(y, m - 1, d) + n * 86_400_000;
  const r = new Date(t);
  return `${r.getUTCFullYear()}-${String(r.getUTCMonth() + 1).padStart(2, '0')}-${String(r.getUTCDate()).padStart(2, '0')}`;
}

/** Whole days from a to b (b - a). */
export function diffDays(a: string, b: string): number {
  const [y1, m1, d1] = a.split('-').map(Number);
  const [y2, m2, d2] = b.split('-').map(Number);
  return Math.round((Date.UTC(y2, m2 - 1, d2) - Date.UTC(y1, m1 - 1, d1)) / 86_400_000);
}

export function isValidDate(s: string): boolean {
  return /^\d{4}-\d{2}-\d{2}$/.test(s) && !Number.isNaN(Date.UTC(+s.slice(0, 4), +s.slice(5, 7) - 1, +s.slice(8, 10)));
}

/** Chicago wall-clock components of an instant. */
export function localParts(d: Date = new Date()): { y: number; m: number; d: number; h: number; min: number; s: number } {
  const p: Record<string, number> = {};
  for (const part of partsFmt.formatToParts(d)) if (part.type !== 'literal') p[part.type] = Number(part.value);
  return { y: p.year, m: p.month, d: p.day, h: p.hour % 24, min: p.minute, s: p.second };
}

/** Milliseconds until the next midnight in America/Chicago (handles DST because it measures wall-clock seconds remaining). */
export function msUntilMidnight(now: Date = new Date()): number {
  const { h, min, s } = localParts(now);
  const elapsed = h * 3600 + min * 60 + s;
  let remaining = 86_400 - elapsed;
  // DST transition days are 23 or 25 hours long; refine by probing the actual date change.
  const probe = new Date(now.getTime() + remaining * 1000);
  const todayStr = toLocalDate(now);
  if (toLocalDate(probe) === todayStr) {
    // still same day (25h day): step forward until date flips
    while (toLocalDate(new Date(now.getTime() + remaining * 1000)) === todayStr) remaining += 60;
  } else {
    // may have overshot on a 23h day: step back while previous second is already tomorrow
    while (remaining > 60 && toLocalDate(new Date(now.getTime() + (remaining - 60) * 1000)) !== todayStr) remaining -= 60;
  }
  return remaining * 1000 - now.getMilliseconds();
}

export function formatCountdown(ms: number): string {
  const total = Math.max(0, Math.floor(ms / 1000));
  const h = Math.floor(total / 3600), m = Math.floor((total % 3600) / 60), s = total % 60;
  return `${String(h).padStart(2, '0')}:${String(m).padStart(2, '0')}:${String(s).padStart(2, '0')}`;
}

/** Human label like "Mon, Oct 13". */
export function prettyDate(date: string): string {
  const [y, m, d] = date.split('-').map(Number);
  return new Date(Date.UTC(y, m - 1, d)).toLocaleDateString('en-US', { weekday: 'short', month: 'short', day: 'numeric', timeZone: 'UTC' });
}
