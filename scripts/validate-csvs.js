// Validates CSV files in src/imports_new/ against expected structure and cross-references.
// Run with: npm run validate-data
// Exits with code 1 if any errors are found; warnings are non-fatal.

import { readFileSync } from 'fs';
import { join, dirname } from 'path';
import { fileURLToPath } from 'url';
import Papa from 'papaparse';

const __dirname = dirname(fileURLToPath(import.meta.url));
const IMPORTS_DIR = join(__dirname, '..', 'src', 'imports_new');

function readCsv(filename) {
  const content = readFileSync(join(IMPORTS_DIR, filename), 'utf8');
  const result = Papa.parse(content, {
    header: true,
    skipEmptyLines: true,
    transformHeader: (h) => h.trim(),
  });
  return result.data;
}

// errors/warnings keyed by file for grouped output
const errors   = {}; // { filename: string[] }
const warnings = {};
const error = (file, msg) => { (errors[file]   ??= []).push(msg); };
const warn  = (file, msg) => { (warnings[file] ??= []).push(msg); };

function printGrouped(label, groups, log) {
  const files = Object.keys(groups);
  if (!files.length) return;
  log(`${label}:`);
  for (const file of files) {
    log(`\n  ${file}.csv`);
    for (const msg of groups[file]) log(`    - ${msg}`);
  }
  log('');
}

// ---------------------------------------------------------------------------
// Load
// ---------------------------------------------------------------------------
const sources               = readCsv('Weapons_Classifications__Small_Arms_sources.csv');
const charOptions           = readCsv('Weapons_Classifications__Small_Arms_characteristic_options.csv');
const charDefinitions       = readCsv('Weapons_Classifications__Small_Arms_characteristic_definitions.csv');
const classOptions          = readCsv('Weapons_Classifications__Small_Arms_classification_options.csv');
const classDefinitions      = readCsv('Weapons_Classifications__Small_Arms_classification_definitions.csv');

// ---------------------------------------------------------------------------
// sources.csv
// ---------------------------------------------------------------------------
const validSourceIds = new Set();
for (const row of sources) {
  const id = row['source_id']?.trim();
  if (!id) { error('sources', `row missing source_id: ${JSON.stringify(row)}`); continue; }
  validSourceIds.add(id);
  if (!row['source_url']?.trim()) warn('sources', `"${id}" has no source_url`);
}

function checkSourceRefs(file, row, context) {
  const ref = row['reference_source_id']?.trim();
  const img = row['image_source']?.trim();
  if (ref && !validSourceIds.has(ref)) error(file, `${context}: unknown reference_source_id "${ref}"`);
  if (img && !validSourceIds.has(img)) error(file, `${context}: unknown image_source "${img}"`);
}

// ---------------------------------------------------------------------------
// characteristic_options.csv
// ---------------------------------------------------------------------------
// Maps characteristic name → Set of valid option IDs (lowercase)
const CHAR_ID_ALIASES = { 'action_mechanism': 'method_of_operation' };
const optionsByChar = {}; // e.g. { how_held: Set { 'one_hand', ... }, ... }

for (const row of charOptions) {
  const rawChar = row['characteristic']?.trim().toLowerCase();
  const char    = CHAR_ID_ALIASES[rawChar] ?? rawChar;
  const option  = row['option']?.trim();

  if (!char)   { error('characteristic_options', `missing characteristic in row: ${JSON.stringify(row)}`); continue; }
  if (!option) { error('characteristic_options', `characteristic "${char}" has a row with no option value`); continue; }
  if (!row['description']?.trim()) warn('characteristic_options', `"${char}/${option}" has no description`);

  if (!optionsByChar[char]) optionsByChar[char] = new Set();
  optionsByChar[char].add(option.toLowerCase());

  checkSourceRefs('characteristic_options', row, `${char}/${option}`);
}

// ---------------------------------------------------------------------------
// characteristic_definitions.csv
// ---------------------------------------------------------------------------
const definedChars = new Set();
for (const row of charDefinitions) {
  const rawChar = row['characteristic']?.trim().toLowerCase();
  const char    = CHAR_ID_ALIASES[rawChar] ?? rawChar;
  if (!char) { error('characteristic_definitions', `missing characteristic in row: ${JSON.stringify(row)}`); continue; }
  if (!row['guidance']?.trim()) warn('characteristic_definitions', `"${char}" has no guidance text`);
  definedChars.add(char);
  checkSourceRefs('characteristic_definitions', row, char);
}

// Every characteristic that has options should also have a definition
for (const char of Object.keys(optionsByChar)) {
  if (!definedChars.has(char)) {
    warn('characteristic_definitions', `"${char}" has options defined but no guidance entry`);
  }
}

// ---------------------------------------------------------------------------
// classification_options.csv
// ---------------------------------------------------------------------------
const CHAR_COLUMNS = ['how_held', 'bore_type', 'loading', 'method_of_operation'];
const classIds = new Set();

for (const row of classOptions) {
  const id   = row['id']?.trim();
  const name = row['name']?.trim();
  if (!id)   { error('classification_options', `row missing id: ${JSON.stringify(row)}`); continue; }
  if (!name) error('classification_options', `id="${id}" has no name`);
  if (classIds.has(id)) error('classification_options', `duplicate id "${id}"`);
  classIds.add(id);

  if (!row['group']?.trim()) warn('classification_options', `id="${id}" has no group`);
  if (!row['type']?.trim())  warn('classification_options', `id="${id}" has no type`);

  // Cross-reference each characteristic value against defined options
  for (const char of CHAR_COLUMNS) {
    const val = row[char]?.trim().toLowerCase();
    if (!val || val === 'none') continue;
    const validOptions = optionsByChar[char];
    if (!validOptions) {
      warn('classification_options', `id="${id}": characteristic "${char}" has no options defined in characteristic_options.csv`);
    } else if (!validOptions.has(val)) {
      error('classification_options', `id="${id}": ${char}="${val}" is not a defined option (valid: ${[...validOptions].join(', ')})`);
    }
  }

  checkSourceRefs('classification_options', row, `id="${id}"`);
}

// ---------------------------------------------------------------------------
// classification_definitions.csv
// ---------------------------------------------------------------------------
const VALID_LEVELS = new Set(['class', 'group', 'type', 'sub_type']);
for (const row of classDefinitions) {
  const level = row['level']?.trim().toLowerCase();
  const term  = row['term']?.trim();
  if (!level)  { error('classification_definitions', `row missing level: ${JSON.stringify(row)}`); continue; }
  if (!term)   { error('classification_definitions', `level="${level}" row missing term`); continue; }
  if (!VALID_LEVELS.has(level)) warn('classification_definitions', `unknown level "${level}" for term="${term}"`);
  if (!row['definition']?.trim()) warn('classification_definitions', `"${level}/${term}" has no definition`);
  checkSourceRefs('classification_definitions', row, `${level}/${term}`);
}

// ---------------------------------------------------------------------------
// Report
// ---------------------------------------------------------------------------
const totalErrors   = Object.values(errors).reduce((n, v) => n + v.length, 0);
const totalWarnings = Object.values(warnings).reduce((n, v) => n + v.length, 0);

console.log('\nValidating src/imports_new/ CSVs...\n');

printGrouped('Warnings', warnings, console.warn);
printGrouped('Errors',   errors,   console.error);

if (totalErrors) {
  console.error(`Validation FAILED — ${totalErrors} error(s), ${totalWarnings} warning(s)\n`);
  process.exit(1);
} else {
  console.log(`Validation PASSED — 0 errors, ${totalWarnings} warning(s)\n`);
}
