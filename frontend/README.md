# Trend Detective React product

This is the new landing page and analysis workspace. The previous static UI
remains at `/app/`; the backend root serves the React build at `/product/`.

The landing hero, three illustrated story chapters, and investigation console
share an astrobotany observatory art direction. The chapter illustration and
console background live in `public/story-scenes-v2.png` and
`public/mission-control-bg.png`. All headings, navigation, methods, numbers,
and results are React elements rather than text embedded in those images.
On a phone, the investigation has a fixed four-stage navigator.

## Develop

```powershell
cd frontend
npm ci
npm run dev
```

Vite proxies `/v1` to the FastAPI backend at `127.0.0.1:8000`.

## Build and serve

```powershell
cd frontend
npm run build
cd ..
python backend/run.py
```

Open `http://127.0.0.1:8000/`. The root redirects to `/product/`.

## Offline demo

The build includes `offline_data.js`, a precomputed snapshot. With Node.js
installed, run `dist/product/START_OFFLINE.cmd` on Windows or
`node dist/product/serve-offline.cjs` elsewhere. Open the printed URL.
Offline mode supports the 12 predefined variable-region analyses over the full
2001–2024 period. Custom dates and AOIs require the backend. The interface
labels offline results as precomputed and does not invent missing analyses.

## Scientific boundaries

The hero art and landing illustrations are conceptual. Analysis numbers,
series, sensitivity windows, spatial significance and explanations come from
the existing API or its frozen offline snapshot. The spatial layer is the
full-period reference product, even when an analysis uses another time window.
The UI copies statistics; it never computes a new trend or p-value.
