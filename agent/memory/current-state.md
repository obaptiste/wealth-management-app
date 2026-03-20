# Current State

## Status
Early-to-mid build stage.

## Known direction
The app is intended to combine portfolio visibility with sentiment-aware analysis and dashboard-style data visualization.

## Current assumptions
- Some frontend/dashboard work already exists or is in progress
- Backend and integration work may still be partial
- Sentiment logic exists in some form but likely needs hardening
- Data contracts may still need normalization and cleanup

## Likely priorities
1. Establish reliable service boundaries
2. Normalize market and sentiment data
3. Make dashboard data loading predictable
4. Add visualizations for time-based changes
5. Reduce build and integration fragility

## Known risks
- Inconsistent API response shapes
- Leaky business logic in UI
- Tight coupling between components and data fetching
- Incomplete schema or migration discipline
- Build failures caused by scattered assumptions
