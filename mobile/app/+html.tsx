import type { ReactNode } from 'react';

// This file is web-only and used to configure the root HTML for every
// web page during static rendering.
// The contents of this function only run in Node.js environments and
// do not have access to the DOM or browser APIs.
export default function Root({ children }: { children: ReactNode }) {
  return (
    <html lang="en">
      <head>
        <meta charSet="utf-8" />
        <meta httpEquiv="X-UA-Compatible" content="IE=edge" />
        <meta name="viewport" content="width=device-width, initial-scale=1, shrink-to-fit=no" />

        {/* Keep mobile browser scrolling usable for AgroParts web. */}
        <style dangerouslySetInnerHTML={{ __html: responsiveBackground }} />
        {/* Add any additional <head> elements that you want globally available on web... */}
      </head>
      <body>{children}</body>
    </html>
  );
}

const responsiveBackground = `
html, body, #root {
  height: 100%;
}
body {
  background-color: #E8EEE9;
  overflow: auto;
  overscroll-behavior: none;
}
/* Expo tabs иногда оставляют absolute-слой на весь экран и блокируют клики */
[data-testid="bottom-tab-bar-overlay"],
div[style*="position: absolute"][style*="inset: 0"] {
  pointer-events: none !important;
}
a[role="tab"], button, [role="button"], input, textarea {
  pointer-events: auto !important;
}
@media (prefers-color-scheme: dark) {
  body {
    background-color: #E8EEE9;
  }
}`;
