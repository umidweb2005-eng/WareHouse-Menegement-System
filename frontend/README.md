# WMS Frontend

Production frontend for the Warehouse Management System FastAPI backend.

## Stack
React 19 · TypeScript · Vite · Tailwind CSS · shadcn/ui · React Router v7 ·
TanStack Query · Axios · React Hook Form · Zod · sonner.

## Prerequisites
- Node.js 18+ (20/22 recommended)
- The backend running at `http://localhost:8000`

## Setup & run

```bash
cd frontend
npm install
cp .env.example .env      # optional; defaults to the Vite proxy
npm run dev               # http://localhost:5173
```

The dev server proxies `/api/*` to `http://localhost:8000` (see `vite.config.ts`),
so no CORS setup is needed in development.

## Build

```bash
npm run build             # tsc -b && vite build  -> dist/
npm run preview           # serve the production build
npm run typecheck         # tsc --noEmit
```

## Configuration
- `VITE_API_URL` — backend API base. Default `/api/v1` (via dev proxy). In
  production set it to the full URL, e.g. `https://api.example.com/api/v1`.

## Auth
Login (`admin` / `Admin12345!` by default) obtains a JWT access + refresh token
pair. The access token is attached to every request; on `401` the client
transparently refreshes once and retries.

## Implemented (Phase 1)
Project setup, routing, authentication, login page, protected & role-guarded
routes, app layout (sidebar + header), light/dark theme.
Modules under **Katalog / Kontragentlar / Operatsiyalar / Moliya / Tizim** are
shown as "tez orada" in the sidebar and will be implemented in later phases.
