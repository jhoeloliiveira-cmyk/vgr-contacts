#!/usr/bin/env node
/**
 * travel-watch — coletor de preços via navegador headless.
 *
 *   check.mjs flights --from LGW --to LIS --date 2026-10-18 [--currency GBP] [--adults 1]
 *   check.mjs hotels  --city London --checkin 2026-10-16 --checkout 2026-10-18 [--adults 1] [--stars 3]
 *
 * Sai com 3 e imprime "BLOCKED: <motivo>" quando a rede barra a fonte.
 * Nesse caso o chamador deve descer para WebFetch/WebSearch, nao insistir aqui.
 */
import { createRequire } from 'node:module';
import { existsSync, readdirSync } from 'node:fs';
import path from 'node:path';

const require = createRequire(import.meta.url);

// --- args -------------------------------------------------------------
const [, , mode, ...rest] = process.argv;
const args = {};
for (let i = 0; i < rest.length; i += 2) {
  if (rest[i]?.startsWith('--')) args[rest[i].slice(2)] = rest[i + 1];
}
const need = (k) => {
  if (!args[k]) {
    console.error(`erro: falta --${k}`);
    process.exit(2);
  }
  return args[k];
};

// --- localizar playwright + chromium ----------------------------------
function loadPlaywright() {
  const candidates = [
    'playwright',
    'playwright-core',
    '/opt/node22/lib/node_modules/playwright',
    '/usr/lib/node_modules/playwright',
  ];
  for (const c of candidates) {
    try { return require(c); } catch { /* proximo */ }
  }
  console.error('BLOCKED: playwright nao instalado (npm i -g playwright) — use WebFetch/WebSearch');
  process.exit(3);
}

function findChromium() {
  if (process.env.CHROMIUM_PATH && existsSync(process.env.CHROMIUM_PATH)) return process.env.CHROMIUM_PATH;
  const root = process.env.PLAYWRIGHT_BROWSERS_PATH || '/opt/pw-browsers';
  if (existsSync(root)) {
    // aceita chromium/ e chromium-<rev>/, prefere o revision mais alto
    const dirs = readdirSync(root)
      .filter((d) => d.startsWith('chromium') && !d.includes('headless'))
      .sort()
      .reverse();
    for (const d of dirs) {
      const bin = path.join(root, d, 'chrome-linux', 'chrome');
      if (existsSync(bin)) return bin;
    }
  }
  return undefined; // deixa o playwright resolver sozinho
}

const proxyUrl = process.env.HTTPS_PROXY || process.env.https_proxy;

async function browse(url, { waitFor, settle = 8000 } = {}) {
  const { chromium } = loadPlaywright();
  const executablePath = findChromium();
  let browser;
  try {
    browser = await chromium.launch({
      ...(executablePath ? { executablePath } : {}),
      ...(proxyUrl ? { proxy: { server: proxyUrl } } : {}),
      args: ['--no-sandbox', '--disable-dev-shm-usage'],
    });
  } catch (e) {
    console.error(`BLOCKED: nao subiu o chromium — ${e.message}`);
    process.exit(3);
  }
  const ctx = await browser.newContext({
    locale: 'en-GB',
    timezoneId: 'Europe/London',
    ignoreHTTPSErrors: true,
    userAgent:
      'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/140.0.0.0 Safari/537.36',
  });
  const page = await ctx.newPage();
  try {
    await page.goto(url, { waitUntil: 'domcontentloaded', timeout: 90000 });
  } catch (e) {
    await browser.close();
    const m = e.message || '';
    // ERR_TUNNEL_CONNECTION_FAILED / 403 do proxy / DNS = politica de rede
    if (/TUNNEL|PROXY|NAME_NOT_RESOLVED|CONNECTION_(REFUSED|RESET|CLOSED)|ERR_ABORTED|403/i.test(m)) {
      console.error(`BLOCKED: rede barrou ${new URL(url).hostname} — ${m.split('\n')[0]}`);
      process.exit(3);
    }
    console.error(`erro ao abrir ${url}: ${m.split('\n')[0]}`);
    process.exit(1);
  }

  // muros de consentimento de cookie
  for (const sel of [
    'button:has-text("Accept all")',
    'button[aria-label*="Accept"]',
    '#onetrust-accept-btn-handler',
    'button:has-text("Reject all")',
  ]) {
    try {
      const b = page.locator(sel).first();
      if ((await b.count()) && (await b.isVisible({ timeout: 1500 }))) {
        await b.click({ timeout: 4000 });
        break;
      }
    } catch { /* segue */ }
  }

  if (waitFor) {
    try { await page.waitForSelector(waitFor, { timeout: 30000 }); }
    catch { console.error(`aviso: seletor "${waitFor}" nao apareceu — pagina pode ter mudado de layout`); }
  }
  await page.waitForTimeout(settle);
  return { browser, page };
}

