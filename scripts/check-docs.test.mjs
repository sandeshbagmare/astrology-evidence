import test from 'node:test';
import assert from 'node:assert/strict';
import { inspectText } from './check-docs.mjs';
test('rejects credential-shaped values without echoing them', () => {
  const secret = ['sk', 'x'.repeat(32)].join('-');
  const findings = inspectText(secret, 'note.md');
  assert.ok(findings.includes('credential-shaped text'));
  assert.ok(!JSON.stringify(findings).includes(secret));
});
test('does not flag ordinary risk-management URLs', () => {
  assert.deepEqual(inspectText('https://www.nist.gov/itl/ai-risk-management-framework', 'note.md'), []);
});
test('catches malformed markdown and damaged text', () => {
  assert.ok(inspectText('```text\nunfinished', 'note.md').includes('unbalanced code fences'));
  assert.ok(inspectText(String.fromCodePoint(0xfffd), 'note.md').includes('replacement character'));
});
