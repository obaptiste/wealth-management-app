# Known Issues (initial backlog feed)

1. Full-stack CI/check orchestration is inconsistent across root/frontend/backend commands.
2. Some runtime flows (auth/watchlist/snapshot scheduling) need end-to-end verification in a realistic environment.
3. Agent memory and task schema were previously inconsistent, making prioritization noisier than necessary.
4. Existing repo contains historical/generated artifacts that can distract from focused PR diffs.
5. Automated checks need clear pass/fail ownership before merge (lint/test/build smoke).
