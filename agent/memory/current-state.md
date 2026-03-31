# Current State

## Status

Early build stage. Frontend pages are mostly static/mocked. Backend API is substantially complete but disconnected from the frontend.

---

## Audit findings (task-001, 2026-03-20)

### Frontend file map

| Path                                  | Purpose                                      | Notes                                                                  |
| ------------------------------------- | -------------------------------------------- | ---------------------------------------------------------------------- |
| `src/app/page.tsx`                    | Root/home page                               | Not yet inspected in detail                                            |
| `src/app/layout.tsx`                  | Root layout                                  | Wraps all pages                                                        |
| `src/app/dashboard/page.tsx`          | Dashboard summary                            | **All values hardcoded** — no API calls                                |
| `src/app/portfolio/page.tsx`          | Portfolio list view                          | **Uses `mockData` const**, no API calls                                |
| `src/app/portfolio/[id]/page.tsx`     | Portfolio detail                             | Not yet inspected                                                      |
| `src/app/insurance/page.tsx`          | Insurance recommendations                    | Not yet inspected                                                      |
| `src/app/pension/page.tsx`            | Pension planner                              | Not yet inspected                                                      |
| `src/app/currency/page.tsx`           | Currency converter                           | Not yet inspected                                                      |
| `src/components/PerformanceChart.tsx` | Chart component                              | Not yet inspected                                                      |
| `src/components/PortfolioChart.tsx`   | Chart component                              | Not yet inspected                                                      |
| `src/components/Providers.tsx`        | Context/theme wrapper                        | Not yet inspected                                                      |
| `src/components/ThemeToggle.tsx`      | Dark/light toggle                            | Exists and in use                                                      |
| `src/components/motion-div.tsx`       | Framer Motion wrapper                        | Used in portfolio page                                                 |
| `src/lib/api.ts`                      | HTTP client (`ApiClient` class)              | All endpoints defined here, token from localStorage                    |
| `src/contexts/AuthContext.tsx`        | Auth state + login/logout                    | Has broken API calls (see risks)                                       |
| `src/types/api.ts`                    | Shared API types (`User`, `ApiClient`, etc.) | Defines `ApiClient` interface separately from implementation           |
| `src/types/assets.ts`                 | Asset and AssetWithPerformance types         | Aligned with backend schemas                                           |
| `src/types/portfolios.ts`             | Canonical portfolio types                    | Consolidated as single source of truth in task-002                     |
| `src/types/domain.ts`                 | Shared domain types                          | Defines watchlist, sentiment, holdings, and snapshot shapes (task-002) |
| `src/types/auth.ts`                   | Auth types                                   | `AuthContextType` interface lives here                                 |
| `src/types/chart.ts`                  | Chart-related types                          | Not yet inspected                                                      |
| `src/types/components.ts`             | Component prop types                         | Not yet inspected                                                      |
| `src/types/index.ts`                  | Barrel re-export                             | Exports from all type files                                            |
| `src/types/theme.ts`                  | Theme types                                  | Not yet inspected                                                      |
| `src/styles/chakra-tailwind.css`      | Chakra + Tailwind bridge                     | Exists                                                                 |
| `src/styles/theme.ts`                 | Chakra theme config                          | Not yet inspected                                                      |
| `src/services/sentiment.ts`           | Sentiment normalization service              | Added in task-003; normalizes score/label/confidence + batch payloads  |

### Backend file map

| Path                         | Purpose                  | Notes                                                                                     |
| ---------------------------- | ------------------------ | ----------------------------------------------------------------------------------------- |
| `backend/main.py`            | FastAPI app, all routes  | Large single file — auth, portfolios, assets, sentiment, currency, insurance, pension     |
| `backend/models.py`          | SQLAlchemy ORM models    | User, Portfolio, Asset, AssetPriceHistory, SentimentResult, InsuranceProduct, PensionPlan |
| `backend/schemas.py`         | Pydantic v2 schemas      | Covers all domains; `UserCreate` validator uses `@validator` (Pydantic v1 syntax)         |
| `backend/auth.py`            | JWT auth helpers         | `create_access_token`, `get_current_user`, `authenticate_user`                            |
| `backend/config.py`          | Pydantic settings        | DB URL, JWT secret, Twitter keys                                                          |
| `backend/database.py`        | Async SQLAlchemy session | Not yet read in detail                                                                    |
| `backend/twitter_fetcher.py` | Tweepy Twitter client    | Fetches tweets by stock symbol; credentials from `.env`                                   |
| `backend/globalSetting.py`   | Global state holder      | Holds `sentiment_model` reference                                                         |
| `backend/alembic/`           | DB migrations            | Exists                                                                                    |
| `backend/tests/`             | Test files               | Multiple test files; some duplicated (auth-tests.py vs test_token.py)                     |

