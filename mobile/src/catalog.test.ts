import assert from 'node:assert/strict';
import { allParts, matchBySkuCandidates, replaceParts, searchParts } from './catalog';
import { extractSkuCandidates } from './vision';

assert.equal(searchParts('RE507922')[0]?.sku, 'RE507922');
assert.ok(searchParts('фильтр John Deere').length >= 1);
assert.ok(matchBySkuCandidates(['RE507922', 'AL156625']).length >= 2);

const fromOcr = extractSkuCandidates('Part No RE507922 John Deere Oil Filter');
assert.ok(fromOcr.includes('RE507922'));

const before = allParts().length;
replaceParts([
  {
    id: 'tmp1',
    sku: 'TMP-1',
    name: 'Тест',
    category: 'filters',
    brand: 'Test',
    compatible: ['A'],
    price: 1,
    stock: 1,
    unit: 'шт',
    description: 't',
  },
]);
assert.equal(allParts().length, 1);
assert.equal(searchParts('TMP-1')[0]?.sku, 'TMP-1');
// восстановим исходный каталог из data через повторный import нельзя —
// для теста достаточно проверить replaceParts; дальше тесты каталога уже прошли
assert.ok(before >= 10);

console.log('catalog/vision tests ok');
