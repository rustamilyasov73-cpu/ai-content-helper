import type { Order, Part } from './types';
import { replaceParts } from './catalog';

export type SubmitOrderResult = {
  ok: boolean;
  order_id?: string;
  message?: string;
  duplicate?: boolean;
  onec?: {
    ok: boolean;
    skipped?: boolean;
    number?: string;
    message?: string;
  };
};

export type FetchPartsResult = {
  ok: boolean;
  count?: number;
  message?: string;
};

function normalizeBase(url: string): string {
  return url.trim().replace(/\/+$/, '');
}

function authHeaders(apiToken = ''): Record<string, string> {
  const headers: Record<string, string> = {
    'Content-Type': 'application/json',
  };
  if (apiToken.trim()) {
    headers['X-API-Token'] = apiToken.trim();
  }
  return headers;
}

export async function submitOrderToApi(
  apiBaseUrl: string,
  order: Order,
  apiToken = '',
): Promise<SubmitOrderResult> {
  const base = normalizeBase(apiBaseUrl);
  if (!base) {
    return { ok: false, message: 'Не указан URL API' };
  }

  const response = await fetch(`${base}/api/orders`, {
    method: 'POST',
    headers: authHeaders(apiToken),
    body: JSON.stringify({
      id: order.id,
      phone: order.phone,
      comment: order.comment,
      total: order.total,
      source: 'mobile',
      items: order.items,
    }),
  });

  let data: SubmitOrderResult;
  try {
    data = (await response.json()) as SubmitOrderResult;
  } catch {
    return { ok: false, message: `HTTP ${response.status}` };
  }

  if (!response.ok) {
    return {
      ok: false,
      message: data.message || `HTTP ${response.status}`,
      onec: data.onec,
    };
  }
  return data;
}

export async function refreshCatalogFromApi(
  apiBaseUrl: string,
  apiToken = '',
): Promise<FetchPartsResult> {
  const base = normalizeBase(apiBaseUrl);
  if (!base) {
    return { ok: false, message: 'Не указан URL API' };
  }

  const response = await fetch(`${base}/api/parts`, {
    method: 'GET',
    headers: authHeaders(apiToken),
  });

  let data: { ok?: boolean; count?: number; items?: Part[]; message?: string };
  try {
    data = (await response.json()) as typeof data;
  } catch {
    return { ok: false, message: `HTTP ${response.status}` };
  }

  if (!response.ok || !Array.isArray(data.items)) {
    return { ok: false, message: data.message || `HTTP ${response.status}` };
  }

  replaceParts(data.items);
  return { ok: true, count: data.items.length };
}
