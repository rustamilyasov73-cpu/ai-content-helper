import partsData from '../data/parts.json';
import type { Part } from './types';

export const CATEGORY_LABELS: Record<string, string> = {
  filters: 'Фильтры',
  belts: 'Ремни',
  bearings: 'Подшипники',
  cutting: 'Режущие элементы',
  hydraulics: 'Гидравлика',
  electrics: 'Электрика',
  chains: 'Цепи',
  chassis: 'Ходовая',
  cooling: 'Охлаждение',
};

const PARTS = partsData as Part[];

function normalize(text: string): string {
  return text
    .trim()
    .toLowerCase()
    .replace(/ё/g, 'е')
    .replace(/[\s\-_/.,;:]+/g, ' ')
    .trim();
}

function compact(text: string): string {
  return normalize(text).replace(/[^a-z0-9а-я]+/g, '');
}

export function categoryLabel(category: string): string {
  return CATEGORY_LABELS[category] ?? category;
}

export function formatPrice(price: number): string {
  return `${price.toLocaleString('ru-RU')} ₽`;
}

export function allParts(): Part[] {
  return PARTS;
}

export function getPart(id: string): Part | undefined {
  return PARTS.find((p) => p.id === id);
}

export function categories(): Array<{ key: string; label: string; count: number }> {
  const counts: Record<string, number> = {};
  for (const part of PARTS) {
    counts[part.category] = (counts[part.category] ?? 0) + 1;
  }
  const ordered = Object.keys(CATEGORY_LABELS)
    .filter((key) => counts[key])
    .map((key) => ({ key, label: CATEGORY_LABELS[key], count: counts[key] }));
  for (const key of Object.keys(counts)) {
    if (!CATEGORY_LABELS[key]) {
      ordered.push({ key, label: key, count: counts[key] });
    }
  }
  return ordered;
}

export function brands(): Array<{ name: string; count: number }> {
  const counts: Record<string, number> = {};
  for (const part of PARTS) {
    counts[part.brand] = (counts[part.brand] ?? 0) + 1;
  }
  return Object.entries(counts)
    .map(([name, count]) => ({ name, count }))
    .sort((a, b) => a.name.localeCompare(b.name, 'ru'));
}

export function byCategory(category: string): Part[] {
  return PARTS.filter((p) => p.category === category);
}

export function byBrand(brand: string): Part[] {
  const needle = normalize(brand);
  return PARTS.filter((p) => normalize(p.brand) === needle);
}

export function searchParts(query: string, limit = 30): Part[] {
  const q = normalize(query);
  if (!q) return [];
  const qCompact = compact(query);

  const scored: Array<[number, Part]> = [];
  for (const part of PARTS) {
    const skuN = normalize(part.sku);
    const skuC = compact(part.sku);
    const nameN = normalize(part.name);
    const brandN = normalize(part.brand);
    const haystack = normalize(
      [part.sku, part.name, part.brand, categoryLabel(part.category), part.compatible.join(' '), part.description].join(
        ' ',
      ),
    );
    let score = 0;
    if (q === skuN || qCompact === skuC) score += 120;
    else if (skuN.includes(q) || (qCompact && skuC.includes(qCompact))) score += 100;
    else if (skuC && qCompact && (skuC.includes(qCompact) || qCompact.includes(skuC))) {
      if (Math.abs(skuC.length - qCompact.length) <= 2) score += 80;
    }
    if (nameN.includes(q)) score += 50;
    if (brandN.includes(q)) score += 30;
    for (const token of q.split(' ')) {
      if (token && haystack.includes(token)) score += 10;
      const tokenC = compact(token);
      if (tokenC && skuC.includes(tokenC)) score += 40;
    }
    if (score) scored.push([score, part]);
  }
  scored.sort((a, b) => b[0] - a[0] || a[1].name.localeCompare(b[1].name, 'ru'));
  return scored.slice(0, limit).map(([, part]) => part);
}

export function matchBySkuCandidates(candidates: string[]): Part[] {
  const found: Part[] = [];
  const seen = new Set<string>();
  for (const candidate of candidates) {
    const hits = searchParts(candidate, 3);
    for (const part of hits) {
      if (!seen.has(part.id)) {
        seen.add(part.id);
        found.push(part);
      }
    }
  }
  return found;
}
