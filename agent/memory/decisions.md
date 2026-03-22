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