---

## Boundary violations and risks

### 1. Dashboard and portfolio pages have no real data

- `dashboard/page.tsx`: all metrics (`$234,500`, `+5.2%`, `12 assets`) are hardcoded strings.
- `portfolio/page.tsx`: chart uses a local `mockData` constant, allocation cards use hardcoded dollar values.
- No API calls are made from either page. The `apiClient` in `src/lib/api.ts` is never imported in these pages.

### 2. AuthContext calls methods that do not exist on the exported apiClient

- `AuthContext.tsx` calls `apiClient.get(...)` and `apiClient.post(...)` directly.
- The exported `apiClient` is an instance of `ApiClient` class which only exposes named methods (`login()`, `register()`, `getPortfolios()`, etc.) — there are no public `.get()` or `.post()` methods.
- The `ApiClient` interface in `types/api.ts` defines `.get()` and `.post()`, but this interface is not implemented by the class in `lib/api.ts`.
- Auth endpoint paths also mismatch: AuthContext calls `/api/auth/current-user` but backend exposes `/auth/me`.

### 3. Type consolidation completed (task-002)

- Removed duplicate `types/portfolio.ts`; `types/portfolios.ts` is now canonical.
- Barrel exports now reference only canonical portfolio types.
- Added `types/domain.ts` for shared `watchlist`, `sentiment`, `holding`, and `historical snapshot` domain contracts.

### 4. Sentiment service layer introduced (task-003)

- Added `src/services/sentiment.ts` with explicit normalization rules for label, score, and confidence.
- Service returns stable `SentimentResult` objects and includes a batch adapter (`normalizeSentimentBatch`).
- UI still needs to consume this service in future work (task-006/task-005).

### 5. No portfolio summary service yet

- No service layer exists yet for portfolio summary calculations or watchlist signal composition.
- The backend performs portfolio performance calculations inside API route handlers (not in a service module).

### 6. No sentiment UI

- Backend has a fully-functional FinBERT sentiment analysis pipeline and Twitter fetcher.
- No frontend page or component exists to display sentiment results.

### 7. No watchlist feature

- Architecture docs call for a watchlist domain; nothing exists on frontend or backend.

### 8. CLAUDE.md stack mismatch

- CLAUDE.md lists "Prisma" as the database ORM, but the actual stack uses SQLAlchemy + Alembic.

### 9. Pydantic v1/v2 mixing

- `schemas.py` uses `@validator` (Pydantic v1) inside a Pydantic v2 `BaseModel`.
  This is allowed in compatibility mode but is a known fragility point.

### 10. `config.py` `is_production` is a method but used as a property

- `settings.is_production` is defined as a method `def is_production(self) -> bool` but used as `settings.is_production` (without calling it) in `main.py` conditional expressions.

### 11. Agent workflow and verification commands are now documented

- `AGENTS.md` now includes the repo-specific agent workflow, required context files, task-update expectations, and concrete frontend/backend command references.
- Agent helper commands are documented via `source agent/agent-tools.sh && ...`.
- Verification guidance now points contributors to run the smallest relevant command set instead of relying on vague "run checks" language.

### 12. Portfolio summary service has been added on the frontend

- Added `frontend/src/services/portfolio-summary.ts` as a pure calculation layer for portfolio totals, allocation slices, and gain/loss metrics.
- The service aggregates duplicate symbols, derives fallback values when price fields are missing, and returns stable typed output for future dashboard loaders/cards.
- `frontend/src/types/domain.ts` now includes `PortfolioAllocationSlice`, `PortfolioGainLossMetrics`, and `PortfolioSummaryResult`.
- Frontend dependencies were installed and task-004 verification was run. Current TypeScript/lint failures are in pre-existing files outside the new service (`pension/page.tsx`, `portfolio/[id]/page.tsx`, `AuthContext.tsx`, `currency/page.tsx`, `insurance/page.tsx`, `layout.tsx`, `lib/api.ts`).

