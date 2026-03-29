# Decisions

## Initial decisions

- The project will use a task-driven agent workflow
- The agent should complete one task at a time
- The agent must update memory after each meaningful task
- The service layer should hold transformation and normalization logic
- UI components should receive already-shaped data where possible
- Verification matters more than confident prose

## Decision log

### [2026-03-20] Treat lib/api.ts as the canonical data-access layer

Context:
AuthContext.tsx calls `apiClient.get()` and `apiClient.post()` which are not exposed by the `ApiClient` class. There is also a separate `ApiClient` interface in `types/api.ts` that defines these methods but is not implemented.

Decision:
Keep `lib/api.ts` as the single data-access layer, using named methods per domain. Do not add raw `.get()`/`.post()` to the class. Fix AuthContext to use named methods.

Reason:
Named methods make the data contract explicit, are easier to mock in tests, and prevent scattered raw-URL calls from spreading through the codebase.

Impact:
`AuthContext.tsx` must be updated to use `apiClient.login()`, `apiClient.register()`, and a new `apiClient.getCurrentUser()` method. The `ApiClient` interface in `types/api.ts` may be removed or repurposed.

---

### [2026-03-20] Use portfolios.ts as canonical portfolio type file; delete portfolio.ts

Context:
Both `types/portfolio.ts` and `types/portfolios.ts` define nearly identical Portfolio interfaces. Both are re-exported from the barrel `types/index.ts`, causing potential name collisions.

Decision:
Canonicalize `portfolios.ts` and remove `portfolio.ts`. Add a dedicated `types/domain.ts` file for non-portfolio shared domain shapes.

Reason:
Single source of truth prevents drift. The `last_updated` nullability difference between the two files is a sign of divergence that will cause bugs.

Impact:
Any consumer must import portfolio types from `types/portfolios.ts` (or the main type barrel). Shared watchlist/sentiment/snapshot contracts now live in `types/domain.ts`.

### [2026-03-22] Add a dedicated sentiment normalization service module

Context:
Task-003 requires sentiment normalization rules to be explicit and reusable so that presentation components do not transform raw payloads directly.

Decision:
Create `frontend/src/services/sentiment.ts` as the canonical normalization layer for raw sentiment payloads, with pure functions for score, confidence, label, single-result mapping, and batch mapping.

Reason:
A dedicated service keeps normalization deterministic and testable, avoids duplicated ad-hoc transforms in UI code, and gives downstream components a stable `SentimentResult` shape.

Impact:
Future dashboard loaders/components should use `normalizeSentimentResult` / `normalizeSentimentBatch` instead of parsing sentiment data in page files. This unblocks task-006 (trend adapter) and supports task-005 data orchestration.

---

### [2026-03-26] Keep agent workflow and verification commands in AGENTS.md

Context:
The repo already contains an agent scaffold in `agent/`, but the top-level `AGENTS.md` only described high-level coding principles and did not list the actual workflow or runnable commands.

Decision:
Document the required agent reading order, task-selection rules, memory update expectations, helper commands from `agent/agent-tools.sh`, and the main frontend/backend verification commands directly in `AGENTS.md`.

Reason:
The implementation workflow should be discoverable from the primary repo instructions. Keeping the command list in one obvious place reduces guesswork and makes task completion criteria more testable.

Impact:
Contributors should use `AGENTS.md` as the top-level workflow reference, then follow the detailed prompts and memory files under `agent/`. Task-009 can be treated as completed documentation work.

---

### [2026-03-26] Model portfolio summaries as a dedicated frontend service

Context:
Task-004 requires summary calculations to live outside UI components, and the current frontend pages still use hardcoded values instead of a reusable calculation layer.

Decision:
Add `frontend/src/services/portfolio-summary.ts` as a pure service that accepts partial asset inputs and returns a `PortfolioSummaryResult` containing summary totals, allocation slices, and simple gain/loss metrics.

Reason:
This keeps arithmetic out of page components, gives task-005/task-007 a stable typed input, and makes fallback handling for missing prices explicit in one place.

Impact:
Future dashboard loaders and portfolio cards should call `summarizePortfolio()` instead of calculating totals or allocation percentages inline. Duplicate symbol rows are merged into one allocation slice, and missing current prices fall back to cost-based values.

---

