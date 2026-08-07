/**
 * Fixture-based tests for check-responsive.mjs's overflow-detection logic.
 *
 * Independent of astro-site's real content — uses local static fixture
 * HTML via page.setContent()/page.route(), never a real preview server
 * (research.md #9).
 */

import { test, expect } from '@playwright/test';
import {
  measureOverflowAcrossViewports,
  checkPath,
} from '../scripts/check-responsive.mjs';

test.describe('measureOverflowAcrossViewports', () => {
  test('flags overflow only at viewports narrower than a fixed-width element', async ({
    page,
  }) => {
    await page.setContent(`
      <!doctype html>
      <html><body style="margin:0">
        <div style="width: 400px; height: 50px;">fixed-width block</div>
      </body></html>
    `);

    const results = await measureOverflowAcrossViewports(page);

    expect(results).toEqual({
      '320': false, // 400px block doesn't fit in a 320px viewport
      '375': false, // ...or a 375px viewport
      '768': true,
      '1024': true,
      '1920': true,
    });
  });

  test('reports no overflow at any viewport for a fluid page', async ({ page }) => {
    await page.setContent(`
      <!doctype html>
      <html><body style="margin:0">
        <p style="max-width: 100%;">
          Some ordinary text content that wraps normally and never forces
          horizontal scroll, regardless of viewport width.
        </p>
      </body></html>
    `);

    const results = await measureOverflowAcrossViewports(page);

    for (const width of ['320', '375', '768', '1024', '1920']) {
      expect(results[width]).toBe(true);
    }
  });

  test('always returns exactly the five specified viewport keys', async ({ page }) => {
    await page.setContent('<!doctype html><html><body>minimal</body></html>');

    const results = await measureOverflowAcrossViewports(page);

    expect(Object.keys(results).sort()).toEqual(
      ['1024', '1920', '320', '375', '768'].sort()
    );
  });
});

test.describe('checkPath', () => {
  test('resolves with per-viewport results for a successful page', async ({ page }) => {
    await page.route('**/clean-page/', (route) =>
      route.fulfill({
        status: 200,
        contentType: 'text/html',
        body: '<!doctype html><html><body style="margin:0">clean</body></html>',
      })
    );

    const results = await checkPath(page, 'http://fixture.test', '/clean-page/');

    for (const width of ['320', '375', '768', '1024', '1920']) {
      expect(results[width]).toBe(true);
    }
  });

  test('throws when the page returns a non-2xx response', async ({ page }) => {
    await page.route('**/broken-page/', (route) =>
      route.fulfill({ status: 500, body: 'server error' })
    );

    await expect(
      checkPath(page, 'http://fixture.test', '/broken-page/')
    ).rejects.toThrow('500');
  });
});
