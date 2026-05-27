# Australian Private Health Insurance Review Refit

This branch refits the original prior authorisation accelerator into an Australian private health insurance demonstration workflow while keeping the existing backend, frontend and multi-agent architecture intact.

## What changed

- Reframed the product from US-style prior authorisation to Australian private hospital pre-admission funding review.
- Updated the UI language from patient / payer terminology to member, policy number, provider identifier, MBS item numbers, hospital admission context and funding review.
- Replaced the sample case with an Australian elective private hospital scenario for knee arthroplasty.
- Updated deterministic demo outputs so `DEMO_MODE=true` produces Australian private health review results without needing Azure, live payer systems or external APIs.
- Tuned the local LLM prompts for Australian private health insurer workflows.
- Updated the procedure validation helper to accept MBS-style numeric item numbers and retain backwards-compatible code formats.

## Demo review lens

The review is designed to surface the kinds of checks an Australian private health insurer, such as a large hospital-cover payer, would typically need to triage before a final human decision:

1. Active member and policy details.
2. Hospital cover and relevant waiting-period context.
3. Provider identifier and proposed hospital context.
4. MBS-style item number alignment.
5. Clinical medical-necessity evidence.
6. Contracted hospital, gap, excess or co-payment context.
7. Prosthesis, implant or device pathway considerations.
8. Missing documentation and human reviewer follow-up items.

## Run locally

```bash
docker compose up --build
```

Then open:

```text
http://localhost:3000
```

The default local path uses `DEMO_MODE=true`, so the app can show a full Australian private health funding review without model keys or live data integrations.

## Important limitation

This repository is a demonstration accelerator only. It does not provide clinical advice, legal advice, benefit advice, claims advice or a binding funding determination. Any production version must integrate with insurer policy, eligibility, hospital contracting, claims, MBS/item, provider, gap scheme and audit systems, and must retain human clinical and policy review before a member-facing outcome is issued.
