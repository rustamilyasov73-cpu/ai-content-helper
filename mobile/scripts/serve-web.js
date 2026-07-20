#!/usr/bin/env node
/**
 * Static host for AgroParts www + proxy /api -> API :8100
 */
const http = require('http');
const fs = require('fs');
const path = require('path');
const { URL } = require('url');

const ROOT = process.env.WEB_ROOT || path.join(__dirname, '..', 'www');
const PORT = Number(process.env.PORT || 8090);
const API_PORT = Number(process.env.API_PORT || 8100);

const MIME = {
  '.html': 'text/html; charset=utf-8',
  '.js': 'application/javascript; charset=utf-8',
  '.css': 'text/css; charset=utf-8',
  '.json': 'application/json; charset=utf-8',
  '.png': 'image/png',
  '.jpg': 'image/jpeg',
  '.jpeg': 'image/jpeg',
  '.svg': 'image/svg+xml',
  '.ico': 'image/x-icon',
  '.woff': 'font/woff',
  '.woff2': 'font/woff2',
  '.ttf': 'font/ttf',
  '.map': 'application/json',
};

function send(res, status, body, headers = {}) {
  res.writeHead(status, headers);
  res.end(body);
}

function safeJoin(root, reqPath) {
  const decoded = decodeURIComponent(reqPath.split('?')[0]);
  const full = path.normalize(path.join(root, decoded));
  if (!full.startsWith(path.normalize(root + path.sep)) && full !== path.normalize(root)) return null;
  return full;
}

function resolveFile(urlPath) {
  const clean = (urlPath.replace(/\/+$/, '') || '/').split('?')[0];
  if (clean === '/' || clean === '/index') return path.join(ROOT, 'index.html');

  let candidate = safeJoin(ROOT, clean);
  if (!candidate) return null;
  if (fs.existsSync(candidate) && fs.statSync(candidate).isFile()) return candidate;
  if (fs.existsSync(candidate + '.html')) return candidate + '.html';
  if (fs.existsSync(path.join(candidate, 'index.html'))) return path.join(candidate, 'index.html');
  return path.join(ROOT, 'index.html');
}

function proxyApi(req, res, apiPath) {
  const chunks = [];
  req.on('data', (c) => chunks.push(c));
  req.on('end', () => {
    const body = Buffer.concat(chunks);
    const headers = { ...req.headers, host: `127.0.0.1:${API_PORT}` };
    delete headers['content-length'];
    const upstream = http.request(
      {
        hostname: '127.0.0.1',
        port: API_PORT,
        path: apiPath,
        method: req.method,
        headers,
      },
      (up) => {
        res.writeHead(up.statusCode || 502, {
          'Access-Control-Allow-Origin': '*',
          'Content-Type': up.headers['content-type'] || 'application/json',
        });
        up.pipe(res);
      },
    );
    upstream.on('error', () => {
      send(res, 502, JSON.stringify({ error: 'API недоступен. Запустите: python api/server.py' }), {
        'Content-Type': 'application/json; charset=utf-8',
        'Access-Control-Allow-Origin': '*',
      });
    });
    if (body.length) upstream.write(body);
    upstream.end();
  });
}

const server = http.createServer((req, res) => {
  try {
    const u = new URL(req.url || '/', `http://${req.headers.host || 'localhost'}`);
    if (u.pathname === '/api' || u.pathname.startsWith('/api/')) {
      if (req.method === 'OPTIONS') {
        res.writeHead(204, {
          'Access-Control-Allow-Origin': '*',
          'Access-Control-Allow-Methods': 'GET, POST, OPTIONS',
          'Access-Control-Allow-Headers': 'Content-Type, Authorization',
        });
        return res.end();
      }
      const apiPath = u.pathname.replace(/^\/api/, '') || '/';
      return proxyApi(req, res, apiPath + u.search);
    }

    const filePath = resolveFile(u.pathname);
    if (!filePath || !fs.existsSync(filePath)) {
      return send(res, 404, 'Not found', { 'Content-Type': 'text/plain; charset=utf-8' });
    }
    const ext = path.extname(filePath).toLowerCase();
    const data = fs.readFileSync(filePath);
    send(res, 200, data, {
      'Content-Type': MIME[ext] || 'application/octet-stream',
      'Cache-Control': ext === '.html' ? 'no-cache' : 'public, max-age=3600',
    });
  } catch (e) {
    send(res, 500, String(e), { 'Content-Type': 'text/plain; charset=utf-8' });
  }
});

server.listen(PORT, '0.0.0.0', () => {
  console.log(`AgroParts web server on http://0.0.0.0:${PORT} root=${ROOT} api->:${API_PORT}`);
});
