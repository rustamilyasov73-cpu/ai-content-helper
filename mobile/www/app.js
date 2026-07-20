const CATEGORY_LABELS = {
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
}`;

const state = {
  parts: [],
  cart: loadJson('agroparts.cart', []),
  orders: loadJson('agroparts.orders', []),
  apiKey: localStorage.getItem('agroparts.openai_api_key') || '',
  apiBaseUrl: localStorage.getItem('agroparts.api_base_url') || '',
  apiToken: localStorage.getItem('agroparts.api_token') || '',
  filter: { type: 'all' },
  query: '',
  photo: {
    preview: '',
    loading: false,
    result: null,
    matches: [],
  },
  phone: '',
  comment: '',
  toast: '',
  sendingOrder: false,
};

function loadJson(key, fallback) {
  try {
    return JSON.parse(localStorage.getItem(key) || '') ?? fallback;
  } catch {
    return fallback;
  }
}

function save() {
  localStorage.setItem('agroparts.cart', JSON.stringify(state.cart));
  localStorage.setItem('agroparts.orders', JSON.stringify(state.orders));
}

function money(n) {
  return `${Number(n).toLocaleString('ru-RU')} ₽`;
}

function normalize(text) {
  return String(text || '')
    .trim()
    .toLowerCase()
    .replace(/ё/g, 'е')
    .replace(/[\s\-_/.,;:]+/g, ' ')
    .trim();
}

function compact(text) {
  return normalize(text).replace(/[^a-z0-9а-я]+/g, '');
}

function categoryLabel(c) {
  return CATEGORY_LABELS[c] || c;
}

function route() {
  const hash = location.hash.replace(/^#/, '') || '/';
  const parts = hash.split('/').filter(Boolean);
  if (!parts.length) return { name: 'catalog' };
  if (parts[0] === 'search') return { name: 'search' };
  if (parts[0] === 'photo') return { name: 'photo' };
  if (parts[0] === 'cart') return { name: 'cart' };
  if (parts[0] === 'settings') return { name: 'settings' };
  if (parts[0] === 'part' && parts[1]) return { name: 'part', id: parts[1] };
  return { name: 'catalog' };
}

function go(path) {
  location.hash = path.startsWith('#') ? path : `#${path}`;
}

function getPart(id) {
  return state.parts.find((p) => p.id === id);
}

function categories() {
  const counts = {};
  for (const p of state.parts) counts[p.category] = (counts[p.category] || 0) + 1;
  const ordered = Object.keys(CATEGORY_LABELS)
    .filter((k) => counts[k])
    .map((k) => ({ key: k, label: CATEGORY_LABELS[k], count: counts[k] }));
  for (const key of Object.keys(counts)) {
    if (!CATEGORY_LABELS[key]) {
      ordered.push({ key, label: key, count: counts[key] });
    }
  }
  return ordered;
}

function brands() {
  const counts = {};
  for (const p of state.parts) counts[p.brand] = (counts[p.brand] || 0) + 1;
  return Object.entries(counts)
    .map(([name, count]) => ({ name, count }))
    .sort((a, b) => a.name.localeCompare(b.name, 'ru'));
}

