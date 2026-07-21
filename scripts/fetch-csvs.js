// Fetches the latest CSV data from the public Google Sheet and writes
// each tab to src/imports_new/. Run with: npm run fetch-data
// Requires Node 18+ (uses built-in fetch).
//
// Uses gviz/tq to select tabs by name (export?sheet= ignores the param and
// always returns the first tab). gviz/tq quotes every field, so we
// parse and re-serialize with PapaParse to produce clean output.

import { writeFileSync } from 'fs';
import { join, dirname } from 'path';
import { fileURLToPath } from 'url';
import Papa from 'papaparse';

const __dirname = dirname(fileURLToPath(import.meta.url));

const SHEET_ID = '1owsUDceWy-sG258SE8Z-gwTDLOQwIqAr6ADdfOln-2E';
const IMPORTS_DIR = join(__dirname, '..', 'src', 'imports_new');

const SHEETS = [
  {
    tab: 'classification_options',
    filename: 'Weapons_Classifications__Small_Arms_classification_options.csv',
  },
  {
    tab: 'classification_definitions',
    filename: 'Weapons_Classifications__Small_Arms_classification_definitions.csv',
  },
  {
    tab: 'characteristic_definitions',
    filename: 'Weapons_Classifications__Small_Arms_characteristic_definitions.csv',
  },
  {
    tab: 'characteristic_options',
    filename: 'Weapons_Classifications__Small_Arms_characteristic_options.csv',
  },
  {
    tab: 'sources',
    filename: 'Weapons_Classifications__Small_Arms_sources.csv',
  },
];

async function fetchSheet({ tab, filename }) {
  const url = `https://docs.google.com/spreadsheets/d/${SHEET_ID}/gviz/tq?tqx=out:csv&sheet=${encodeURIComponent(tab)}`;
  const res = await fetch(url);
  if (!res.ok) throw new Error(`Failed to fetch tab "${tab}": ${res.status} ${res.statusText}`);
  const rawCsv = await res.text();

  // gviz/tq quotes every field. Parse then re-serialize to produce clean CSV
  // that matches what a manual Google Sheets download produces.
  const { data, meta } = Papa.parse(rawCsv, { header: true, skipEmptyLines: true });
  const cleanCsv = Papa.unparse(data, { columns: meta.fields });

  const dest = join(IMPORTS_DIR, filename);
  writeFileSync(dest, cleanCsv, 'utf8');
  console.log(`  wrote ${filename}`);
}

console.log('Fetching CSVs from Google Sheets...');
for (const sheet of SHEETS) {
  await fetchSheet(sheet);
}
console.log('Done.');
