// Run with playwright-cli run-code --filename tests/browser/record-demos.js
// Start the local app and privacy worker first; only invented data is used.
async page => {
  const appOrigin = new URL(page.url()).origin;
  if (!['127.0.0.1', 'localhost'].includes(new URL(appOrigin).hostname)) {
    throw new Error('Open the local synthetic application before running this script');
  }
  const browser = page.context().browser();
  const chapters = [];
  const results = [];
  async function requireThat(condition, message) {
    if (!condition) throw new Error(message);
  }
  async function record(kind, viewport, javaScriptEnabled) {
    const context = await browser.newContext({
      viewport,
      javaScriptEnabled,
      recordVideo: {dir: '.playwright-cli/demo-recordings', size: viewport},
    });
    const actor = await context.newPage();
    const started = Date.now();
    const errors = [];
    actor.on('pageerror', error => errors.push(error.message));
    const alias = kind === 'desktop' ? 'Invented desktop example' : 'Invented mobile example';
    async function pause(label, milliseconds = 1100) {
      chapters.push({demo: kind, seconds: Math.round((Date.now() - started) / 100) / 10, label});
      await actor.waitForTimeout(milliseconds);
    }
    async function fits() {
      const size = await actor.evaluate(() => ({width: innerWidth, content: document.documentElement.scrollWidth}));
      await requireThat(size.content <= size.width, 'Horizontal page overflow: ' + actor.url());
    }
    let deleted = false;
    try {
      const response = await actor.goto(appOrigin + '/');
      await requireThat(response.status() === 200, 'Direct entry failed');
      await requireThat(await actor.locator('a[href="/login"], input[value="logout"]').count() === 0, 'Authentication controls present');
      await fits();
      await pause('Open a separate browser workspace without sign-in', 1700);
      await actor.screenshot({path: 'docs/assets/demos/' + kind + '-poster.png'});
      await actor.getByRole('link', {name: 'Create your first chart', exact: true}).click();
      await actor.getByLabel('Alias', {exact: true}).fill(alias);
      await actor.getByLabel('Birth date', {exact: true}).fill(javaScriptEnabled ? '2024-11-03' : '2000-01-01');
      if (javaScriptEnabled) {
        await actor.getByLabel('Local time', {exact: true}).fill('01:30');
      } else {
        await actor.getByLabel('Time certainty').selectOption('unknown');
      }
      await actor.getByLabel('Latitude', {exact: true}).fill(javaScriptEnabled ? '40.7' : '28.6');
      await actor.getByLabel('Longitude', {exact: true}).fill(javaScriptEnabled ? '-74.0' : '77.2');
      await actor.getByLabel('Time zone', {exact: true}).fill(javaScriptEnabled ? 'America/New_York' : 'Asia/Kolkata');
      await actor.getByLabel('Historical timezone confidence').selectOption('confirmed');
      if (javaScriptEnabled) {
        await actor.getByLabel('Time zone', {exact: true}).press('Tab');
        await actor.getByRole('option', {name: 'Second occurrence (UTC-05:00)', exact: true}).waitFor({state: 'attached'});
        await actor.getByLabel('Occurrence when the local time repeats').selectOption('1');
        await pause('Resolve a repeated local time with its explicit UTC offset', 1500);
      } else {
        await pause('Unknown time stays unknown; this mobile flow has JavaScript disabled', 1500);
      }
      await actor.locator('input[name="storage_consent"]').check();
      await actor.getByRole('button', {name: 'Save profile', exact: true}).click();
      await actor.waitForURL('**/dashboard');
      await actor.getByRole('link', {name: 'Birth profiles', exact: true}).click();
      await pause('The saved profile belongs to this browser workspace');
      await fits();
      await actor.getByRole('button', {name: 'Calculate chart', exact: true}).click();
      await actor.waitForURL('**/charts/*');
      const chartId = actor.url().split('/').pop();
      await actor.getByRole('heading', {name: 'Chart snapshot', exact: true}).waitFor();
      await fits();
      if (!javaScriptEnabled) {
        await actor.getByRole('heading', {name: 'Unavailable calculations', exact: true}).scrollIntoViewIfNeeded();
      }
      await pause(javaScriptEnabled ? 'Inspect the native chart, calculated facts and declared method' : 'Uncertain birth time visibly withholds unsupported calculations', 1800);
      await actor.screenshot({path: 'docs/assets/demos/' + kind + '-chart.png'});
      await actor.getByRole('link', {name: /Ask about this chart/}).click();
      await requireThat(await actor.locator('input[name="chart_id"]').inputValue() === chartId, 'Chart snapshot binding lost');
      await actor.getByLabel('Question', {exact: true}).fill('What source evidence is available for this invented example?');
      await pause('Ask against this exact immutable chart snapshot');
      await actor.getByRole('button', {name: 'Submit question', exact: true}).click();
      await actor.waitForURL(/\/readings\/[0-9a-f-]+$/);
      await actor.getByText('Insufficient evidence to answer', {exact: true}).waitFor();
      await fits();
      await pause('No approved corpus: the reading abstains instead of inventing a prediction', 1800);
      await actor.getByRole('heading', {name: 'Sources', exact: true}).scrollIntoViewIfNeeded();
      await pause('Evidence and limitations remain visible', 1500);
      await actor.getByRole('link', {name: 'Source library', exact: true}).click();
      await actor.getByLabel('Search approved passages').fill('moon signs');
      await actor.getByRole('button', {name: 'Search sources', exact: true}).click();
      await actor.getByText('Source search is not configured.', {exact: true}).waitFor();
      await pause('Library search explains its unavailable state honestly');
      await actor.getByRole('link', {name: 'Data & settings', exact: true}).click();
      await fits();
      await pause('Review browser access limits, separate AI consent, export and deletion', 1700);
      await actor.getByRole('button', {name: 'Request export', exact: true}).click();
      await actor.getByRole('heading', {name: 'Export queued', exact: true}).waitFor();
      const refresh = actor.getByRole('link', {name: 'Refresh export status', exact: true});
      let ready = false;
      for (let attempt = 0; attempt < 12; attempt += 1) {
        if (await actor.getByRole('link', {name: 'Download export', exact: true}).count()) {
          ready = true;
          break;
        }
        await actor.waitForTimeout(500);
        await refresh.click();
      }
      await requireThat(ready, 'The privacy worker did not complete the export');
      const downloadUrl = await actor.getByRole('link', {name: 'Download export', exact: true}).getAttribute('href');
      const exportResponse = await context.request.get(appOrigin + downloadUrl);
      await requireThat(exportResponse.status() === 200, 'Export download failed');
      await requireThat(exportResponse.headers()['cache-control'] === 'no-store', 'Export may be cached');
      await pause('The privacy worker completes a private, expiring data export', 1400);
      await actor.getByRole('link', {name: 'Data & settings', exact: true}).first().click();
      await actor.getByLabel('Type DELETE to confirm', {exact: true}).fill('DELETE');
      await pause('Destructive actions require explicit confirmation');
      await actor.getByRole('button', {name: 'Delete workspace data', exact: true}).click();
      await actor.getByRole('link', {name: 'Start a fresh workspace', exact: true}).waitFor();
      deleted = true;
      await pause('Access is revoked; background deletion has been queued', 1600);
      await requireThat(errors.length === 0, 'Browser JavaScript errors: ' + errors.join('; '));
      results.push({demo: kind, status: 'PASS', javaScriptEnabled, viewport, chartSnapshot: true, export: true, deletion: true, pageErrors: errors.length});
    } finally {
      if (!deleted) {
        await actor.goto(appOrigin + '/settings');
        await actor.getByLabel('Type DELETE to confirm', {exact: true}).fill('DELETE');
        await actor.getByRole('button', {name: 'Delete workspace data', exact: true}).click();
      }
      const video = actor.video();
      await context.close();
      await video.saveAs('docs/assets/demos/' + kind + '-journey.webm');
    }
  }
  await record('desktop', {width: 1280, height: 800}, true);
  await record('mobile', {width: 390, height: 844}, false);
  return {results, chapters, note: 'Invented inputs only; no model call or licensed book content. Edge recordings, no audio.'};
}
