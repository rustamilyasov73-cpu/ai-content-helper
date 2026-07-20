import type { Order } from './types';

export type SubmitOrderResult = {
  ok: boolean;
  order_id?: string;
  message?: string;
  onec?: {
    ok: boolean;
    skipped?: boolean;
    number?: string;
    message?: string;
  };
};

function normalizeBase(url: string): string {
  return url.trim().replace(/\/+$/, '');
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

  const headers: Record<string, string> = {
    'Content-Type': 'application/json',
  };
  if (apiToken.trim()) {
    headers['X-API-Token'] = apiToken.trim();
  }

  const response = await fetch(`${base}/api/orders`, {
    method: 'POST',
    headers,
    body: JSON.stringify({
      id: order.id,
      phone: order.phone,
      comment: order.comment,
      total: order.total,
      source: 'mobile',
      items: order.items,
    }),
  });

  let data: SubmitOrderResult & { message?: string };
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