const PRICE_RE = /(?:£|\$|€|R\$)\s?\d[\d.,]*/;

function parsePrice(text) {
  const m = text.match(PRICE_RE);
  if (!m) return null;
  const raw = m[0];
  const currency = raw.startsWith('£') ? 'GBP' : raw.startsWith('€') ? 'EUR' : raw.startsWith('R$') ? 'BRL' : 'USD';
  const amount = parseFloat(raw.replace(/[^\d.,]/g, '').replace(/,(?=\d{3}\b)/g, '').replace(',', '.'));
  return Number.isFinite(amount) ? { amount, currency, raw } : null;
}

// --- voos: Google Flights ---------------------------------------------
async function flights() {
  const from = need('from'), to = need('to'), date = need('date');
  const currency = args.currency || 'GBP';
  const q = `Flights to ${to} from ${from} on ${date} oneway`;
  const url = `https://www.google.com/travel/flights?q=${encodeURIComponent(q)}&curr=${currency}&hl=en-GB&gl=GB`;

  const { browser, page } = await browse(url, { waitFor: 'li.pIav2d', settle: 6000 });
  const rows = await page.$$eval('li.pIav2d', (els) =>
    els.map((el) => el.innerText.replace(/\n+/g, ' | ').trim()).filter(Boolean)
  ).catch(() => []);
  await browser.close();

  if (!rows.length) {
    console.error('sem resultados — layout do Google Flights pode ter mudado, ou a data nao tem voo');
    process.exit(1);
  }

  const parsed = rows.map((text) => {
    const price = parsePrice(text);
    const times = text.match(/\d{1,2}:\d{2}\s?(?:AM|PM)?/g) || [];
    const dur = text.match(/\d+\s?hr(?:\s?\d+\s?min)?/)?.[0] || null;
    const stops = /Nonstop/i.test(text) ? 'direto' : (text.match(/\d+ stop\w*/i)?.[0] || null);
    return { price, depart: times[0] || null, arrive: times[1] || null, duration: dur, stops, text };
  }).filter((r) => r.price);

  parsed.sort((a, b) => a.price.amount - b.price.amount);
  console.log(JSON.stringify({
    kind: 'flights', route: `${from}-${to}`, date, source: 'google-flights',
    checkedAt: new Date().toISOString(),
    cheapest: parsed[0] || null,
    results: parsed.slice(0, 12),
  }, null, 2));
}

// --- hoteis: Booking.com ----------------------------------------------
async function hotels() {
  const city = need('city'), checkin = need('checkin'), checkout = need('checkout');
  const adults = args.adults || '1';
  const url = `https://www.booking.com/searchresults.html?ss=${encodeURIComponent(city)}` +
    `&checkin=${checkin}&checkout=${checkout}&group_adults=${adults}&no_rooms=1&group_children=0` +
    `&order=price&selected_currency=GBP`;

  const { browser, page } = await browse(url, { waitFor: '[data-testid="property-card"]', settle: 6000 });
  const rows = await page.$$eval('[data-testid="property-card"]', (els) =>
    els.slice(0, 25).map((el) => ({
      name: el.querySelector('[data-testid="title"]')?.innerText?.trim() || null,
      area: el.querySelector('[data-testid="address"]')?.innerText?.trim() || null,
      score: el.querySelector('[data-testid="review-score"]')?.innerText?.replace(/\n+/g, ' ').trim() || null,
      priceText: el.querySelector('[data-testid="price-and-discounted-price"]')?.innerText?.trim() || null,
    }))
  ).catch(() => []);
  await browser.close();

  const parsed = rows
    .map((r) => ({ ...r, price: r.priceText ? parsePrice(r.priceText) : null }))
    .filter((r) => r.price && r.name);
  parsed.sort((a, b) => a.price.amount - b.price.amount);

  if (!parsed.length) {
    console.error('sem resultados — Booking pode ter mudado de layout ou pedido captcha');
    process.exit(1);
  }
  const nights = Math.round((new Date(checkout) - new Date(checkin)) / 86400000);
  console.log(JSON.stringify({
    kind: 'hotels', city, checkin, checkout, nights, source: 'booking.com',
    checkedAt: new Date().toISOString(),
    note: `precos sao o total de ${nights} noite(s), nao a diaria`,
    cheapest: parsed[0] || null,
    results: parsed.slice(0, 15),
  }, null, 2));
}

if (mode === 'flights') await flights();
else if (mode === 'hotels') await hotels();
else {
  console.error('uso: check.mjs flights --from LGW --to LIS --date 2026-10-18');
  console.error('     check.mjs hotels --city London --checkin 2026-10-16 --checkout 2026-10-18');
  process.exit(2);
}
