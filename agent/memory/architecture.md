# Architecture

## Current architectural intent

The app should separate concerns into the following layers:

### 1. Data access layer

Responsible for fetching external or internal data.
Examples:

- market data providers
- sentiment data providers
- database queries

### 2. Service layer

Responsible for normalizing, transforming, and combining data.
Examples:

- sentiment scoring services
- portfolio summary calculations
- watchlist signal generation

### 3. Application layer

Responsible for orchestrating what the UI needs.
Examples:

- dashboard loaders
- server actions
- route-level data composition

### 4. Presentation layer

Responsible for rendering data cleanly.
Examples:

- cards
- tables
- charts
- alerts
- watchlist panels

## Rules

- Keep external API logic out of UI components
- Keep transformation logic out of page files where possible
- Prefer one source of truth for each major domain concept
- Reuse shared types where practical
- Make it easy to replace mock data with real data later

## Candidate domains

- portfolio
- holdings
- watchlist
- sentiment
- market data
- alerts
- historical snapshots
