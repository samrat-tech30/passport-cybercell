---
name: frontend-conventions
description: Conventions for frontend/ - where components, the API client, hooks and styles go, the live event stream, run state, error and loading states, env vars. Use when creating or changing anything in frontend/ (together with project-ui for anything visible).
---

# Frontend conventions

**Stack:** React 19.3, Vite 8.3, TypeScript 7.0, plain CSS tokens. No router, no UI kit, no state library. Nothing else without asking.

## Where things go
| Thing | Path |
|---|---|
| App shell, tabs, top controls | `src/App.tsx` |
| Screens and pieces | `src/components/` (RunView, DecisionCard, Stamp, EvidenceDrawer, ApprovalDialog, WorldPanel, Scoreboard, AuditView) |
| **All backend calls** | `src/lib/api/client.ts` (`api.*`, `subscribe()`), types in `src/lib/api/types.ts` |
| Run state (live events → UI state) | `src/lib/useRun.ts` (reducer; dedupes events by `seq`) |
| Labels and small helpers | `src/lib/format.ts` |
| Styles | `src/styles/tokens.css` (values), `src/styles/app.css` (classes using tokens) |

## Rules
- Components never call `fetch`/`EventSource`; add a function to `client.ts`. Errors become `ApiError(status, code, message)`; show `message`.
- New event types: add to `EventType` in types.ts, the list in `subscribe()`, and the reducer in useRun.ts.
- Every view handles loading, empty, error and success. "Backend not reachable" must be readable, not a blank page.
- Dialogs use native `<dialog>` + `showModal()` guarded with `if (!ref.current.open)`; Esc on the approval dialog = Reject.
- Effects use block bodies (`useEffect(() => { ... })`), never an expression that returns a value.
- Never render backend text as HTML (`dangerouslySetInnerHTML` is banned): evidence must show hidden HTML as text.
- `VITE_API_URL` is the only env var; it is public.

## Commands (inside frontend/)
dev `npm run dev` · typecheck `npm run typecheck` · build `npm run build` · both `npm run check`
