# Wealth App Project Instructions

## Project purpose

This project is a wealth management app focused on portfolio visibility, sentiment-informed analysis, watchlists, and clear data visualization.

## Primary stack

- Next.js
- TypeScript
- React
- PostgreSQL
- Prisma

## Working principles

- Prefer small, safe, incremental changes
- Keep code readable and well-commented
- Avoid unnecessary abstraction
- Preserve existing architecture unless the task explicitly requires change
- Do not modify unrelated files
- Do not silently change data contracts
- If Prisma schema changes, document the migration impact
- If API shapes change, update all dependent types and consumers
- Prefer server-safe patterns and predictable data flow
- Surface risks clearly instead of hiding uncertainty

## Definition of done

A task is only complete when:

1. The requested behavior is implemented
2. Types are consistent
3. Relevant build or verification steps have been run
4. Important edge cases are noted
5. Memory files are updated
6. Next steps are suggested if work remains

## Coding style

- Use explicit TypeScript types where they improve clarity
- Keep functions small and focused
- Prefer descriptive names over clever names
- Add comments where intent may not be obvious
- Reuse existing utilities before introducing new ones

## Guardrails

- Do not invent market or portfolio data
- Do not fake successful API responses
- Do not mark tasks done without verification
- Do not perform broad refactors while completing a narrow task
