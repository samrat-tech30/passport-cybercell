# Deploy: two servers, one repo

`backend/` and `frontend/` are independent. Deploy each with its own **root directory** setting.

## Backend (any container host: Render, Railway, Fly.io, a VM)
1. New service from this GitHub repo, **root directory = `backend`**, build from `backend/Dockerfile`.
2. Environment variables (host dashboard, never in git):
   - `APP_ENV=prod`
   - `ALLOWED_ORIGINS=https://<your-frontend-domain>` (exact origin, no trailing slash)
   - `DEMO_ACCESS_CODE=<6+ chars>` (recommended on a public URL)
   - `DATA_DIR=/data` (already the image default; attach a disk there if the host supports it)
   - optional live mode: `ALLOW_LIVE_LLM=true`, `LLM_BASE_URL`, `LLM_API_KEY`, `LLM_MODEL`
3. The container listens on `$PORT` (default 8000). Health check path: `/health`.
4. Check: `curl https://<backend>/health` → `{"status":"ok",…}`.
Free tiers may sleep: open `/health` 2 minutes before judging. Without a persistent disk the SQLite file resets on redeploy (fine for a demo).

## Frontend (Vercel, Netlify, Cloudflare Pages)
1. New project from the same repo, **root directory = `frontend`**.
2. Build command `npm run build`, output directory `dist`.
3. Environment variable: `VITE_API_URL=https://<your-backend-domain>` (public by design).
4. Security headers: `frontend/vercel.json` (Vercel) or `frontend/public/_headers` (Netlify/Cloudflare).
5. Open the site → the scenario list loads → run S2.

## If the frontend can't reach the backend
- Banner "Can't reach the backend": wrong `VITE_API_URL` (rebuild after changing it) or the backend is asleep.
- Browser console CORS error: `ALLOWED_ORIGINS` doesn't exactly match the frontend origin (scheme + host, no slash).
- 401 on Run scenario: enter the demo code in the top bar.

**Not verified yet:** none of these hosts was tried from the starter. M1 records what worked in API-NOTES.md and here.
