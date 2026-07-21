import Papa from 'papaparse';
import classificationOptionsCsv from '../../imports_new/Weapons_Classifications__Small_Arms_classification_options.csv?raw';
import characteristicOptionsCsv from '../../imports_new/Weapons_Classifications__Small_Arms_characteristic_options.csv?raw';
import characteristicDefinitionsCsv from '../../imports_new/Weapons_Classifications__Small_Arms_characteristic_definitions.csv?raw';
import sourcesCsv from '../../imports_new/Weapons_Classifications__Small_Arms_sources.csv?raw';

export type CharacteristicType = 'how_held' | 'bore_type' | 'loading' | 'method_of_operation';

export const formatLabel = (s: string) => s.replace(/_/g, ' ');

export interface CharacteristicOption {
  id: string;
  name: string;
  guidance: string;
  pdfPages?: number[];      // offset-adjusted, for PDF navigation
  rawPdfPages?: number[];   // original page numbers from the sheet, for display
  imagePage?: number;
}

export interface Characteristic {
  id: CharacteristicType;
  name: string;
  description: string;
  options: CharacteristicOption[];
}

export interface WeaponClassification {
  id: string;
  name: string;
  description: string;
  group: string;
  type: string;
  subType?: string;
  pdfPages?: number[];      // offset-adjusted, for PDF navigation
  rawPdfPages?: number[];   // original page numbers from the sheet, for display
  imagePage?: number;
  imageUrl?: string;
  characteristics: {
    'how_held'?: string;
    'bore_type'?: string;
    'loading'?: string;
    'method_of_operation'?: string;
  };
}

// --- Parse source offsets from sources.csv ---
// Offset = how much to add to a page number from the sheet to get the correct PDF viewer page.
const sourceOffsets: Record<string, number> = {};
const sourcePdfUrls: Record<string, string> = {};
const sourcesResult = Papa.parse<Record<string, string>>(sourcesCsv, { header: true, skipEmptyLines: true, transformHeader: (h) => h.trim() });
const offsetColumn = Object.keys(sourcesResult.data[0] ?? {}).find(k => k.toLowerCase().startsWith('offset'));
for (const row of sourcesResult.data) {
  const id = (row['source_id'] ?? '').trim();
  if (!id) continue;
  const offset = offsetColumn ? parseInt(row[offsetColumn] ?? '0', 10) : 0;
  sourceOffsets[id] = isNaN(offset) ? 0 : offset;
  // Strip URL fragment so PdfViewer can append its own #page=
  const url = (row['source_url'] ?? '').trim();
  sourcePdfUrls[id] = url.includes('#') ? url.substring(0, url.indexOf('#')) : url;
}

export const PDF_URL = sourcePdfUrls['ares_guide'] ?? '';

function getOffset(sourceId: string | undefined): number {
  return sourceOffsets[(sourceId ?? '').trim()] ?? 0;
}

// Parse space-separated page numbers, adding source offset to each
function parsePages(pageStr: string | undefined, offset: number): number[] | undefined {
  if (!pageStr || pageStr.trim() === '' || pageStr.trim() === 'NA') return undefined;
  const pages = pageStr.trim().split(/\s+/).map(p => parseInt(p) + offset).filter(n => !isNaN(n));
  return pages.length > 0 ? pages : undefined;
}

function parseSinglePage(pageStr: string | undefined, offset: number): number | undefined {
  return parsePages(pageStr, offset)?.[0];
}

// Map CSV characteristic column values to CharacteristicType IDs.
// characteristic_definitions.csv uses 'action_mechanism'; options + classifications use 'method_of_operation'.
const CHAR_ID_MAP: Record<string, CharacteristicType> = {
  'how_held': 'how_held',
  'bore_type': 'bore_type',
  'loading': 'loading',
  'method_of_operation': 'method_of_operation',
  'action_mechanism': 'method_of_operation',
};

const CHARACTERISTIC_ORDER: CharacteristicType[] = [
  'how_held',
  'bore_type',
  'loading',
  'method_of_operation',
];

const CHARACTERISTIC_DISPLAY_NAMES: Record<CharacteristicType, string> = {
  'how_held': 'How Held (Grip/Bracing)',
  'bore_type': 'Bore Type',
  'loading': 'Loading Mechanism',
  'method_of_operation': 'Method of Operation',
};