function searchParts(query, limit = 30) {
  const q = normalize(query);
  if (!q) return [];
  const qCompact = compact(query);
  const scored = [];
  for (const part of state.parts) {
    const skuN = normalize(part.sku);
    const skuC = compact(part.sku);
    const nameN = normalize(part.name);
    const brandN = normalize(part.brand);
    const haystack = normalize(
      [part.sku, part.name, part.brand, categoryLabel(part.category), ...(part.compatible || []), part.description].join(
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
  return scored.slice(0, limit).map((x) => x[1]);
}

function filteredParts() {
  if (state.filter.type === 'category') {
    return state.parts.filter((p) => p.category === state.filter.key);
  }
  if (state.filter.type === 'brand') {
    const needle = normalize(state.filter.name);
    return state.parts.filter((p) => normalize(p.brand) === needle);
  }
  return state.parts;
}

function cartQty() {
  return state.cart.reduce((s, i) => s + i.qty, 0);
}

function cartTotal() {
  return state.cart.reduce((s, i) => {
    const p = getPart(i.partId);
    return s + (p ? p.price * i.qty : 0);
  }, 0);
}

function addToCart(partId, qty = 1) {
  const part = getPart(partId);
  if (!part || part.stock <= 0) return toast('Нет в наличии');
  const existing = state.cart.find((i) => i.partId === partId);
  if (!existing) state.cart.push({ partId, qty: Math.min(qty, part.stock) });
  else existing.qty = Math.min(existing.qty + qty, part.stock);
  save();
  toast('Добавлено в корзину');
  render();
}

function setQty(partId, qty) {
  const part = getPart(partId);
  if (!part) return;
  if (qty <= 0) state.cart = state.cart.filter((i) => i.partId !== partId);
  else {
    const item = state.cart.find((i) => i.partId === partId);
    if (item) item.qty = Math.min(qty, part.stock);
  }
  save();
  render();
}

function commitLocalOrder(order) {
  state.orders = [order, ...state.orders.filter((o) => o.id !== order.id)];
  state.cart = [];
  state.phone = '';
  state.comment = '';
  save();
}

async function placeOrder() {
  if (state.sendingOrder) return;
  if (!state.cart.length) return toast('Корзина пуста');
  if (!state.phone.trim()) return toast('Укажите телефон');
  const items = state.cart
    .map((i) => {
      const p = getPart(i.partId);
      if (!p) return null;
      return { partId: p.id, sku: p.sku, name: p.name, qty: i.qty, price: p.price };
    })
    .filter(Boolean);
  const order = {
    id: `ord-${Date.now()}`,
    createdAt: new Date().toISOString(),
    phone: state.phone.trim(),
    comment: state.comment.trim(),
    items,
    total: items.reduce((s, i) => s + i.price * i.qty, 0),
  };

  const base = state.apiBaseUrl.trim().replace(/\/+$/, '');
  if (!base) {
    commitLocalOrder(order);
    toast(`Заявка ${order.id} на телефоне. Укажите URL API для 1С`);
    render();
    return;
  }

  state.sendingOrder = true;
  render();
  try {
    const headers = { 'Content-Type': 'application/json' };
    if (state.apiToken.trim()) headers['X-API-Token'] = state.apiToken.trim();
    const res = await fetch(`${base}/api/orders`, {
      method: 'POST',
      headers,
      body: JSON.stringify({
        id: order.id,
        phone: order.phone,
        comment: order.comment,
        total: order.total,
        source: 'mobile-web',
        items: order.items,
      }),
    });
    const data = await res.json().catch(() => ({}));
    if (!res.ok || data.ok === false) {
      toast(`Не отправлено, корзина сохранена: ${data.message || res.status}`);
      return;
    }
    commitLocalOrder(order);
    if (data.onec?.number) toast(`Заявка в 1С №${data.onec.number}`);
    else if (data.onec?.skipped) toast('Заявка на сервере (1С выкл.)');
    else toast(`Заявка ${order.id} отправлена`);
  } catch (e) {
    toast(`Не отправлено, корзина сохранена: ${e.message || 'ошибка'}`);
  } finally {
    state.sendingOrder = false;
    render();
  }
}

async function refreshCatalogFromApi() {
  const base = state.apiBaseUrl.trim().replace(/\/+$/, '');
  if (!base) return toast('Укажите URL API');
  try {
    const headers = {};
    if (state.apiToken.trim()) headers['X-API-Token'] = state.apiToken.trim();
    const res = await fetch(`${base}/api/parts`, { headers });
    const data = await res.json();
    if (!res.ok || !Array.isArray(data.items)) {
      return toast(data.message || `Ошибка ${res.status}`);
    }
    state.parts = data.items;
    toast(`Каталог: ${data.items.length} позиций`);
    render();
  } catch (e) {
    toast(e.message || 'Сеть недоступна');
  }
}

function toast(msg) {
  state.toast = msg;
  render();
  setTimeout(() => {
    if (state.toast === msg) {
      state.toast = '';
      render();
    }
  }, 2200);
}

function extractSkuCandidates(text) {
  const found = [];
  const seen = new Set();
  for (const match of String(text || '').matchAll(SKU_PATTERN)) {
    const token = match[1].replace(/\s+/g, '').toUpperCase();
    const key = token.replace(/[^A-Z0-9]/g, '');
    if (key.length < 5 || seen.has(key)) continue;
    seen.add(key);
    found.push(token);
  }
  return found;
}

function parseVisionJson(content) {
  let text = String(content || '').trim();
  if (text.startsWith('```')) text = text.replace(/^```(?:json)?\s*/i, '').replace(/\s*```$/, '');
  try {
    const data = JSON.parse(text);
    const candidates = (data.candidates || []).map((c) => String(c).trim()).filter(Boolean);
    const rawText = String(data.raw_text || '');
    for (const extra of extractSkuCandidates(`${rawText} ${candidates.join(' ')}`)) {
      if (!candidates.includes(extra)) candidates.push(extra);
    }
    return {
      rawText,
      candidates,
      brand: String(data.brand || ''),
      model: String(data.model || ''),
      notes: String(data.notes || ''),
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

async function recognizeImage(file) {
  if (!state.apiKey.trim()) {
    state.photo.result = { error: 'Укажите OpenAI API ключ в Настройках' };
    render();
    return;
  }
  state.photo.loading = true;
  state.photo.result = null;
  state.photo.matches = [];
  state.photo.preview = URL.createObjectURL(file);
  render();

  const base64 = await fileToBase64(file);
  const mime = file.type || 'image/jpeg';
  try {
    const response = await fetch('https://api.openai.com/v1/chat/completions', {
      method: 'POST',
      headers: {
        Authorization: `Bearer ${state.apiKey.trim()}`,
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        model: 'gpt-4o-mini',
        temperature: 0,
        messages: [
          {
            role: 'user',
            content: [
              { type: 'text', text: VISION_PROMPT },
              { type: 'image_url', image_url: { url: `data:${mime};base64,${base64}` } },
            ],
          },
        ],
      }),
    });
    if (!response.ok) {
      const err = await response.text();
      state.photo.result = { error: `Ошибка API (${response.status}): ${err.slice(0, 180)}` };
    } else {
      const json = await response.json();
      const parsed = parseVisionJson(json.choices?.[0]?.message?.content || '');
      state.photo.result = parsed;
      const matches = [];
      const seen = new Set();
      for (const c of parsed.candidates || []) {
        for (const part of searchParts(c, 3)) {
          if (!seen.has(part.id)) {
            seen.add(part.id);
            matches.push(part);
          }
        }
      }
      state.photo.matches = matches;
    }
  } catch (e) {
    state.photo.result = { error: e.message || 'Не удалось распознать' };
  }
  state.photo.loading = false;
  render();
}

function fileToBase64(file) {
  return new Promise((resolve, reject) => {
    const reader = new FileReader();
    reader.onload = () => {
      const result = String(reader.result || '');
      resolve(result.includes(',') ? result.split(',')[1] : result);
    };
    reader.onerror = reject;
    reader.readAsDataURL(file);
  });
}

function partRow(part) {
  return `
    <button class="row" type="button" data-go="#/part/${part.id}">
      <div class="sku">${escapeHtml(part.sku)}</div>
      <div class="name">${escapeHtml(part.name)}</div>
      <div class="meta">${escapeHtml(part.brand)} · ${escapeHtml(categoryLabel(part.category))}</div>
      <div class="footer">
        <span class="price">${money(part.price)}</span>
        <span class="stock ${part.stock > 0 ? 'ok' : 'bad'}">${
          part.stock > 0 ? `${part.stock} ${part.unit}` : 'нет'
        }</span>
      </div>
    </button>
  `;
}

function tabbar(active) {
  const qty = cartQty();
  const tabs = [
    ['catalog', '#/', '▦', 'Каталог'],
    ['search', '#/search', '⌕', 'Поиск'],
    ['photo', '#/photo', '📷', 'Фото'],
    ['cart', '#/cart', '🛒', 'Корзина'],
    ['settings', '#/settings', '⚙', 'Настройки'],
  ];
  return `
    <nav class="tabbar">
      ${tabs
        .map(
          ([name, href, icon, title]) => `
        <button class="tab ${active === name ? 'active' : ''}" type="button" data-go="${href}">
          <span class="icon">${icon}</span>
          <span>${title}</span>
          ${name === 'cart' && qty ? `<span class="badge">${qty}</span>` : ''}
        </button>`,
        )
        .join('')}
    </nav>
  `;
}

function renderCatalog() {
  const cats = categories();
  const brandList = brands();
  const parts = filteredParts();
  return `
    <header class="hero">
      <h1>AgroParts</h1>
      <p>Запчасти для тракторов и комбайнов</p>
    </header>
    <div class="chips">
      <button class="chip ${state.filter.type === 'all' ? 'active' : ''}" data-filter='{"type":"all"}'>Все</button>
      ${cats
        .map(
          (c) =>
            `<button class="chip ${
              state.filter.type === 'category' && state.filter.key === c.key ? 'active' : ''
            }" data-filter='${JSON.stringify({ type: 'category', key: c.key })}'>${escapeHtml(c.label)} (${c.count})</button>`,
        )
        .join('')}
      ${brandList
        .map(
          (b) =>
            `<button class="chip ${
              state.filter.type === 'brand' && state.filter.name === b.name ? 'active' : ''
            }" data-filter='${JSON.stringify({ type: 'brand', name: b.name })}'>${escapeHtml(b.name)}</button>`,
        )
        .join('')}
    </div>
    <div class="list">${parts.map(partRow).join('') || '<div class="hint">Ничего не найдено</div>'}</div>
    ${tabbar('catalog')}
  `;
}

function renderSearch() {
  const results = searchParts(state.query);
  return `
    <div class="topbar">Поиск</div>
    <div class="panel">
      <input class="input" id="searchInput" placeholder="Артикул, бренд, модель…" value="${escapeAttr(
        state.query,
      )}" />
    </div>
    ${
      !state.query.trim()
        ? '<div class="hint">Например: RE507922 или фильтр John Deere</div>'
        : `<div class="list">${results.map(partRow).join('') || '<div class="hint">Ничего не найдено</div>'}</div>`
    }
    ${tabbar('search')}
  `;
}

function renderPhoto() {
  const r = state.photo.result;
  return `
    <div class="topbar">Фото</div>
    <div class="panel">
      <h2 style="margin:0 0 6px;font-size:20px;">Снимите бирку или шильдик</h2>
      <p class="muted" style="margin:0;">Приложение распознает артикул и найдёт деталь в каталоге</p>
      ${!state.apiKey ? '<p class="warn">Сначала укажите OpenAI API ключ во вкладке Настройки</p>' : ''}
      <div class="actions">
        <label class="btn primary" style="text-align:center;">
          Камера
          <input id="cameraInput" type="file" accept="image/*" capture="environment" hidden />
        </label>
        <label class="btn secondary" style="text-align:center;">
          Галерея
          <input id="galleryInput" type="file" accept="image/*" hidden />
        </label>
      </div>
      ${state.photo.preview ? `<img class="preview" src="${state.photo.preview}" alt="preview" />` : ''}
      ${state.photo.loading ? '<p class="hint">Распознаём артикул…</p>' : ''}
      ${r?.error ? `<p class="error">${escapeHtml(r.error)}</p>` : ''}
      ${
        r && !r.error
          ? `<div class="card">
              <strong>${
                r.candidates?.length
                  ? `Найденные коды: ${escapeHtml(r.candidates.join(', '))}`
                  : 'Артикулы не распознаны'
              }</strong>
              ${r.notes ? `<div class="muted" style="margin-top:4px;">${escapeHtml(r.notes)}</div>` : ''}
            </div>`
          : ''
      }
    </div>
    ${
      state.photo.matches.length
        ? `<div class="panel"><strong>Совпадения в каталоге</strong></div><div class="list">${state.photo.matches
            .map(partRow)
            .join('')}</div>`
        : ''
    }
    ${tabbar('photo')}
  `;
}

function renderCart() {
  return `
    <div class="topbar">Корзина</div>
    ${
      !state.cart.length
        ? '<div class="hint">Корзина пуста — добавьте детали из каталога</div>'
        : state.cart
            .map((item) => {
              const part = getPart(item.partId);
              if (!part) return '';
              return `
                <div class="cart-row">
                  <button class="main row" style="border:0;padding:0;background:transparent;" data-go="#/part/${part.id}">
                    <div class="sku">${escapeHtml(part.sku)}</div>
                    <div class="name">${escapeHtml(part.name)}</div>
                    <div class="price">${money(part.price * item.qty)}</div>
                  </button>
                  <div>
                    <div class="qty">
                      <button type="button" data-qty="${part.id}:${item.qty - 1}">−</button>
                      <span>${item.qty}</span>
                      <button type="button" data-qty="${part.id}:${item.qty + 1}">+</button>
                    </div>
                    <button class="ghost" type="button" data-qty="${part.id}:0">Удалить</button>
                  </div>
                </div>`;
            })
            .join('')
    }
    <div class="panel">
      ${
        state.cart.length
          ? `
        <h2 style="margin:0 0 12px;">Итого: ${money(cartTotal())}</h2>
        <input class="input" id="phoneInput" placeholder="Телефон для связи" value="${escapeAttr(state.phone)}" />
        <div style="height:10px"></div>
        <textarea class="textarea" id="commentInput" placeholder="Комментарий (модель техники, срочность…)">${escapeHtml(
          state.comment,
        )}</textarea>
        <div style="height:12px"></div>
        <button class="btn primary" id="orderBtn" type="button">Оформить заявку</button>`
          : ''
      }
      ${
        state.orders.length
          ? `<div style="margin-top:18px;"><strong>Последние заявки</strong>${state.orders
              .slice(0, 5)
              .map(
                (o) => `<div class="card">
                  <strong>${escapeHtml(o.id)}</strong>
                  <div class="muted">${new Date(o.createdAt).toLocaleString('ru-RU')} · ${escapeHtml(o.phone)}</div>
                  <div class="muted">${o.items.length} поз. · ${money(o.total)}</div>
                </div>`,
              )
              .join('')}</div>`
          : ''
      }
    </div>
    ${tabbar('cart')}
  `;
}

function renderSettings() {
  return `
    <div class="topbar">Настройки</div>
    <div class="panel">
      <h2 style="margin:0 0 8px;font-size:22px;">AgroParts</h2>
      <p class="muted">Локальный каталог: ${state.parts.length} поз. Обновите с сервера после синхронизации 1С.</p>
      <label style="display:block;margin:12px 0 6px;font-weight:600;">URL API (1С через AgroParts)</label>
      <input class="input" id="apiUrlInput" type="url" placeholder="http://192.168.1.10:8080" value="${escapeAttr(state.apiBaseUrl)}" />
      <label style="display:block;margin:12px 0 6px;font-weight:600;">API Token</label>
      <input class="input" id="apiTokenInput" type="password" placeholder="необязательно" value="${escapeAttr(state.apiToken)}" />
      <label style="display:block;margin:12px 0 6px;font-weight:600;">OpenAI API Key</label>
      <input class="input" id="apiKeyInput" type="password" placeholder="sk-..." value="${escapeAttr(state.apiKey)}" />
      <div style="height:12px"></div>
      <button class="btn primary" id="saveKeyBtn" type="button">Сохранить</button>
      <div style="height:10px"></div>
      <button class="btn" id="syncCatalogBtn" type="button">Обновить каталог с сервера</button>
    </div>
    ${tabbar('settings')}
  `;
}

function renderPart(id) {
  const part = getPart(id);
  if (!part) {
    return `<div class="topbar"><button class="back" data-go="#/">←</button>Деталь</div><div class="hint">Деталь не найдена</div>${tabbar('catalog')}`;
  }
  return `
    <div class="topbar"><button class="back" data-go="#/">←</button>${escapeHtml(part.sku)}</div>
    <div class="panel detail">
      <div class="sku">${escapeHtml(part.sku)}</div>
      <h2>${escapeHtml(part.name)}</h2>
      <div class="muted">${escapeHtml(part.brand)} · ${escapeHtml(categoryLabel(part.category))}</div>
      <div class="price" style="font-size:24px;margin-top:10px;">${money(part.price)} / ${escapeHtml(part.unit)}</div>
      <div class="stock ${part.stock > 0 ? 'ok' : 'bad'}" style="margin-top:6px;">
        ${part.stock > 0 ? `В наличии: ${part.stock} ${part.unit}` : 'Нет в наличии'}
      </div>
      <div class="label">Совместимость</div>
      <div>${escapeHtml((part.compatible || []).join(', '))}</div>
      <div class="label">Описание</div>
      <div>${escapeHtml(part.description || '')}</div>
      <div style="height:16px"></div>
      <button class="btn primary" id="addBtn" type="button" data-add="${part.id}" ${
        part.stock <= 0 ? 'disabled style="opacity:.45"' : ''
      }>В корзину</button>
    </div>
    ${tabbar('catalog')}
  `;
}

function escapeHtml(s) {
  return String(s || '')
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;');
}

function escapeAttr(s) {
  return escapeHtml(s).replace(/'/g, '&#39;');
}

function render() {
  const app = document.getElementById('app');
  const r = route();
  let html = '';
  if (r.name === 'search') html = renderSearch();
  else if (r.name === 'photo') html = renderPhoto();
  else if (r.name === 'cart') html = renderCart();
  else if (r.name === 'settings') html = renderSettings();
  else if (r.name === 'part') html = renderPart(r.id);
  else html = renderCatalog();
  if (state.toast) html += `<div class="toast">${escapeHtml(state.toast)}</div>`;
  app.innerHTML = html;
  bind();
}

function bind() {
  document.querySelectorAll('[data-go]').forEach((el) => {
    el.addEventListener('click', (e) => {
      e.preventDefault();
      go(el.getAttribute('data-go'));
    });
  });
  document.querySelectorAll('[data-filter]').forEach((el) => {
    el.addEventListener('click', () => {
      state.filter = JSON.parse(el.getAttribute('data-filter'));
      render();
    });
  });
  const searchInput = document.getElementById('searchInput');
  if (searchInput) {
    searchInput.addEventListener('input', (e) => {
      state.query = e.target.value;
      render();
      const again = document.getElementById('searchInput');
      if (again) {
        again.focus();
        again.setSelectionRange(state.query.length, state.query.length);
      }
    });
  }
  document.querySelectorAll('[data-qty]').forEach((el) => {
    el.addEventListener('click', () => {
      const [id, qty] = el.getAttribute('data-qty').split(':');
      setQty(id, Number(qty));
    });
  });
  document.querySelectorAll('[data-add]').forEach((el) => {
    el.addEventListener('click', () => addToCart(el.getAttribute('data-add')));
  });
  const phoneInput = document.getElementById('phoneInput');
  if (phoneInput) phoneInput.addEventListener('input', (e) => (state.phone = e.target.value));
  const commentInput = document.getElementById('commentInput');
  if (commentInput) commentInput.addEventListener('input', (e) => (state.comment = e.target.value));
  const orderBtn = document.getElementById('orderBtn');
  if (orderBtn) orderBtn.addEventListener('click', () => void placeOrder());
  const apiKeyInput = document.getElementById('apiKeyInput');
  const apiUrlInput = document.getElementById('apiUrlInput');
  const apiTokenInput = document.getElementById('apiTokenInput');
  const saveKeyBtn = document.getElementById('saveKeyBtn');
  if (saveKeyBtn) {
    saveKeyBtn.addEventListener('click', () => {
      if (apiKeyInput) {
        state.apiKey = apiKeyInput.value.trim();
        localStorage.setItem('agroparts.openai_api_key', state.apiKey);
      }
      if (apiUrlInput) {
        state.apiBaseUrl = apiUrlInput.value.trim().replace(/\/+$/, '');
        localStorage.setItem('agroparts.api_base_url', state.apiBaseUrl);
      }
      if (apiTokenInput) {
        state.apiToken = apiTokenInput.value.trim();
        localStorage.setItem('agroparts.api_token', state.apiToken);
      }
      toast('Настройки сохранены');
    });
  }
  const syncCatalogBtn = document.getElementById('syncCatalogBtn');
  if (syncCatalogBtn) {
    syncCatalogBtn.addEventListener('click', () => {
      if (apiUrlInput) {
        state.apiBaseUrl = apiUrlInput.value.trim().replace(/\/+$/, '');
        localStorage.setItem('agroparts.api_base_url', state.apiBaseUrl);
      }
      if (apiTokenInput) {
        state.apiToken = apiTokenInput.value.trim();
        localStorage.setItem('agroparts.api_token', state.apiToken);
      }
      void refreshCatalogFromApi();
    });
  }
  const cameraInput = document.getElementById('cameraInput');
  const galleryInput = document.getElementById('galleryInput');
  if (cameraInput) cameraInput.addEventListener('change', () => {
    if (cameraInput.files?.[0]) recognizeImage(cameraInput.files[0]);
  });
  if (galleryInput) galleryInput.addEventListener('change', () => {
    if (galleryInput.files?.[0]) recognizeImage(galleryInput.files[0]);
  });
}

async function boot() {
  const res = await fetch('./parts.json');
  state.parts = await res.json();
  window.addEventListener('hashchange', render);
  if (!location.hash) location.hash = '#/';
  render();
}

boot().catch((e) => {
  document.getElementById('app').innerHTML = `<div class="hint">Ошибка загрузки: ${escapeHtml(e.message)}</div>`;
});