### 13. Dashboard data now flows through a dedicated loader

- Added `frontend/src/app/dashboard/data.ts` as the route-level composition layer for dashboard data.
- The loader fetches portfolio detail records, aggregates all holdings through `summarizePortfolio()`, and derives an optional primary sentiment signal from the largest holding's stored sentiment history.
- `frontend/src/app/dashboard/page.tsx` now renders loading, error, and populated states from loader output instead of hardcoded metric strings.
- `frontend/src/lib/api.ts` now exposes `getSentimentHistory()` and typed payloads for asset/pension updates.
- Targeted ESLint for the changed dashboard/API files passes. Full frontend `tsc --noEmit` still fails in pre-existing files: `pension/page.tsx`, `portfolio/[id]/page.tsx`, and `AuthContext.tsx`.

### 14. Sentiment history now has a dedicated chart adapter

- Added `frontend/src/services/sentiment-trend.ts` as the canonical adapter from backend `sentiment/history` payloads to chart-ready frontend points.
- The adapter normalizes dates, clamps sentiment percentages, computes a stable `score` in `[-1, 1]`, drops invalid dates, and returns an empty list for missing history.
- `frontend/src/types/chart.ts` now defines `SentimentChartPoint` so chart consumers can rely on one typed shape.

### 15. Frontend build verification is clean again

- Fixed the remaining frontend TypeScript and ESLint blockers in auth, portfolio detail, pension, currency, insurance, layout, and the portfolio overview page.
- `frontend/src/lib/api.ts` now matches the backend auth contract more closely by using `/auth/token` for login and exposing `getCurrentUser()`.
- `frontend/src/contexts/AuthContext.tsx` now uses named `apiClient` methods instead of nonexistent generic `.get()` / `.post()` calls.
- The `/portfolio` route is now explicitly client-rendered so the production build can safely include its chart/motion dependencies.
- Verification now passes for `./node_modules/.bin/tsc --noEmit`, targeted ESLint, and `npm run build` in `frontend/`.

### 16. Dashboard summary cards are now reusable components

- Added `frontend/src/components/dashboard/DashboardSummaryCards.tsx` as the shared rendering layer for dashboard summary cards.
- The component renders typed portfolio value, asset count, sentiment signal, and allocation highlight cards directly from `DashboardData`.
- Loading state now uses card-shaped skeletons instead of a generic spinner, and empty states fall back to neutral copy when no holdings exist.
- `frontend/src/app/dashboard/page.tsx` now focuses on request-state orchestration and delegates summary rendering to the component.

### 17. Dashboard now renders a sentiment trend chart

- Added `frontend/src/services/sentiment-trend.ts` as the canonical adapter from backend `sentiment/history` payloads to chart-ready `SentimentChartPoint[]`.
- `frontend/src/types/chart.ts` now defines `SentimentChartPoint` for reusable chart consumers.
- `frontend/src/app/dashboard/data.ts` now exposes `sentiment_trend` alongside summary metrics and primary sentiment.
- Added `frontend/src/components/dashboard/SentimentTrendChart.tsx` to render the adapted trend data with chart-specific empty and loading states.
- Verification passes for targeted ESLint, `./node_modules/.bin/tsc --noEmit`, and `npm run build` in `frontend/`.

### 18. Review fixes applied (2026-03-27)

A reviewer pass on task-006/task-007 identified four bugs. All are now fixed:

**Bug 1 — broken import (build-breaking)**
- `frontend/src/app/dashboard/data.ts` imported `mapSentimentTrendHistory` from `@/services/sentiment-trend`, but the exported name is `buildSentimentTrendPoints`. Fixed: import updated to `buildSentimentTrendPoints`.

**Bug 2 — sentiment score double-processing (data corruption)**
- `loadPrimarySentiment` computed a net score in `[-1, 1]` via `toSentimentScore`, then passed it through `normalizeSentimentResult` → `normalizeSentimentScore`. That function treats any value in `[0, 1]` as a raw model probability and re-maps it: e.g. `0.4` became `-0.2`. Only negative scores passed through correctly.
- Fixed: replaced `normalizeSentimentResult` usage with a direct `SentimentResult` construction. A local `scoreToSentimentLabel` maps the already-normalized score to the domain label. The `normalizeSentimentScore` function is not called on trend-derived scores.

