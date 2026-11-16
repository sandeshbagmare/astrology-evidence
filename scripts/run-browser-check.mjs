import assert from 'node:assert/strict';
import {readFile} from 'node:fs/promises';
import {resolve} from 'node:path';
import {pathToFileURL} from 'node:url';
import vm from 'node:vm';

// CI installs the exact Playwright release outside the application checkout.
assert.ok(process.env.PLAYWRIGHT_PACKAGE_DIR, 'Set PLAYWRIGHT_PACKAGE_DIR to the installed playwright directory');
const {chromium} = await import(pathToFileURL(resolve(process.env.PLAYWRIGHT_PACKAGE_DIR, 'index.mjs')).href);
const origin = new URL(process.env.APP_PUBLIC_ORIGIN || 'http://127.0.0.1:8000');
assert.ok(['127.0.0.1', 'localhost'].includes(origin.hostname), 'Browser check must use the local synthetic app');
const source = await readFile(new URL('../tests/browser/verify-app.js', import.meta.url), 'utf8');
const verify = vm.runInNewContext(source, {URL, Date}, {filename: 'verify-app.js'});
const browser = await chromium.launch({headless: true});
try {
  const page = await browser.newPage();
  await page.goto(origin.href);
  const result = await verify(page);
  assert.equal(result.status, 'PASS');
  console.log(JSON.stringify(result));
} finally {
  await browser.close();
}
