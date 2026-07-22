#!/usr/bin/env node
/**
 * Static host for Expo web export with clean SPA-like routes.
 * Maps /search -> search.html, /part/p001 -> part/[id].html, etc.
 */
const http = require('http');
const fs = require('fs');
const path = require('path');
const { URL } = require('url');

const ROOT = process.env.WEB_ROOT || path.join(__dirname, '..', 'www');
const PORT = Number(process.env.PORT || 8090);

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

  // SPA / hash app fallback
  return path.join(ROOT, 'index.html');
}

const server = http.createServer((req, res) => {
  try {
    const u = new URL(req.url || '/', `http://${req.headers.host || 'localhost'}`);
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
  console.log(`AgroParts web server on http://0.0.0.0:${PORT} root=${ROOT}`);
});
