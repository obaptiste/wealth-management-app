# Historical Snapshot Plan

## Goal

Provide a stable way to chart and compare:

- portfolio value over time
- allocation drift over time
- holding-level value changes over time
- sentiment changes over time

without forcing the UI to reconstruct history from volatile live market calls.

## Current inputs

### Already available

- `AssetPriceHistory` stores point-in-time prices for individual assets
- `SentimentResult` stores timestamped raw sentiment results per symbol
- frontend types already include `PortfolioSnapshot` and `HistoricalSnapshotPoint`
- dashboard and watchlist loaders already consume chart-ready sentiment adapters

### Current gaps

- No persisted portfolio-level snapshot exists
- `AssetPriceHistory` is only written opportunistically when assets are created or fetched
- Sentiment history is derived live from raw `SentimentResult` rows each request
- No single "as of" record exists for an entire portfolio state on a given date

## Recommended model

### 1. Persist portfolio-level snapshots

Add a dedicated portfolio snapshot table as the canonical historical source for portfolio charts.

Recommended shape:

- `portfolio_snapshots`
- `id`
- `portfolio_id`
- `snapshot_date`
- `total_value`
- `total_cost`
- `total_profit_loss`
- `total_profit_loss_percent`
- `asset_count`
- `captured_at`

Rules:

- one row per portfolio per day
- uniqueness on `(portfolio_id, snapshot_date)`
- `snapshot_date` should represent the business date; `captured_at` records when the row was actually written

Why:

- portfolio charts should read from one stable aggregate table, not recompute from current holdings plus live prices
- one-row-per-day keeps queries simple and storage predictable

### 2. Persist holding-level snapshot rows under the portfolio snapshot

Add a child table for allocation and holding breakdowns on the same snapshot date.

Recommended shape:

- `portfolio_snapshot_holdings`
- `id`
- `portfolio_snapshot_id`
- `asset_id`
- `symbol`
- `quantity`
- `price`
- `current_value`
- `allocation_percent`
- `total_cost`
- `profit_loss`
- `profit_loss_percent`

Rules:

- rows are written together with the parent portfolio snapshot
- symbol is denormalized into the row so charts remain readable even if the source asset changes later

Why:

- this supports allocation-over-time views and "what changed" comparisons
- it avoids replaying historical prices against today’s asset list

### 3. Keep sentiment history derived from raw sentiment rows for now

Do not add a separate persisted sentiment snapshot table in the first iteration.

Use `SentimentResult` as the source of truth and aggregate it by symbol and day, which is already how `/sentiment/history/{symbol}` behaves today.

Why:

- the current sentiment model already produces append-only event data
- daily aggregation can be done deterministically from raw rows
- adding another sentiment snapshot table now would duplicate information without a clear product need

## Storage direction

### Portfolio history direction

Persist daily portfolio snapshots in the application database.

Write path:

1. load current assets for a portfolio
2. resolve current prices for those assets
3. compute aggregate portfolio summary
4. upsert one `portfolio_snapshots` row for `snapshot_date`
5. replace or upsert the child `portfolio_snapshot_holdings` rows for that parent snapshot

Trigger direction:

- preferred long-term: scheduled daily job
- acceptable short-term fallback: snapshot-on-read with daily upsert guard

Recommendation:

- start with a daily scheduled snapshot job
- allow an idempotent manual backfill command for existing portfolios

### Sentiment history direction

Keep storing raw `SentimentResult` events.

Read path:

- continue aggregating by symbol and day for chart APIs
- if query cost becomes a problem later, introduce a derived materialized/daily summary table

## API direction

### Portfolio chart API

Add a dedicated endpoint that reads from persisted portfolio snapshots, not live holdings.

Recommended response:

- `portfolio_id`
- `from`
- `to`
- `points: HistoricalSnapshotPoint[]`

Each point:

- `as_of`
- `portfolio_value`
- optional `sentiment_score` only if the product explicitly wants a combined portfolio-level overlay

### Allocation comparison API

Add a second endpoint for detailed snapshot comparisons when needed.

Recommended shape:

- current snapshot summary
- previous snapshot summary
- holding deltas by symbol

Do not overload the existing dashboard loader with snapshot-comparison logic.

## Mock vs persistent trade-offs

### Mock-only approach

Pros:

- fast to prototype
- no schema work
- no scheduler needed

Cons:

- history changes every time live data changes
- impossible to explain "what the portfolio looked like last Tuesday"
- not trustworthy for user-facing performance charts

Conclusion:

- acceptable for local demos only
- not acceptable as the long-term product direction

### Persistent portfolio snapshots

Pros:

- stable chart data
- supports day-over-day comparison
- supports auditability and user trust
- keeps frontend loaders simple

Cons:

- requires schema and background-write logic
- backfill strategy is needed for existing portfolios
- price resolution failures need explicit handling

Conclusion:

- this is the recommended production direction

### Persisted sentiment snapshots

Pros:

- potentially faster chart queries
- easier to precompute daily symbol summaries

Cons:

- duplicates information already present in `SentimentResult`
- adds another write path and reconciliation burden

Conclusion:

- defer until raw-row aggregation becomes too slow or too expensive

## Capture rules

### Portfolio snapshot capture

- capture at most once per portfolio per day
- if the job reruns on the same day, upsert the parent row and replace child holding rows
- if a price cannot be fetched for one holding, store the snapshot with a clear fallback rule rather than skipping the whole portfolio

Recommended fallback:

- use the most recent known `AssetPriceHistory` price for that asset
- if none exists, fall back to purchase price and mark the snapshot as degraded in logs

### Sentiment aggregation

- aggregate by UTC day for consistency with existing backend timestamps
- keep the frontend adapters date-only at the chart boundary

## Rollout plan

### Phase 1

- document the model and API direction
- keep current dashboard sentiment history unchanged

### Phase 2

- add `portfolio_snapshots` and `portfolio_snapshot_holdings`
- add daily snapshot writer/backfill command

### Phase 3

- add portfolio snapshot read endpoint
- switch portfolio value charts to snapshot-backed data

### Phase 4

- add allocation comparison views if the product needs them
- evaluate whether sentiment daily summaries need persistence

## Recommended next implementation task

Implement the portfolio snapshot persistence layer first.

That is the smallest durable step that unlocks:

- historical portfolio charts
- allocation drift analysis
- clearer dashboard comparisons
- future reporting exports
