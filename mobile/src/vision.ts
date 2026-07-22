import type { PhotoRecognition } from './types';
import { VISION_MODEL } from './version';

const SKU_PATTERN =
  /(?<![A-Z0-9])([A-Z]{1,4}[-_ ]?\d{4,10}|\d+(?:\.\d+){1,4}|[A-Z]{2,}\d{3,}[A-Z0-9]*|\d{6,12})(?![A-Z0-9])/gi;

const VISION_PROMPT = `Ты OCR-помощник магазина запчастей AgroParts.
На фото бирка, шильдик, узел, упаковка или этикетка сельхозтехники.
Извлеки ВСЕ читаемые артикулы/part number/OEM/номера деталей, бренд и полезный текст.

Верни ТОЛЬКО JSON без markdown:
{
  "raw_text": "весь распознанный текст кратко",
  "candidates": ["артикул1", "артикул2"],
  "brand": "бренд или пусто",
  "model": "модель техники или пусто",
  "notes": "что видно на фото одним предложением"
}

Правила:
- candidates — только коды деталей (не даты, не серийники машины целиком, если есть явный Part No)
- сохраняй буквы/цифры как на бирке, можно без лишних пробелов
- если ничего не читается — candidates: []`;

export function extractSkuCandidates(text: string): string[] {
  const found: string[] = [];
  const seen = new Set<string>();
  const matches = text.matchAll(SKU_PATTERN);
  for (const match of matches) {
    const token = match[1].replace(/\s+/g, '').toUpperCase();
    const key = token.replace(/[^A-Z0-9]/g, '');
    if (key.length < 5 || seen.has(key)) continue;
    seen.add(key);
    found.push(token);
  }
  return found;
}

function parseVisionJson(content: string): PhotoRecognition {
  let text = (content || '').trim();
  if (text.startsWith('```')) {
    text = text.replace(/^```(?:json)?\s*/i, '').replace(/\s*```$/, '');
  }
  try {
    const data = JSON.parse(text) as {
      raw_text?: string;
      candidates?: string[];
      brand?: string;
      model?: string;
      notes?: string;
    };
    const candidates = (data.candidates ?? []).map((c) => String(c).trim()).filter(Boolean);
    const rawText = String(data.raw_text ?? '');
    for (const extra of extractSkuCandidates(`${rawText} ${candidates.join(' ')}`)) {
      if (!candidates.includes(extra)) candidates.push(extra);
    }
    return {
      rawText,
      candidates,
      brand: String(data.brand ?? ''),
      model: String(data.model ?? ''),
      notes: String(data.notes ?? ''),
    };
  } catch {
    return {
      rawText: text.slice(0, 1000),
      candidates: extractSkuCandidates(text),
      brand: '',
      model: '',
      notes: 'Распознан текст без строгого JSON',
    };
  }
}

export async function recognizePartPhoto(
  base64Image: string,
  mimeType: string,
  apiKey: string,
  model = VISION_MODEL,
): Promise<PhotoRecognition> {
  if (!apiKey.trim()) {
    return {
      rawText: '',
      candidates: [],
      brand: '',
      model: '',
      notes: '',
      error: 'Укажите OpenAI API ключ в Настройках',
    };
  }

  try {
    const response = await fetch('https://api.openai.com/v1/chat/completions', {
      method: 'POST',
      headers: {
        Authorization: `Bearer ${apiKey.trim()}`,
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        model,
        temperature: 0,
        messages: [
          {
            role: 'user',
            content: [
              { type: 'text', text: VISION_PROMPT },
              {
                type: 'image_url',
                image_url: {
                  url: `data:${mimeType};base64,${base64Image}`,
                },
              },
            ],
          },
        ],
      }),
    });

    if (!response.ok) {
      const errText = await response.text();
      return {
        rawText: '',
        candidates: [],
        brand: '',
        model: '',
        notes: '',
        error: `Ошибка API (${response.status}): ${errText.slice(0, 200)}`,
      };
    }

    const json = (await response.json()) as {
      choices?: Array<{ message?: { content?: string } }>;
    };
    const content = json.choices?.[0]?.message?.content ?? '';
    return parseVisionJson(content);
  } catch (e) {
    return {
      rawText: '',
      candidates: [],
      brand: '',
      model: '',
      notes: '',
      error: e instanceof Error ? e.message : 'Не удалось распознать фото',
    };
  }
}
