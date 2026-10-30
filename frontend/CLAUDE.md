# Frontend rules (in addition to the root CLAUDE.md)

- **Stack:** React 19.3, Vite 8.3, TypeScript 7.0 (`tsc` is the new native compiler), plain CSS with tokens. No UI library, no Tailwind, no router (three tabs in `App.tsx`). Add nothing else without asking.
- Follow `frontend-conventions` for structure and `project-ui` for anything visible. Look at `../design/mockups/*.png` before changing a screen.
- **All backend calls go through `src/lib/api/client.ts`**, typed by `src/lib/api/types.ts` (mirror of `../contracts/README.md`). Components never call `fetch` or `EventSource` directly.
- Styles: values only from `src/styles/tokens.css` (the guard hook blocks raw hex colours elsewhere).
- The backend URL comes from `VITE_API_URL` (`.env.local`). Everything in a `VITE_` variable is public: never put a secret there.
- A UI task is done only after the screenshot loop: `node scripts/screenshot.mjs /` (desktop 1440×900) and `--projector` (1280×720), PNGs read and compared with the mockups.
- Commands (inside `frontend/`): dev `npm run dev` · typecheck `npm run typecheck` · build `npm run build` · all `npm run check`.