### [2026-03-26] Keep dashboard data orchestration in a dedicated route loader until auth is server-safe

Context:
Task-005 requires dashboard composition to move out of the page, but the current frontend auth/data client still depends on browser-only token storage and redirect behavior.

Decision:
Create `frontend/src/app/dashboard/data.ts` as a client-safe route-level loader that composes portfolio detail fetches, portfolio summary aggregation, and optional sentiment history lookup for the leading holding.

Reason:
This removes scattered business logic from `dashboard/page.tsx` immediately without introducing a server-side fetch path that would break under the current `localStorage`-based auth model.

Impact:
The dashboard page now focuses on request-state rendering, while future auth changes can migrate the loader server-side without reintroducing business logic into the UI component.

---

### [2026-03-26] Model sentiment history as chart-specific frontend points

Context:
Task-006 requires the app to stop passing raw `sentiment/history` payloads toward presentation code and instead provide a stable chart-oriented shape that tolerates incomplete upstream data.

Decision:
Add `frontend/src/services/sentiment-trend.ts` as a pure adapter that maps raw history entries into `SentimentChartPoint` values.

Reason:
This keeps history normalization and score derivation in one place, avoids leaking backend response details into chart components, and gives future sentiment visualizations a single typed input contract.

Impact:
Any dashboard or watchlist chart can consume `SentimentChartPoint[]` directly. Invalid or partial history rows are filtered or normalized before they reach presentation code.

---

### [2026-03-26] Align frontend auth calls with the backend before expanding UI work

Context:
The clean-build pass exposed that `AuthContext.tsx` and the portfolio detail page still depended on nonexistent generic API client methods, while the backend auth flow actually uses `/auth/token` and `/auth/me`.

Decision:
Keep `lib/api.ts` as the single access layer and update it to expose backend-aligned named auth methods (`login()` using form data and `getCurrentUser()`), then update consumers to call those methods directly.

Reason:
This preserves the existing explicit-client pattern and removes a class of compile-time and runtime mismatches without reintroducing raw URL calls throughout the frontend.

Impact:
Auth-related consumers now compile cleanly, token storage stays centralized in the frontend auth flow, and future auth refactors have a clearer starting point.

---

### [2026-03-26] Render dashboard summary state through reusable card components

Context:
Task-007 requires the dashboard summary UI to be reusable and typed, while the current dashboard page still contained card markup and text shaping inline.

Decision:
Add `frontend/src/components/dashboard/DashboardSummaryCards.tsx` as the reusable presentation layer for summary cards and keep the page responsible only for loader state orchestration.

Reason:
This keeps calculation and data composition outside the UI, centralizes the dashboard card markup in one place, and makes loading and empty states consistent without duplicating card structure.

Impact:
Future dashboard or portfolio views can reuse the same summary card component shape, and the route page is simpler to evolve because it no longer owns individual card markup.

---

### [2026-03-26] Keep sentiment chart transformation separate from chart rendering

Context:
The dashboard needed a sentiment trend chart, but the backend `sentiment/history` payload is not a presentation-ready chart format.

Decision:
Add a dedicated `frontend/src/services/sentiment-trend.ts` adapter and keep `SentimentTrendChart.tsx` focused only on rendering `SentimentChartPoint[]`.

Reason:
This preserves the service-layer boundary established in earlier tasks, avoids pushing API-shape knowledge into chart components, and makes empty or malformed history handling deterministic in one place.

Impact:
Future dashboard or watchlist charts can reuse the same adapted sentiment series without duplicating normalization logic.

---

### [2026-03-27] Construct primary sentiment result directly instead of routing through normalizeSentimentResult
Context:
`loadPrimarySentiment` in `dashboard/data.ts` computed a net score via `(positive - negative) / 100`, producing a value in `[-1, 1]`, then passed it to `normalizeSentimentResult`. That function internally calls `normalizeSentimentScore`, which treats any value in `[0, 1]` as a raw model probability and remaps it to `[-1, 1]` via `(score * 2) - 1`. This corrupted all non-negative net sentiment scores.

Decision:
Construct the `SentimentResult` object directly in `derivePrimarySentiment`, using a local `scoreToSentimentLabel` helper to map the score to a domain label. Do not call `normalizeSentimentResult` on scores that are already in `[-1, 1]` net sentiment format.

