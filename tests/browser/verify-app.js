// Open the local synthetic app, then run through playwright-cli.
async page => {
  const origin = new URL(page.url()).origin;
  if (!['127.0.0.1', 'localhost'].includes(new URL(origin).hostname)) throw new Error('Open the local synthetic app first');
  const alias = 'Synthetic refresh ' + Date.now();
  const browser = page.context().browser();
  const context = await browser.newContext({viewport:{width:1440,height:1000}});
  const contexts = [context];
  const deletedContexts = new Set();
  let primaryFailure;
  try {
  const owner = await context.newPage();
  const pageErrors = [];
  owner.on('pageerror', error => pageErrors.push(error.message));
  const home = await owner.goto(origin);
  if (home.status() !== 200) throw new Error('Home does not open');
  if (await owner.locator('a[href="/login"],form input[value="logout"]').count()) throw new Error('Login UI present');
  const paths = ['/', '/profiles', '/charts', '/readings', '/readings/new', '/library', '/settings', '/profiles/new'];
  const layouts = [];
  for (const width of [1440,768,320]) {
    await owner.setViewportSize({width,height:900});
    for (const path of paths) {
      const response = await owner.goto(origin + path);
      if (response.status() !== 200) throw new Error(path + ' returned ' + response.status());
      const size = await owner.evaluate(() => ({width:innerWidth,scrollWidth:document.documentElement.scrollWidth}));
      if (size.scrollWidth > size.width) {
        const overflowing = await owner.evaluate(() => [...document.querySelectorAll('input,select,label,fieldset,section,aside')]
          .map(element => ({tag:element.tagName,name:element.getAttribute('name'),right:element.getBoundingClientRect().right}))
          .filter(element => element.right > innerWidth).slice(0, 8));
        throw new Error('Overflow ' + path + ' at ' + width + ': ' + size.scrollWidth + ' ' + JSON.stringify(overflowing));
      }
      if (await owner.locator('a[href="/login"],input[value="logout"]').count()) throw new Error('Login UI on ' + path);
      layouts.push({path,width,pass:true});
    }
  }
  await owner.goto(origin + '/profiles/new');
  await owner.getByLabel('Alias', {exact:true}).fill(alias);
  await owner.getByLabel('Birth date', {exact:true}).fill('2024-11-03');
  await owner.getByLabel('Local time', {exact:true}).fill('01:30');
  await owner.getByLabel('Latitude', {exact:true}).fill('40.7');
  await owner.getByLabel('Longitude', {exact:true}).fill('-74.0');
  await owner.getByLabel('Time zone', {exact:true}).fill('America/New_York');
  await owner.getByLabel('Historical timezone confidence').selectOption('confirmed');
  await owner.getByLabel('Time zone', {exact:true}).press('Tab');
  await owner.getByRole('option', {name:'Second occurrence (UTC-05:00)', exact:true}).waitFor({state:'attached'});
  await owner.getByLabel('Occurrence when the local time repeats').selectOption('1');
  await owner.locator('input[name="storage_consent"]').check();
  await owner.getByRole('button', {name:'Save profile',exact:true}).click();
  await owner.waitForURL('**/dashboard');
  const profileRecords = await owner.evaluate(async () => (await fetch('/api/profiles')).json());
  const profileRecord = profileRecords.find(p => p.alias === alias);
  if (!profileRecord || profileRecord.birth_input.fold !== 1) throw new Error('Fold/profile not saved');
  await owner.goto(origin + '/profiles');
  const card = owner.locator('article').filter({has:owner.getByRole('heading', {name:alias,exact:true})});
  await card.getByRole('button', {name:'Calculate chart',exact:true}).click();
  await owner.waitForURL('**/charts/*');
  const chartId = owner.url().split('/').pop();
  const chart = await owner.evaluate(async id => (await fetch('/api/charts/' + id)).json(), chartId);
  if (!chart.facts.length) throw new Error('Chart has no facts');
  await owner.getByRole('link', {name:/Ask about this chart/i}).click();
  await owner.waitForURL('**/readings/new?*');
  if (await owner.locator('input[name="chart_id"]').inputValue() !== chartId) throw new Error('Chart context lost');
  await owner.getByLabel('Question',{exact:true}).fill('What source evidence is available for this synthetic chart?');
  await owner.getByRole('button',{name:'Submit question',exact:true}).click();
  await owner.waitForURL(/\/readings\/[0-9a-f-]+$/);
  await owner.getByText('Insufficient evidence to answer',{exact:true}).waitFor();
  const readingId = owner.url().split('/').pop();
  const foreignContext = await browser.newContext({viewport:{width:320,height:740}});
  contexts.push(foreignContext);
  const stranger = await foreignContext.newPage();
  await stranger.goto(origin);
  const denied = await stranger.evaluate(async ids => {
    const me = await (await fetch('/api/me')).json();
    const headers = {'Content-Type':'application/json','X-CSRF-Token':me.csrf_token};
    return {
      profiles:await (await fetch('/api/profiles')).json(),
      profile:(await fetch('/api/profiles/' + ids.profile)).status,
      chart:(await fetch('/api/charts/' + ids.chart)).status,
      reading:(await fetch('/api/readings/' + ids.reading)).status,
      delete:(await fetch('/api/readings/' + ids.reading,{method:'DELETE',headers})).status,
      admin:(await fetch('/admin/corpus')).status,
    };
  }, {profile:profileRecord.id,chart:chartId,reading:readingId});
  if (denied.profiles.length || [denied.profile,denied.chart,denied.reading,denied.delete].some(status=>status!==404) || denied.admin!==403) throw new Error('Guest isolation failed ' + JSON.stringify(denied));
  await owner.getByLabel('Type DELETE to remove this reading:').fill('DELETE');
  await owner.getByRole('button',{name:'Delete reading',exact:true}).click();
  await owner.waitForURL('**/readings');
  await owner.goto(origin + '/profiles/' + profileRecord.id + '/edit');
  const deleteProfile = owner.getByRole('button', {name:'Delete profile and its readings',exact:true});
  await deleteProfile.click();
  const confirmation = owner.getByLabel('Type DELETE to remove this profile and its readings:', {exact:true});
  if (await confirmation.evaluate(input => input.validity.valid)) throw new Error('Profile deletion does not require confirmation');
  const unconfirmed = await context.request.get(origin + '/api/profiles/' + profileRecord.id);
  if (unconfirmed.status() !== 200) throw new Error('Unconfirmed profile deletion removed data');
  await confirmation.fill('DELETE');
  await deleteProfile.click();
  await owner.waitForURL('**/dashboard');
  for (const resource of ['/api/profiles/' + profileRecord.id, '/api/charts/' + chartId]) {
    const removed = await context.request.get(origin + resource);
    if (removed.status() !== 404) throw new Error('Confirmed profile deletion did not revoke ' + resource);
  }
  const nojs = await browser.newContext({javaScriptEnabled:false,viewport:{width:320,height:740}});
  contexts.push(nojs);
  const fallback = await nojs.newPage();
  await fallback.goto(origin + '/profiles/new');
  await fallback.getByLabel('Alias',{exact:true}).fill(alias + ' no JS');
  await fallback.getByLabel('Birth date',{exact:true}).fill('2024-11-03');
  await fallback.getByLabel('Local time',{exact:true}).fill('01:30');
  await fallback.getByLabel('Latitude',{exact:true}).fill('40.7');
  await fallback.getByLabel('Longitude',{exact:true}).fill('-74.0');
  await fallback.getByLabel('Time zone',{exact:true}).fill('America/New_York');
  await fallback.getByLabel('Historical timezone confidence').selectOption('confirmed');
  await fallback.locator('input[name="storage_consent"]').check();
  await fallback.getByRole('button',{name:'Save profile',exact:true}).click();
  await fallback.getByRole('option',{name:'Second occurrence (UTC-05:00)',exact:true}).waitFor({state:'attached'});
  await fallback.getByLabel('Occurrence when the local time repeats').selectOption('1');
  await fallback.locator('input[name="storage_consent"]').check();
  await fallback.getByRole('button',{name:'Save profile',exact:true}).click();
  await fallback.waitForURL('**/dashboard');
  await fallback.goto(origin + '/settings');
  await fallback.getByRole('button',{name:'Request export',exact:true}).click();
  await fallback.getByRole('heading',{name:'Export queued',exact:true}).waitFor();
  const download = fallback.getByRole('link', {name:'Download export',exact:true});
  const exportDeadline = Date.now() + 15000;
  while (!(await download.count()) && Date.now() < exportDeadline) {
    await fallback.waitForTimeout(Math.max(0, Math.min(500, exportDeadline - Date.now())));
    const remaining = exportDeadline - Date.now();
    if (remaining <= 0) break;
    await fallback.getByRole('link', {name:'Refresh export status',exact:true}).click({timeout:remaining});
  }
  if (!(await download.count())) throw new Error('Privacy worker did not finish the export within 15 seconds');
  const exportUrl = new URL(await download.getAttribute('href'), origin).href;
  const exported = await nojs.request.get(exportUrl);
  if (exported.status() !== 200 || exported.headers()['cache-control'] !== 'no-store') throw new Error('Owner export download failed or may be cached');
  await exported.dispose();
  const forbiddenExport = await foreignContext.request.get(exportUrl);
  if (forbiddenExport.status() !== 404) throw new Error('Export is accessible from another workspace');
  await forbiddenExport.dispose();
  await fallback.goto(origin + '/settings');
  await fallback.getByLabel('Type DELETE to confirm',{exact:true}).fill('DELETE');
  await fallback.getByRole('button',{name:'Delete workspace data',exact:true}).click();
  await fallback.getByRole('link',{name:'Start a fresh workspace',exact:true}).waitFor();
  deletedContexts.add(nojs);
  if (pageErrors.length) throw new Error('Page errors ' + JSON.stringify(pageErrors));
  return {status:'PASS',layouts:layouts.length,guestIsolation:denied,chartFacts:chart.facts.length,jsErrors:pageErrors.length,profileDeletion:true,exportCompleted:true,exportOwnerOnly:true,flow:'guest/DST/chart/reading/delete/noJS/export/delete-workspace'};
  } catch (error) {
    primaryFailure = error;
    throw error;
  } finally {
    const cleanupErrors = [];
    for (const disposable of contexts.reverse()) {
      try {
        if (deletedContexts.has(disposable)) continue;
        const cleanup = await disposable.newPage();
        await cleanup.goto(origin + '/settings');
        const remove = cleanup.getByRole('button', {name: 'Delete workspace data', exact: true});
        if (await remove.count()) {
          await cleanup.getByLabel('Type DELETE to confirm', {exact: true}).fill('DELETE');
          await remove.click();
          await cleanup.getByRole('link', {name: 'Start a fresh workspace', exact: true}).waitFor();
        }
      } catch (error) {
        cleanupErrors.push(error);
      } finally {
        try {
          await disposable.close();
        } catch (error) {
          cleanupErrors.push(error);
        }
      }
    }
    if (cleanupErrors.length) {
      if (primaryFailure) primaryFailure.cleanupErrors = cleanupErrors;
      else throw new AggregateError(cleanupErrors, 'Browser verification cleanup failed');
    }
  }
}