**Bug 3 — duplicate API calls (efficiency)**

- `loadPrimarySentiment` and `loadSentimentTrend` both independently called `apiClient.getSentimentHistory(symbol, 7)`, producing two identical requests per dashboard load.
- Fixed: a single `loadSentimentHistory` fetch is performed in `loadDashboardData`; `derivePrimarySentiment` and `deriveSentimentTrend` both consume the same result.

**Bug 4 — loss accent color invisible (UI)**

- `DashboardSummaryCards.tsx` rendered negative `total_profit_loss` in `gray.500`, indistinguishable from neutral text.
- Fixed: changed to `red.500`.

**CLAUDE.md correction**

- `CLAUDE.md` listed Prisma as the ORM; the actual backend uses SQLAlchemy + Alembic. Corrected.

- Verification: `tsc --noEmit --skipLibCheck` filtered to `src/app/dashboard/data.ts` reports zero errors after fixes. All other tsc errors across the project are pre-existing "cannot find module" failures caused by `frontend/node_modules` not being installed in this environment. Full `npm install && npm run build` in `frontend/` is required to confirm a clean build in a real environment.

### 19. Dashboard now has a watchlist-ready signal panel

- Added `frontend/src/services/watchlist-signals.ts` as the service-layer adapter for watchlist rows plus optional sentiment history enrichment.
- Added `frontend/src/components/dashboard/WatchlistSignalPanel.tsx` to render loading, unavailable, empty, and populated watchlist states without embedding signal logic in the UI.
- `frontend/src/app/dashboard/data.ts` now fetches watchlist data through `lib/api.ts`, enriches up to four watchlist symbols with sentiment history, and returns a discriminated watchlist state on `DashboardData`.
- `frontend/src/lib/api.ts` now exposes `getWatchlist()` as the canonical frontend access point for the future backend route.
- The dashboard degrades safely when `/watchlist` is not present yet: the rest of the dashboard still loads, and the panel shows that backend support is not available on the current branch.
- Verification passes for `./node_modules/.bin/tsc --noEmit`, targeted ESLint on changed frontend files, and `npm run build` in `frontend/`.

---

### 19. Watchlist backend domain added (task-008, 2026-03-29)

- Added `WatchlistItem` ORM model to `backend/models.py` with `user_id`, `symbol`, `display_name`, `notes`, and `created_at`/`updated_at` via `TimestampMixin`. Unique index on `(user_id, symbol)` prevents duplicate entries.
- Added `WatchlistItemCreate`, `WatchlistItemOut`, and `WatchlistItemSentiment` Pydantic schemas to `backend/schemas.py`. `WatchlistItemSentiment` derives a `[-1, 1]` score from the raw FinBERT `sentiment` + `confidence` columns.
- Fixed `schemas.py` bug: migrated `UserCreate.password_strength` from `@validator` (Pydantic v1) to `@field_validator` + `@classmethod` (Pydantic v2).
- Added three endpoints to `backend/main.py`:
  - `GET /watchlist` — returns all items for the authenticated user, each enriched with the most recent `SentimentResult` for that symbol.
  - `POST /watchlist` — adds a symbol; returns 409 if already present.
  - `DELETE /watchlist/{symbol}` — removes a symbol; returns 404 if not found.
- Added Alembic migration `add_watchlist_items.py` (revision `a1b2c3d4e5f6`, down_revision `f9d3e2c1a8b4`).
- Frontend `/watchlist` page and API client methods remain to be built (task-008 frontend phase).

### 20. Watchlist frontend flow completed (task-008, 2026-03-29)

