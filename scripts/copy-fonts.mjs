// Copies MathLive's fonts into public/fonts/mathlive so the virtual keyboard and math field render in production.
import { cpSync, mkdirSync, existsSync } from 'node:fs';
const src = 'node_modules/mathlive/fonts';
const dst = 'public/fonts/mathlive';
if (!existsSync(src)) { console.error('mathlive fonts not found; run npm install'); process.exit(1); }
mkdirSync(dst, { recursive: true });
cpSync(src, dst, { recursive: true });
console.log('copied MathLive fonts to', dst);
