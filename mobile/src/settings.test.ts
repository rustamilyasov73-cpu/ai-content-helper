import assert from 'node:assert/strict';
import { isLikelyOpenAiKey, maskOpenAiKey, normalizeOpenAiKey } from './openaiKey';

assert.equal(normalizeOpenAiKey('  sk-test 123  '), 'sk-test123');
assert.equal(normalizeOpenAiKey('"sk-abc"'), 'sk-abc');
assert.ok(isLikelyOpenAiKey('sk-' + 'x'.repeat(20)));
assert.equal(isLikelyOpenAiKey('not-a-key'), false);
assert.ok(maskOpenAiKey('sk-abcdefghijklmnop').includes('…'));

console.log('openai key helpers ok');
