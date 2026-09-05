#!/usr/bin/env node
/**
 * travel-watch — historico de precos.
 *
 *   history.mjs record --key flight:LGW-LIS:2026-10-18 --price 78.99 --currency GBP \
 *                      --label "easyJet 06:25" --source google-flights
 *   history.mjs report --key flight:LGW-LIS:2026-10-18 [--target 70]
 *   history.mjs report --all
 *
 * Guarda em ../data/history.json. Commite depois de gravar — sem commit,
 * a serie temporal morre junto com o container.
 */
import { readFileSync, writeFileSync, mkdirSync, existsSync } from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

const HERE = path.dirname(fileURLToPath(import.meta.url));
const DATA_DIR = path.join(HERE, '..', 'data');
const DB = path.join(DATA_DIR, 'history.json');

const [, , cmd, ...rest] = process.argv;
const args = {};
for (let i = 0; i < rest.length; i += 2) {
  if (rest[i]?.startsWith('--')) args[rest[i].slice(2)] = rest[i + 1] ?? true;
}

const load = () => (existsSync(DB) ? JSON.parse(readFileSync(DB, 'utf8')) : { series: {} });
const save = (db) => {
  mkdirSync(DATA_DIR, { recursive: true });
  writeFileSync(DB, JSON.stringify(db, null, 2) + '\n');
};
const money = (n, c) => `${{ GBP: '£', EUR: '€', USD: '$', BRL: 'R$' }[c] || ''}${n.toFixed(2)}${c && !['GBP','EUR','USD','BRL'].includes(c) ? ' ' + c : ''}`;

function record() {
  const key = args.key, price = parseFloat(args.price);
  if (!key || !Number.isFinite(price)) {
    console.error('erro: --key e --price (numerico) sao obrigatorios');
    process.exit(2);
  }
  const db = load();
  const s = (db.series[key] ??= { key, currency: args.currency || 'GBP', points: [] });
  if (args.currency && args.currency !== s.currency) {
    console.error(`erro: serie "${key}" esta em ${s.currency}, recebeu ${args.currency}. ` +
      `Converta antes de gravar ou use outra --key. Misturar moeda invalida o historico.`);
    process.exit(2);
  }
  s.points.push({
    at: new Date().toISOString(),
    price,
    label: args.label || null,
    source: args.source || null,
  });
  save(db);

  const pts = s.points;
  const prev = pts.length > 1 ? pts[pts.length - 2].price : null;
  const delta = prev === null ? null : price - prev;
  console.log(`gravado ${key}: ${money(price, s.currency)}` +
    (delta === null ? ' (primeira leitura)'
      : delta === 0 ? ' (sem mudanca)'
      : ` (${delta > 0 ? '+' : ''}${money(delta, s.currency)} vs. leitura anterior)`));
}

function summarize(s, target) {
  const pts = s.points;
  if (!pts.length) return { key: s.key, empty: true };
  const cur = pts[pts.length - 1];
  const prev = pts.length > 1 ? pts[pts.length - 2] : null;
  const prices = pts.map((p) => p.price);
  const min = Math.min(...prices), max = Math.max(...prices);
  const minPt = pts.find((p) => p.price === min);
  const delta = prev ? cur.price - prev.price : null;
  const pct = prev && prev.price ? (delta / prev.price) * 100 : null;
  return {
    key: s.key, currency: s.currency, readings: pts.length,
    current: cur, previous: prev, delta, pct, min, minAt: minPt?.at, max,
    isAllTimeLow: cur.price <= min,
    target: target ?? null,
    hitTarget: target != null ? cur.price <= target : null,
    // gatilho de alerta: abaixo do alvo, ou queda >= 10%
    shouldAlert: (target != null && cur.price <= target) || (pct != null && pct <= -10),
  };
}

function printSummary(r) {
  if (r.empty) { console.log(`${r.key}: sem leituras`); return; }
  const c = r.currency;
  console.log(`\n${r.key}`);
  console.log(`  agora      ${money(r.current.price, c)}` +
    (r.current.label ? `  — ${r.current.label}` : '') +
    (r.current.source ? `  [${r.current.source}]` : ''));
  if (r.delta === null) console.log('  variacao   primeira leitura');
  else if (r.delta === 0) console.log('  variacao   estavel desde a ultima checagem');
  else console.log(`  variacao   ${r.delta > 0 ? '▲ subiu' : '▼ caiu'} ${money(Math.abs(r.delta), c)}` +
    ` (${r.pct.toFixed(1)}%) desde ${new Date(r.previous.at).toISOString().slice(0, 16).replace('T', ' ')}`);
  console.log(`  minimo     ${money(r.min, c)}${r.isAllTimeLow ? '  ← esta no minimo historico' : ''}` +
    `   maximo ${money(r.max, c)}   (${r.readings} leitura${r.readings > 1 ? 's' : ''})`);
  if (r.target != null) {
    console.log(`  alvo       ${money(r.target, c)} — ${r.hitTarget ? 'ATINGIDO ✓' : `faltam ${money(r.current.price - r.target, c)}`}`);
  }
  if (r.shouldAlert) console.log('  >> ALERTA: notifique o usuario.');
}

function report() {
  const db = load();
  const keys = args.all ? Object.keys(db.series) : [args.key].filter(Boolean);
  if (!keys.length) {
    console.error('erro: use --key <chave> ou --all');
    process.exit(2);
  }
  const target = args.target != null && args.target !== true ? parseFloat(args.target) : null;
  const out = [];
  for (const k of keys) {
    const s = db.series[k];
    if (!s) { console.error(`serie "${k}" nao existe. Series: ${Object.keys(db.series).join(', ') || '(nenhuma)'}`); process.exit(1); }
    const r = summarize(s, args.all ? null : target);
    out.push(r);
    printSummary(r);
  }
  if (args.json) console.log('\n' + JSON.stringify(out, null, 2));
  // codigo 10 = algo merece alerta; util pra rotina decidir se notifica
  process.exit(out.some((r) => r.shouldAlert) ? 10 : 0);
}

if (cmd === 'record') record();
else if (cmd === 'report') report();
else {
  console.error('uso: history.mjs record --key K --price N [--currency GBP] [--label L] [--source S]');
  console.error('     history.mjs report --key K [--target N] [--json]');
  console.error('     history.mjs report --all');
  process.exit(2);
}