// --- Parse characteristic descriptions from characteristic_definitions.csv ---
const charDescriptions: Partial<Record<CharacteristicType, string>> = {};
const definitionsResult = Papa.parse<Record<string, string>>(characteristicDefinitionsCsv, {
  header: true,
  skipEmptyLines: true,
  transformHeader: (h) => h.trim(),
});
for (const row of definitionsResult.data) {
  const charKey = (row['characteristic'] ?? '').trim().toLowerCase();
  const id = CHAR_ID_MAP[charKey];
  if (id) {
    charDescriptions[id] = row['guidance'] ?? '';
  }
}

// --- Parse characteristic options from characteristic_options.csv ---
const charOptions: Record<CharacteristicType, CharacteristicOption[]> = {
  'how_held': [],
  'bore_type': [],
  'loading': [],
  'method_of_operation': [],
};
const optionsResult = Papa.parse<Record<string, string>>(characteristicOptionsCsv, {
  header: true,
  skipEmptyLines: true,
  transformHeader: (h) => h.trim(),
});
for (const row of optionsResult.data) {
  const charKey = (row['characteristic'] ?? '').trim().toLowerCase();
  const id = CHAR_ID_MAP[charKey];
  if (!id) continue;

  const refSourceId = (row['reference_source_id'] ?? '').trim();
  const imgSourceId = (row['image_source'] ?? '').trim();
  const refOffset = getOffset(refSourceId);
  const imgOffset = getOffset(imgSourceId);

  const pdfPages = parsePages(row['source_reference_page_number'], refOffset);
  const rawPdfPages = parsePages(row['source_reference_page_number'], 0);
  const imagePage = parseSinglePage(row['source_image_page_number'], imgOffset) ?? pdfPages?.[0];

  charOptions[id].push({
    id: (row['option'] ?? '').trim().toLowerCase(),
    name: formatLabel(row['option'] ?? ''),
    guidance: row['description'] ?? '',
    pdfPages,
    rawPdfPages,
    imagePage,
  });
}

// --- Build CHARACTERISTICS in fixed display order ---
export const CHARACTERISTICS: Characteristic[] = CHARACTERISTIC_ORDER.map(id => ({
  id,
  name: CHARACTERISTIC_DISPLAY_NAMES[id],
  description: charDescriptions[id] ?? '',
  options: charOptions[id],
}));

// --- Parse weapon classifications from classification_options.csv ---
const classResult = Papa.parse<Record<string, string>>(classificationOptionsCsv, {
  header: true,
  skipEmptyLines: true,
  transformHeader: (h) => h.trim(),
});

export const WEAPON_CLASSIFICATIONS: WeaponClassification[] = classResult.data.map(row => {
  const refSourceId = (row['reference_source_id'] ?? '').trim();
  const imgSourceId = (row['image_source'] ?? '').trim();
  const pdfPages = parsePages(row['source_reference_page_number'], getOffset(refSourceId));
  const rawPdfPages = parsePages(row['source_reference_page_number'], 0);
  const imagePage = parseSinglePage(row['source_image_page_number'], getOffset(imgSourceId));

  const parseCharValue = (v: string | undefined) => { const s = (v ?? '').trim().toLowerCase(); return s && s !== 'none' ? s : undefined; };
  const held = parseCharValue(row['how_held']);
  const bore = parseCharValue(row['bore_type']);
  const loading = parseCharValue(row['loading']);
  const method = parseCharValue(row['method_of_operation']);

  return {
    id: row['id'] ?? '',
    name: row['name'] ?? '',
    description: (row['description'] ?? '').trim(),
    group: row['group'] ?? '',
    type: row['type'] ?? '',
    subType: (row['sub_type'] ?? '').trim() || undefined,
    pdfPages,
    rawPdfPages,
    imagePage,
    characteristics: {
      ...(held ? { 'how_held': held } : {}),
      ...(bore ? { 'bore_type': bore } : {}),
      ...(loading ? { 'loading': loading } : {}),
      ...(method ? { 'method_of_operation': method } : {}),
    },
  };
});
