import { test, expect } from '@playwright/test';

const routes = ['top', 'work', 'about', 'research', 'now'];

async function expectOnlyPage(page, route) {
  // Assert absence from the DOM, not merely that CSS hides the other pages.
  await expect(page.locator('main > [data-page]')).toHaveCount(1);
  await expect(page.locator(`main > [data-page="${route}"]`)).toBeVisible();
  for (const other of routes.filter((value) => value !== route)) {
    await expect(page.locator(`[data-page="${other}"]`)).toHaveCount(0);
  }
  await expect(page.locator('main h1')).toHaveCount(1);
  await expect(page.locator('[data-panel]')).toHaveCount(0);
  const width = await page.evaluate(() => ({ page: document.documentElement.scrollWidth, viewport: innerWidth }));
  expect(width.page).toBeLessThanOrEqual(width.viewport);
}

test('every navigation transition unmounts the previous page', async ({ page }) => {
  const errors = [];
  page.on('pageerror', (error) => errors.push(error.message));
  for (const from of routes) {
    for (const to of routes.filter((route) => route !== from)) {
      await page.goto(`/#${from}`);
      await expectOnlyPage(page, from);
      await page.evaluate(() => { window.previousPage = document.querySelector('main > [data-page]'); });
      const link = to === 'top' ? page.locator('.mark') : page.locator(`nav a[href="#${to}"]`);
      await link.click();
      await expectOnlyPage(page, to);
      expect(await page.evaluate(() => window.previousPage.isConnected)).toBe(false);
      await expect(page).toHaveURL(new RegExp(`#${to}$`));
      await expect(page.locator('main h1')).toBeFocused();
      if (to !== 'top') {
        await expect(link).toHaveAttribute('aria-current', 'page');
        await expect(page.locator('footer')).toHaveCount(0);
      }
    }
  }
  expect(errors).toEqual([]);
});

test('Research stays isolated after refresh and history navigation', async ({ page }) => {
  await page.goto('/#about');
  await page.locator('nav a[href="#work"]').click();
  await page.locator('nav a[href="#research"]').click();
  await expectOnlyPage(page, 'research');
  await expect(page.locator('main')).not.toContainText('ShiftGuard');
  await expect(page.locator('main')).not.toContainText('University of Southern Mississippi');
  await page.reload();
  await expectOnlyPage(page, 'research');
  await page.goBack();
  await expectOnlyPage(page, 'work');
  await page.goForward();
  await expectOnlyPage(page, 'research');
  // Even hostile layout overrides cannot bring back a page that was unmounted.
  await page.addStyleTag({ content: 'section, [hidden], [inert] { display: block !important; visibility: visible !important; }' });
  await expectOnlyPage(page, 'research');
  await expect(page.locator('main h1')).toHaveText('What I’m studying');
  await expect(page.locator('.research-entry')).toHaveCount(2);
  await expect(page.getByRole('link', { name: 'Read the paper' })).toHaveAttribute('href', 'https://arxiv.org/abs/2605.17201');
  await page.screenshot({ path: test.info().outputPath('research.png'), fullPage: true });
});

test('keyboard navigation, repeated clicks, invalid hashes, and download', async ({ page }) => {
  await page.goto('/#about');
  await page.keyboard.press('Tab');
  await expect(page.locator('.skip-link')).toBeFocused();
  await page.keyboard.press('Enter');
  await expect(page.locator('main')).toBeFocused();
  await expectOnlyPage(page, 'about');
  await page.locator('nav a[href="#research"]').focus();
  await page.keyboard.press('Enter');
  await expectOnlyPage(page, 'research');
  await page.locator('nav a[href="#research"]').click();
  await expectOnlyPage(page, 'research');
  await page.goto('/#unknown');
  await expectOnlyPage(page, 'top');
  const downloaded = page.waitForEvent('download');
  await page.locator('.header-resume').click();
  const download = await downloaded;
  expect(download.suggestedFilename()).toBe('Kshitiz-Neupane-Resume.pdf');
  expect(await download.failure()).toBeNull();
  const animations = await page.evaluate(() => [...document.querySelectorAll('*')].filter((element) => {
    const style = getComputedStyle(element);
    return style.animationName !== 'none' || style.transitionDuration.split(',').some((value) => parseFloat(value) > 0);
  }).length);
  expect(animations).toBe(0);
});

