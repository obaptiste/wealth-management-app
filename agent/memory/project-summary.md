# Project Summary

## Product
Wealth management application with a Next.js frontend and FastAPI backend for portfolio tracking, sentiment analysis, watchlist monitoring, and historical snapshots.

## Primary goals
- Give users accurate portfolio visibility and trend context.
- Combine portfolio data with sentiment signals in a clear dashboard UX.
- Keep backend contracts explicit and strongly typed on the frontend.
- Ship in small, reviewable increments with verification.

## Tech stack
- Frontend: Next.js App Router, React, TypeScript, Chakra UI.
- Backend: FastAPI, SQLAlchemy, Alembic, PostgreSQL.
- Tooling: ESLint, TypeScript compiler, Pytest, Docker Compose.

## Delivery constraints
- Preserve server/client boundaries (server-first, `"use client"` only when needed).
- Keep database access in backend/server-side code only.
- Never commit secrets or `.env` files.
- Prefer narrow PRs tied to one task ID at a time.
