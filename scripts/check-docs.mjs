import { readdirSync, readFileSync, existsSync } from 'node:fs';
import { resolve, dirname, relative, extname } from 'node:path';
import { fileURLToPath } from 'node:url';
const root = resolve(dirname(fileURLToPath(import.meta.url)), '..');
export function inspectText(text, name) {
  const issues = [];
  if (/(?<![A-Za-z0-9])sk-[A-Za-z0-9_-]{20,}|Bearer\s+[A-Za-z0-9_-]{20,}/.test(text)) issues.push('credential-shaped text');
  if (text.includes('\uFFFD')) issues.push('replacement character');
  if (name.endsWith('.md') && (text.match(/^```/gm) || []).length % 2) issues.push('unbalanced code fences');
  return issues;
}
function filesAt(dir) {
  return readdirSync(dir, { withFileTypes: true }).flatMap(entry => {
    if (['.git', 'node_modules', '.playwright-cli', '.venv', '.venv314', '.runtime312', '.runtime314', '__pycache__', '.pytest_cache', '.mypy_cache', '.ruff_cache'].includes(entry.name)) return [];
    const path = resolve(dir, entry.name);
    return entry.isDirectory() ? filesAt(path) : [path];
  });
}
export function checkProject() {
  const errors = [];
  const files = filesAt(root).filter(p => ['.md', '.html', '.css', '.mjs', '.yml'].includes(extname(p)));
  for (const file of files) {
    const text = readFileSync(file, 'utf8');
    const name = relative(root, file);
    for (const issue of inspectText(text, name)) errors.push(`${name}: ${issue}`);
    if (!['.md', '.html'].includes(extname(file)) || (extname(file) === '.html' && name.startsWith('src'))) continue;
    const targets = extname(file) === '.md'
      ? [...text.matchAll(/\]\(([^)]+)\)/g)].map(m => m[1])
      : [...text.matchAll(/(?:href|src)="([^"]+)"/g)].map(m => m[1]);
    for (const target of targets) {
      if (/^(https?:|mailto:)/.test(target)) continue;
      const [path, anchor] = target.split('#');
      const destination = path ? resolve(dirname(file), decodeURIComponent(path)) : file;
      if (!existsSync(destination)) errors.push(`${name}: missing local target ${target}`);
      else if (anchor && extname(destination) === '.html' && !readFileSync(destination, 'utf8').includes(`id="${anchor}"`)) errors.push(`${name}: missing HTML anchor ${target}`);
    }
  }
  for (const required of ['README.md', 'AGENTS.md', 'REPORT.md', 'docs/index.html', 'docs/style.css', 'context/44-small-commits-and-continuous-verification.md']) {
    if (!existsSync(resolve(root, required))) errors.push(`missing ${required}`);
  }
  return { files: files.length, errors };
}
if (process.argv[1] && resolve(process.argv[1]) === fileURLToPath(import.meta.url)) {
  const result = checkProject();
  for (const error of result.errors) console.error(error);
  console.log(`${result.errors.length ? 'FAIL' : 'PASS'}: ${result.files} files checked, ${result.errors.length} issues`);
  process.exitCode = result.errors.length ? 1 : 0;
}
