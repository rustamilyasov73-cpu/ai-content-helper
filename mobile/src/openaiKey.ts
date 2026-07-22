export function normalizeOpenAiKey(raw: string): string {
  return String(raw || '')
    .trim()
    .replace(/^["']+|["']+$/g, '')
    .replace(/\s+/g, '');
}

export function isLikelyOpenAiKey(raw: string): boolean {
  const key = normalizeOpenAiKey(raw);
  return key.startsWith('sk-') && key.length >= 20;
}

export function maskOpenAiKey(raw: string): string {
  const key = normalizeOpenAiKey(raw);
  if (!key) return '';
  if (key.length <= 12) return '••••••••';
  return `${key.slice(0, 7)}…${key.slice(-4)}`;
}