test('published files work from a GitHub Pages repository subpath', async ({ page }) => {
  // Serve the same generated artifact under /portfolio/ without changing its relative URLs.
  await page.route('**/portfolio/**', async (route) => {
    const url = new URL(route.request().url());
    url.pathname = url.pathname.replace(/^\/portfolio\//, '/');
    const response = await route.fetch({ url: url.href });
    await route.fulfill({ response });
  });
  await page.goto('/portfolio/#research');
  await expectOnlyPage(page, 'research');
  await page.locator('nav a[href="#about"]').click();
  await expectOnlyPage(page, 'about');
  await expect(page).toHaveURL(/\/portfolio\/#about$/);
});

test('project images load and filters show the correct work', async ({ page }) => {
  await page.goto('/#work');
  await expect(page.locator('.project')).toHaveCount(3);
  for (const image of await page.locator('.project img').all()) {
    await image.scrollIntoViewIfNeeded();
    await expect.poll(() => image.evaluate(el => el.complete && el.naturalWidth > 0)).toBe(true);
  }
  await page.getByRole('button', { name: 'Machine learning', exact: true }).click();
  await expect(page.locator('.project')).toHaveCount(3);
  await expect(page.locator('#project-shiftguard')).toBeVisible();
  await expect(page.locator('#project-f1')).toHaveCount(0);
  await page.getByRole('button', { name: 'Data science', exact: true }).click();
  await expect(page.locator('.project')).toHaveCount(3);
  await expect(page.locator('#project-f1')).toBeVisible();
  await page.getByRole('button', { name: 'Software', exact: true }).click();
  await expect(page.locator('.project')).toHaveCount(3);
  await expect(page.locator('#project-workforge')).toBeVisible();
  await page.screenshot({ path: test.info().outputPath('work.png'), fullPage: true });
  await page.locator('.mark').click();
  await expect(page.locator('.home-motto')).toHaveText('Carpe Diem');
  await expect(page.locator('main h1')).toHaveText('Kshitiz Neupane');
  await expect(page.locator('.home-avatar')).toHaveAttribute('alt', 'Pencil sketch portrait of Kshitiz Neupane');
  await expect.poll(() => page.locator('.home-avatar').evaluate(image => image.complete && image.naturalWidth > 0)).toBe(true);
  await expect(page.locator('.hero-feature')).toHaveCount(0);
  await page.screenshot({ path: test.info().outputPath('home.png'), fullPage: true });
});


test('ongoing work and the short bio reflect the current profile', async ({ page }) => {
  await page.goto('/#now');
  await expect(page.locator('.now-item h2')).toHaveText(['agriculture-ai', 'WMSV', 'solver-verifier-research']);
  await expect(page.locator('.now-item a')).toHaveCount(0);
  await page.locator('nav a[href="#about"]').click();
  await expect(page.locator('.bio')).toContainText('I am a student passionate about machine learning');
  await expect(page.locator('.bio')).toContainText('badminton');
  await expect(page.locator('.about-portrait img')).toHaveAttribute('alt', 'Pencil sketch portrait of Kshitiz Neupane');
  await expect.poll(() => page.locator('.about-portrait img').evaluate(image => image.complete && image.naturalWidth > 0)).toBe(true);
});

test('every project has its own page with details and project visuals', async ({ page }) => {
  const projects = {
    shiftguard: 5,
    f1: 5,
    bayesian: 5,
    pca: 4,
    workforge: 4,
    manageyourhome: 5,
    'money-manager': 1,
  };

  for (const [id, imageCount] of Object.entries(projects)) {
    await page.goto(`/#project/${id}`);
    await expect(page.locator(`main > [data-page="project-${id}"]`)).toBeVisible();
    await expect(page.locator('.project-page-content')).toBeVisible();
    await expect(page.locator('.project-page-content section > p:not(.eyebrow)')).toHaveCount(2);
    await expect(page.locator('.project-page img')).toHaveCount(imageCount + (imageCount > 1 ? 1 : 0));
    await expect(page.locator('nav a[href="#work"]')).toHaveAttribute('aria-current', 'page');
    const width = await page.evaluate(() => ({ page: document.documentElement.scrollWidth, viewport: innerWidth }));
    expect(width.page).toBeLessThanOrEqual(width.viewport);
  }

  await page.goto('/#work');
  await page.getByRole('button', { name: 'Data science', exact: true }).click();
  await page.locator('#project-f1 a[href="#project/f1"]').click();
  await expect(page).toHaveURL(/#project\/f1$/);
  await expect(page.locator('#project-page-title')).toHaveText('F1 Race Analysis');
  await page.locator('.back-link').click();
  await expectOnlyPage(page, 'work');
});
