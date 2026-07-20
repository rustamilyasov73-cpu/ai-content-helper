import assert from 'node:assert/strict';
import { matchBySkuCandidates, searchParts } from './catalog';
import { extractSkuCandidates } from './vision';

assert.equal(searchParts('RE507922')[0]?.sku, 'RE507922');
assert.ok(searchParts('фильтр John Deere').length >= 1);
assert.ok(matchBySkuCandidates(['RE507922', 'AL156625']).length >= 2);

const fromOcr = extractSkuCandidates('Part No RE507922 John Deere Oil Filter');
assert.ok(fromOcr.includes('RE507922'));

console.log('catalog/vision tests ok');