Reason:
`normalizeSentimentScore` is designed for raw model output probabilities. Net sentiment derived from percentage breakdowns is a different format and must not be re-processed. Constructing the result directly makes the assumption explicit and avoids coupling the loader to a function built for a different input contract.

Impact:
`normalizeSentimentResult` and `normalizeSentimentScore` remain correct for their intended use (raw model outputs in `sentiment.ts`). `dashboard/data.ts` now owns the label derivation for trend-based signals via `scoreToSentimentLabel`.

---

### [2026-03-27] Fetch sentiment history once per dashboard load
Context:
`loadPrimarySentiment` and `loadSentimentTrend` in `dashboard/data.ts` each independently called `apiClient.getSentimentHistory(symbol, 7)`, producing two identical HTTP requests per dashboard render.

Decision:
Add a single `loadSentimentHistory` function that fetches once and returns `RawSentimentHistory | null`. Both `derivePrimarySentiment` and `deriveSentimentTrend` accept the result and derive their outputs from the same payload.

Reason:
There is no reason to make two identical calls. Fetching once halves the network cost, keeps error handling in one place, and makes the data flow easier to trace.

Impact:
`loadDashboardData` now awaits `loadSentimentHistory` once before calling both derive functions. The `Promise.all` for the two sentiment fetches is removed.

---

### [2026-03-29] Treat watchlist data as an optional dashboard enhancement until the backend lands
Context:
Task-008 needed a dashboard watchlist signal panel, but the current branch still lacks the watchlist ORM, schemas, endpoints, and migration work being developed separately.

Decision:
Implement the frontend watchlist adapter and panel now, and treat `/watchlist` as an optional endpoint. When the route is missing, the dashboard returns a typed `watchlist.status = "unavailable"` state instead of failing the entire page load.

Reason:
This lets the frontend progress without conflicting with concurrent backend work, keeps the watchlist signal logic in service code instead of UI components, and makes the eventual merge mostly a contract check rather than a large UI refactor.

Impact:
`frontend/src/app/dashboard/data.ts`, `frontend/src/services/watchlist-signals.ts`, and `frontend/src/components/dashboard/WatchlistSignalPanel.tsx` now support both "backend missing" and "backend available" states. After the backend branch merges, the remaining work is validating the endpoint shape and end-to-end behavior.

---

### [2026-03-29] Rank watchlist candidates before trimming dashboard panel items
Context:
The dashboard watchlist panel is intentionally limited to a few symbols, but the backend returns watchlist rows oldest-first. Trimming the raw response before ranking would hide newer or stronger signals once the watchlist grows past the panel limit.

Decision:
Build and rank signal items across the full watchlist first, then fetch sentiment history only for the selected top symbols and render those in the panel.

Reason:
This preserves the panel limit without making the oldest rows sticky forever, and it keeps the more expensive sentiment-history fetches constrained to the items that will actually be shown.

Impact:
`frontend/src/app/dashboard/data.ts` now uses a two-step watchlist flow: base ranking from the embedded sentiment on all rows, followed by history enrichment for only the chosen panel symbols.

---

### [2026-03-29] Treat backend watchlist sentiment scores as already normalized
Context:
The backend watchlist endpoint returns `latest_sentiment.score` in `[-1, 1]`, derived directly from FinBERT sentiment plus confidence. Reusing `normalizeSentimentResult()` on that payload would incorrectly remap non-negative scores as if they were raw probabilities.

Decision:
Add a dedicated embedded-watchlist sentiment normalization path in `frontend/src/services/watchlist-signals.ts` that preserves backend scores, normalizes confidence, and derives the frontend label from the preserved score.

Reason:
Watchlist endpoint payloads are not the same contract as raw model outputs. A dedicated adapter keeps the service-layer boundary explicit and prevents silent data corruption in the dashboard and watchlist page.

Impact:
Embedded watchlist sentiment now produces correct score direction and strength in both the dashboard panel and the `/watchlist` page, even before history enrichment is fetched.

---

## Decision log format

Use this format for future entries:

### [YYYY-MM-DD] Decision title

Context:
What problem or question led to this decision?

Decision:
What was chosen?

Reason:
Why was this the best option?

Impact:
What files, flows, or future work does this affect?