- Added `frontend/src/app/watchlist/page.tsx` as the watchlist management route for listing, adding, and removing tracked symbols.
- `frontend/src/lib/api.ts` now exposes `addToWatchlist()` and `removeFromWatchlist()` alongside `getWatchlist()`.
- `frontend/src/app/dashboard/page.tsx` now links to the `/watchlist` route so the new flow is discoverable from the dashboard.
- Fixed watchlist signal normalization in `frontend/src/services/watchlist-signals.ts`: embedded backend watchlist scores are now treated as already-normalized `[-1, 1]` values instead of being re-processed as raw model probabilities.
- Fixed dashboard watchlist selection in `frontend/src/app/dashboard/data.ts`: the loader now ranks the full watchlist first, then fetches history for the top symbols instead of permanently trimming to the oldest four entries.
- Verification passes for targeted ESLint, `npm run build`, and `./node_modules/.bin/tsc --noEmit` in `frontend/`.

### 21. Historical snapshot plan is now defined (task-010, 2026-03-29)

- Added `agent/memory/historical-snapshot-plan.md` as the canonical design note for historical portfolio and sentiment data.
- The recommended direction is:
  - persist daily portfolio-level snapshots in a dedicated aggregate table
  - persist child holding snapshot rows for allocation-over-time and comparison views
  - keep sentiment history derived from raw `SentimentResult` rows for now instead of introducing a second sentiment snapshot table
- The plan explicitly documents the write direction (daily scheduled snapshot job with idempotent upsert), read direction (snapshot-backed portfolio chart API), fallback behavior, and the trade-offs between mock and persistent history.
- This task is documentation-only; no schema or API changes were made yet.

### 22. Portfolio snapshot persistence is now live (task-011, 2026-03-31)

- Added `PortfolioSnapshot` and `PortfolioSnapshotHolding` ORM models plus an Alembic migration to persist daily portfolio aggregates and holding rows.
- Added snapshot capture/history/detail APIs in `backend/main.py` and a dedicated `backend/portfolio_snapshots.py` service module to keep snapshot logic out of route handlers.
- Asset create, update, and delete now refresh the current day snapshot best-effort so the latest portfolio state is persisted without waiting for a batch job.
- Snapshot capture resolves prices in this order: live yfinance quote, latest stored `AssetPriceHistory`, then purchase price fallback.

### 23. Daily snapshot job and backfill path now exist (task-013, 2026-03-31)

- Added `backend/snapshot_jobs.py` as the canonical batch entrypoint for historical snapshot capture.
- The job captures only missing snapshot rows for a given date, so repeated runs are idempotent and safe after restarts.
- Added inclusive range backfill support via `python3 -m backend.snapshot_jobs --backfill-start YYYY-MM-DD --backfill-end YYYY-MM-DD`.
- Added optional scheduler configuration in `backend/config.py` and startup wiring in `backend/main.py` behind `SNAPSHOT_SCHEDULER_ENABLED`; this is intended for exactly one dedicated process.
- Documented the manual run, backfill, and dedicated scheduler env vars in `README.md`.
- Fixed `backend/database.py` to bind `async_session_factory` to the SQLAlchemy engine so real runtime sessions, including the new snapshot job, can open database connections correctly.

### 24. Frontend portfolio history wired to snapshot API (task-012, 2026-03-31)

- `frontend/src/lib/api.ts` now exposes `getPortfolioSnapshotHistory(portfolioId, days?)` calling `GET /portfolios/{id}/snapshots?days=N` and `getPortfolioSnapshot(portfolioId, date)` calling `GET /portfolios/{id}/snapshots/{date}`.
- `frontend/src/types/domain.ts` now exports `PortfolioSnapshotHistoryResponse { portfolio_id, from_date, to_date, points }` aligned with the backend schema.
- `frontend/src/app/portfolio/[id]/page.tsx` now fetches snapshot history in parallel with portfolio detail, maps `HistoricalSnapshotPoint[]` to `DataPoint[]`, and renders `PerformanceChart` when history is available. The history fetch degrades silently to an empty chart if the endpoint returns an error or has no data yet.
- `PerformanceChart` is loaded via `next/dynamic` with `ssr: false` to keep the d3 dependency client-only.
- Verification: `tsc --noEmit --skipLibCheck` on changed files reports zero errors. Full `npm run build` requires `npm install` in `frontend/` which is not available in this environment.

## Likely priorities (updated)

1. Review the frontend auth flow against the backend runtime contract beyond compile-time alignment
2. Add snapshot comparison endpoint and UI hook (task-014)
3. Validate the watchlist and portfolio history flows in a live authenticated environment
