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
Add `frontend/src/services/sentiment-trend.ts` as a pure adapter that maps raw history entries into `SentimentChartPoint` values, and expose that adapted series through the dashboard loader.

Reason:
This keeps history normalization and score derivation in one place, avoids leaking backend response details into chart components, and gives future sentiment visualizations a single typed input contract.

Impact:
Any dashboard or watchlist chart can consume `SentimentChartPoint[]` directly. Invalid or partial history rows are filtered or normalized before they reach presentation code.

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
