# PWA Testing Guide

Use this checklist to verify Progressive Web App behavior.

## Preconditions

- Run frontend in production mode for realistic service worker behavior:
  - `npm run build`
  - `npm start`
- Open app in Chrome/Edge.

## Verify Manifest

1. Open DevTools -> Application -> Manifest.
2. Confirm manifest loads without errors.
3. Confirm app name, icons, start URL, and display mode are present.

## Verify Service Worker

1. DevTools -> Application -> Service Workers.
2. Confirm a service worker is registered and activated.
3. Reload once to ensure updates apply cleanly.

## Installability

1. In browser address bar, verify install icon appears.
2. Install app.
3. Launch installed app and verify it opens correctly.

## Offline Behavior

1. In DevTools -> Network, switch to Offline.
2. Reload app.
3. Confirm offline fallback page is shown (or cached shell behavior works).
4. Return online and verify normal routes recover.

## Cache Safety Checks

1. DevTools -> Application -> Cache Storage.
2. Confirm caches are not growing without bound after normal navigation.
3. Verify old cache versions are cleaned after new deployment.

## Troubleshooting

- If service worker does not register:
  - Ensure app is running in production mode.
  - Check `_app.tsx` registration guard (`NODE_ENV === 'production'`).
- If stale assets appear:
  - Hard refresh and unregister old worker in DevTools.
  - Rebuild and restart frontend.
- If install prompt is missing:
  - Confirm manifest/icons are valid and served over HTTPS in deployed environments.
