# Current State

## Status
Early build stage. Frontend pages are mostly static/mocked. Backend API is substantially complete but disconnected from the frontend.

---

## Audit findings (task-001, 2026-03-20)

### Frontend file map

| Path | Purpose | Notes |
|------|---------|-------|
| `src/app/page.tsx` | Root/home page | Not yet inspected in detail |
| `src/app/layout.tsx` | Root layout | Wraps all pages |
| `src/app/dashboard/page.tsx` | Dashboard summary | **All values hardcoded** — no API calls |
| `src/app/portfolio/page.tsx` | Portfolio list view | **Uses `mockData` const**, no API calls |
| `src/app/portfolio/[id]/page.tsx` | Portfolio detail | Not yet inspected |
| `src/app/insurance/page.tsx` | Insurance recommendations | Not yet inspected |
| `src/app/pension/page.tsx` | Pension planner | Not yet inspected |
| `src/app/currency/page.tsx` | Currency converter | Not yet inspected |
| `src/components/PerformanceChart.tsx` | Chart component | Not yet inspected |
| `src/components/PortfolioChart.tsx` | Chart component | Not yet inspected |
| `src/components/Providers.tsx` | Context/theme wrapper | Not yet inspected |
| `src/components/ThemeToggle.tsx` | Dark/light toggle | Exists and in use |
| `src/components/motion-div.tsx` | Framer Motion wrapper | Used in portfolio page |
| `src/lib/api.ts` | HTTP client (`ApiClient` class) | All endpoints defined here, token from localStorage |
| `src/contexts/AuthContext.tsx` | Auth state + login/logout | Has broken API calls (see risks) |
| `src/types/api.ts` | Shared API types (`User`, `ApiClient`, etc.) | Defines `ApiClient` interface separately from implementation |
| `src/types/assets.ts` | Asset and AssetWithPerformance types | Aligned with backend schemas |
| `src/types/portfolios.ts` | Canonical portfolio types | Consolidated as single source of truth in task-002 |
| `src/types/domain.ts` | Shared domain types | Defines watchlist, sentiment, holdings, and snapshot shapes (task-002) |
| `src/types/auth.ts` | Auth types | `AuthContextType` interface lives here |
| `src/types/chart.ts` | Chart-related types | Not yet inspected |
| `src/types/components.ts` | Component prop types | Not yet inspected |
| `src/types/index.ts` | Barrel re-export | Exports from all type files |
| `src/types/theme.ts` | Theme types | Not yet inspected |
| `src/styles/chakra-tailwind.css` | Chakra + Tailwind bridge | Exists |
| `src/styles/theme.ts` | Chakra theme config | Not yet inspected |
| `src/services/sentiment.ts` | Sentiment normalization service | Added in task-003; normalizes score/label/confidence + batch payloads |

### Backend file map

| Path | Purpose | Notes |
|------|---------|-------|
| `backend/main.py` | FastAPI app, all routes | Large single file — auth, portfolios, assets, sentiment, currency, insurance, pension |
| `backend/models.py` | SQLAlchemy ORM models | User, Portfolio, Asset, AssetPriceHistory, SentimentResult, InsuranceProduct, PensionPlan |
| `backend/schemas.py` | Pydantic v2 schemas | Covers all domains; `UserCreate` validator uses `@validator` (Pydantic v1 syntax) |
| `backend/auth.py` | JWT auth helpers | `create_access_token`, `get_current_user`, `authenticate_user` |
| `backend/config.py` | Pydantic settings | DB URL, JWT secret, Twitter keys |
| `backend/database.py` | Async SQLAlchemy session | Not yet read in detail |
| `backend/twitter_fetcher.py` | Tweepy Twitter client | Fetches tweets by stock symbol; credentials from `.env` |
| `backend/globalSetting.py` | Global state holder | Holds `sentiment_model` reference |
| `backend/alembic/` | DB migrations | Exists |
| `backend/tests/` | Test files | Multiple test files; some duplicated (auth-tests.py vs test_token.py) |

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
- `frontend/src/app/dashboard/data.ts` now exposes `sentiment_trend` alongside the summary sentiment signal, so presentation components can render charts without parsing raw API history.

---

## Likely priorities (updated)
1. Fix AuthContext to use the correct apiClient methods and correct API paths
2. Build portfolio summary cards (task-007)
3. Connect the portfolio detail page to the named apiClient methods
4. Introduce watchlist domain (backend + frontend)
5. Establish historical snapshot plan (task-010)
