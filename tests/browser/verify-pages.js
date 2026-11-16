// Open the local preview or published guide, then run through playwright-cli.
async page => {
  const base = new URL('./', page.url()).href;
  const context = await page.context().browser().newContext();
  const guide = await context.newPage();
  const failures = [];
  guide.on('pageerror', error => failures.push(error.message));
  guide.on('requestfailed', request => failures.push('Request failed: ' + request.url()));
  const check = (condition, message) => { if (!condition) throw new Error(message); };
  try {
    const response = await guide.goto(base);
    check(response.status() === 200, 'Guide is not HTTP 200');
    await guide.keyboard.press('Tab');
    check(await guide.locator('.skip').evaluate(element => element === document.activeElement), 'Skip link is not first in keyboard order');
    await guide.keyboard.press('Enter');
    await guide.locator('summary').first().focus();
    await guide.keyboard.press('Enter');
    check(await guide.locator('details').first().evaluate(element => element.open), 'Research disclosure does not open from keyboard');
    const targets = await guide.evaluate(() => {
      const attributes = [...document.querySelectorAll('[href], [src], [poster]')]
        .flatMap(element => ['href', 'src', 'poster'].map(name => element.getAttribute(name)).filter(Boolean));
      return {
        assets: [...new Set(attributes.filter(value => !value.startsWith('#') && !/^https?:/.test(value)))],
        anchors: [...new Set(attributes.filter(value => value.startsWith('#')))],
        repository: [...new Set(attributes.filter(value => value.startsWith('https://github.com/sandeshbagmare/astrology-evidence')))],
      };
    });
    for (const anchor of targets.anchors) {
      check(await guide.locator('[id]').evaluateAll((elements, id) => elements.some(element => element.id === id), anchor.slice(1)), 'Missing anchor ' + anchor);
    }
    const assetResults = [];
    for (const asset of targets.assets) {
      const resource = await context.request.get(new URL(asset, base).href, {timeout: 20000});
      check(resource.status() === 200, 'Missing asset ' + asset + ': ' + resource.status());
      const type = resource.headers()['content-type'] || '';
      if (asset.endsWith('.webm')) check(type.includes('video/webm'), 'Incorrect video MIME ' + asset);
      if (asset.endsWith('.vtt')) check(type.includes('text/vtt'), 'Incorrect captions MIME ' + asset);
      assetResults.push({asset, status: resource.status(), type});
      await resource.dispose();
    }
    const repositoryResults = [];
    if (new URL(base).hostname.endsWith('github.io')) {
      for (let index = 0; index < targets.repository.length; index += 3) {
        const group = await Promise.all(targets.repository.slice(index, index + 3).map(async url => {
          let result = await context.request.get(url, {timeout: 30000});
          if (result.status() === 429 || result.status() >= 500) {
            await guide.waitForTimeout(1500);
            result = await context.request.get(url, {timeout: 30000});
          }
          return {url, status: result.status()};
        }));
        for (const result of group) check(result.status === 200, 'Repository link failed: ' + result.url + ' ' + result.status);
        repositoryResults.push(...group);
      }
    }
    const layouts = [];
    for (const width of [1440, 1024, 768, 390, 320]) {
      await guide.setViewportSize({width, height: 900});
      const dimensions = await guide.evaluate(() => ({width: innerWidth, content: document.documentElement.scrollWidth}));
      check(dimensions.content <= dimensions.width, 'Guide overflows at ' + width);
      layouts.push(dimensions);
    }
    await guide.setViewportSize({width: 1280, height: 900});
    const media = await guide.locator('video').evaluateAll(async videos => {
      return await Promise.all(videos.map(async video => {
        video.muted = true;
        video.currentTime = 0;
        const completed = new Promise((resolve, reject) => {
          const timer = setTimeout(() => reject(new Error('Video did not finish within 60 seconds')), 60000);
          video.addEventListener('ended', () => { clearTimeout(timer); resolve(true); }, {once: true});
          video.addEventListener('error', () => { clearTimeout(timer); reject(new Error('Video playback failed')); }, {once: true});
        });
        await video.play();
        await completed;
        const cues = [...(video.textTracks[0]?.cues || [])];
        const data = {
          duration: video.duration,
          width: video.videoWidth,
          height: video.videoHeight,
          completed: video.ended && video.currentTime >= video.duration - 0.1,
          captionTracks: video.textTracks.length,
          captionCues: cues.length,
          captionsWithinDuration: cues.every(cue => cue.startTime >= 0 && cue.endTime <= video.duration + 0.1),
          error: video.error?.message || null,
        };
        return data;
      }));
    });
    for (const result of media) {
      check(result.completed && result.width > 0 && Number.isFinite(result.duration), 'Video did not play to the end with usable metadata');
      check(result.captionTracks === 1 && result.captionCues > 0 && result.captionsWithinDuration && !result.error, 'Video captions or playback error');
    }
    check(media.length === 3, 'Expected three playable demos');
    check(failures.length === 0, 'Browser failures: ' + failures.join('; '));
    return {status: 'PASS', base, anchors: targets.anchors.length, assets: assetResults, repositoryLinks: repositoryResults.length, layouts, media, browserErrors: failures};
  } finally {
    await context.close();
  }
}
