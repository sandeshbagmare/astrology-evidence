import fs from 'node:fs';
import vm from 'node:vm';
import test from 'node:test';
import assert from 'node:assert/strict';

const verifyApp = vm.runInNewContext(fs.readFileSync(new URL('./browser/verify-app.js', import.meta.url), 'utf8'), {URL, Date});

test('browser verification preserves the primary failure when cleanup also fails', async () => {
  const primary = new Error('Application unavailable');
  let closed = 0;
  let pages = 0;
  const context = {
    async newPage() {
      const number = pages++;
      return {on() {}, async goto() {throw number === 0 ? primary : new Error('Cleanup unavailable');}};
    },
    async close() {closed += 1;},
  };
  const page = {url: () => 'http://127.0.0.1:18766/', context: () => ({browser: () => ({newContext: async () => context})})};
  await assert.rejects(() => verifyApp(page), error => error === primary);
  assert.equal(closed, 1);
});
