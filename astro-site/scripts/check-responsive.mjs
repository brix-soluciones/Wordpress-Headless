/**
 * Overflow-check CLI for the WordPress-to-Astro migration skill.
 *
 * Usage: node check-responsive.mjs <preview-base-url> <path> [<path> ...]
 *
 * Contract: specs/003-astro-migration-skill/contracts/check-responsive-cli.md
 *
 * The two functions below (`measureOverflowAcrossViewports`, `checkPath`)
 * are exported so tests/check-responsive.spec.mjs can exercise the
 * overflow-detection logic directly against local fixture HTML, without
 * spawning this file as a subprocess or standing up a real HTTP server
 * (research.md #9). `main()` is the CLI entrypoint and only runs when
 * this file is executed directly.
 */

import { pathToFileURL } from 'node:url';

import { chromium } from '@playwright/test';

const VIEWPORT_WIDTHS = [320, 375, 768, 1024, 1920];
const VIEWPORT_HEIGHT = 1000;

/**
 * Resize `page` to each of the five specified viewport widths and
 * evaluate horizontal overflow at each (research.md #3):
 * `document.documentElement.scrollWidth > document.documentElement.clientWidth`.
 *
 * Assumes `page` already has content loaded (via `goto` or `setContent`).
 *
 * @param {import('playwright').Page} page
 * @returns {Promise<Record<string, boolean>>} per-viewport result, keyed
 *   by width as a string — `true` means no overflow (pass), `false`
 *   means overflow (fail), per contracts/check-responsive-cli.md.
 */
export async function measureOverflowAcrossViewports(page) {
  const perViewport = {};

  for (const width of VIEWPORT_WIDTHS) {
    await page.setViewportSize({ width, height: VIEWPORT_HEIGHT });
    const hasOverflow = await page.evaluate(
      () => document.documentElement.scrollWidth > document.documentElement.clientWidth
    );
    perViewport[String(width)] = !hasOverflow;
  }

  return perViewport;
}

/**
 * Navigate `page` to `path` (resolved against `baseUrl`) and measure
 * overflow across all five viewports.
 *
 * @param {import('playwright').Page} page
 * @param {string} baseUrl
 * @param {string} path
 * @returns {Promise<Record<string, boolean>>}
 * @throws if the navigation doesn't return a 2xx response.
 */
export async function checkPath(page, baseUrl, path) {
  const url = new URL(path, baseUrl).toString();

  const response = await page.goto(url, { waitUntil: 'load' });
  if (!response || !response.ok()) {
    const status = response ? response.status() : 'no response';
    throw new Error(`GET ${url} returned ${status}`);
  }

  return measureOverflowAcrossViewports(page);
}

function usageError(message) {
  process.stderr.write(`${message}\n`);
  process.stderr.write(
    'Usage: node check-responsive.mjs <preview-base-url> <path> [<path> ...]\n'
  );
  process.exit(1);
}

async function main() {
  const [baseUrl, ...paths] = process.argv.slice(2);

  if (!baseUrl || paths.length === 0) {
    usageError('Missing required arguments.');
    return;
  }

  let browser;
  try {
    browser = await chromium.launch();
    const page = await browser.newPage();

    const results = {};
    for (const path of paths) {
      results[path] = await checkPath(page, baseUrl, path);
    }

    process.stdout.write(`${JSON.stringify({ results })}\n`);
  } catch (error) {
    process.stderr.write(`${error.message}\n`);
    process.exitCode = 1;
  } finally {
    if (browser) {
      await browser.close();
    }
  }
}

const isMain = process.argv[1] && import.meta.url === pathToFileURL(process.argv[1]).href;
if (isMain) {
  main();
}
