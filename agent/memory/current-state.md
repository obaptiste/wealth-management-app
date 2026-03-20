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
| `src/types/portfolio.ts` | Portfolio types (v1) | **Duplicate of portfolios.ts** |
| `src/types/portfolios.ts` | Portfolio types (v2) | **Duplicate of portfolio.ts** — one must be canonical |
| `src/types/auth.ts` | Auth types | `AuthContextType` interface lives here |
| `src/types/chart.ts` | Chart-related types | Not yet inspected |
| `src/types/components.ts` | Component prop types | Not yet inspected |
| `src/types/index.ts` | Barrel re-export | Exports from all type files |
| `src/types/theme.ts` | Theme types | Not yet inspected |
| `src/styles/chakra-tailwind.css` | Chakra + Tailwind bridge | Exists |
| `src/styles/theme.ts` | Chakra theme config | Not yet inspected |

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

### 3. Duplicate type definitions
- `types/portfolio.ts` and `types/portfolios.ts` are nearly identical.
- `PortfolioSummary.last_updated` is `string | undefined` in `portfolio.ts` but required `string` in `portfolios.ts`.
- Both are exported from `types/index.ts` causing likely name collisions.

### 4. No service layer
- `lib/api.ts` is purely a data-access / HTTP client layer.
- No service layer exists for portfolio summary calculations, sentiment normalization, or watchlist signals.
- The backend performs portfolio performance calculations inside API route handlers (not in a service module).

### 5. No sentiment UI
- Backend has a fully-functional FinBERT sentiment analysis pipeline and Twitter fetcher.
- No frontend page or component exists to display sentiment results.

### 6. No watchlist feature
- Architecture docs call for a watchlist domain; nothing exists on frontend or backend.

### 7. CLAUDE.md stack mismatch
- CLAUDE.md lists "Prisma" as the database ORM, but the actual stack uses SQLAlchemy + Alembic.

### 8. Pydantic v1/v2 mixing
- `schemas.py` uses `@validator` (Pydantic v1) inside a Pydantic v2 `BaseModel`.
  This is allowed in compatibility mode but is a known fragility point.

### 9. `config.py` `is_production` is a method but used as a property
- `settings.is_production` is defined as a method `def is_production(self) -> bool` but used as `settings.is_production` (without calling it) in `main.py` conditional expressions.

---

## Likely priorities (updated)
1. Fix AuthContext to use the correct apiClient methods and correct API paths
2. Consolidate duplicate type files (`portfolio.ts` vs `portfolios.ts`)
3. Build service layer for portfolio summary (calculation logic)
4. Connect dashboard and portfolio pages to real API data
5. Build sentiment UI
6. Introduce watchlist domain (backend + frontend)
