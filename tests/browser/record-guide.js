// Open the published guide, then run with playwright-cli run-code --filename.
async page => {
  const context = await page.context().browser().newContext({
    viewport: {width: 1280, height: 800},
    recordVideo: {dir: '.playwright-cli/demo-recordings', size: {width: 1280, height: 800}},
  });
  const guide = await context.newPage();
  const errors = [];
  guide.on('pageerror', error => errors.push(error.message));
  try {
    const response = await guide.goto('https://sandeshbagmare.github.io/astrology-evidence/');
    if (response.status() !== 200) throw new Error('Published guide unavailable');
    await guide.screenshot({path: 'docs/assets/demos/guide-poster.png'});
    await guide.waitForTimeout(1800);
    await guide.getByRole('link', {name: 'How it works', exact: true}).click();
    await guide.waitForTimeout(1500);
    await guide.getByRole('link', {name: 'Reading guide', exact: true}).click();
    await guide.waitForTimeout(1600);
    await guide.getByText('Browse the specialist research by topic', {exact: true}).click();
    await guide.getByRole('link', {name: 'UI research: eight astrology websites', exact: true}).scrollIntoViewIfNeeded();
    await guide.waitForTimeout(1700);
    await guide.getByRole('link', {name: 'Readiness', exact: true}).click();
    await guide.locator('.app-preview img').scrollIntoViewIfNeeded();
    await guide.waitForTimeout(1600);
    await guide.getByRole('heading', {name: 'Required before real users', exact: true}).scrollIntoViewIfNeeded();
    await guide.waitForTimeout(1600);
    await guide.setViewportSize({width: 390, height: 844});
    await guide.goto('https://sandeshbagmare.github.io/astrology-evidence/');
    await guide.waitForTimeout(1800);
    const fit = await guide.evaluate(() => document.documentElement.scrollWidth <= innerWidth);
    if (!fit || errors.length) throw new Error('Guide layout or JavaScript failure');
    return {status: 'PASS', desktop: '1280x800', mobile: '390x844', links: 'navigation and disclosure', pageErrors: 0};
  } finally {
    const video = guide.video();
    await context.close();
    await video.saveAs('docs/assets/demos/guide-tour.webm');
  }
}
