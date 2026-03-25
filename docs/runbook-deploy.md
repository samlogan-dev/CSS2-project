# Deployment Runbook

**Document ID:** ENG-RUN-001
**Owner:** Platform Engineering
**Last Updated:** March 2025

---

## Overview

This runbook describes the standard deployment process for all production services. Follow these steps in order. Do not skip steps without explicit approval from the on-call lead.

For incidents that occur during or after deployment, refer to the **Incident Response Runbook** (`runbook-incident-response.md`).

---

## Pre-Deployment Checklist

Before triggering a deployment, confirm all of the following:

- [ ] Pull request has been reviewed and approved by at least 2 engineers.
- [ ] All CI checks are green (unit tests, integration tests, linting).
- [ ] The staging environment has been tested with the same build.
- [ ] A deployment window has been agreed with the on-call engineer.
- [ ] The database migration plan has been reviewed (if applicable). See `runbook-database-backup.md` for backup requirements before migrations.
- [ ] The rollback plan is documented in the PR description.
- [ ] Any dependent services have been notified of the deployment.

---

## Deployment Window

Standard deployment windows are:

- **Weekdays:** 10:00 AM – 12:00 PM AEST or 2:00 PM – 4:00 PM AEST
- **Weekends:** Avoided unless a critical hotfix is required

Emergency deployments outside these windows require on-call lead approval and must be flagged in the `#deployments` Slack channel.

---

## Step-by-Step Deployment Process

### Step 1 — Notify the Team

Post in `#deployments` on Slack:

```
:rocket: Deploying [service-name] v[version] to production
Build: [CI build link]
PR: [PR link]
On-call: @[name]
```

### Step 2 — Tag the Release

```bash
git tag -a v<version> -m "Release v<version>"
git push origin v<version>
```

Versioning follows **Semantic Versioning** (MAJOR.MINOR.PATCH). Patch for bug fixes, minor for new features, major for breaking changes.

### Step 3 — Trigger the Pipeline

Navigate to the CI/CD dashboard and trigger the `deploy-production` pipeline for the tagged commit. Do not deploy from a branch directly.

Monitor the pipeline output in real time. If any stage fails, do not proceed — follow the rollback procedure below.

### Step 4 — Smoke Tests

Once the pipeline completes, run the smoke test suite against production:

```bash
./scripts/smoke-test.sh --env production
```

All smoke tests must pass before marking the deployment as complete. If tests fail, escalate to the on-call lead immediately.

### Step 5 — Monitor Metrics (15 Minutes)

After a successful smoke test, monitor the following dashboards for 15 minutes:

- Error rate: should remain below 0.1%
- P95 latency: should remain within 10% of pre-deployment baseline
- Database connection pool: should not approach limits

Dashboard links are pinned in `#deployments`.

### Step 6 — Close Out

Post in `#deployments`:

```
:white_check_mark: [service-name] v[version] deployed successfully
```

Update the deployment log in Confluence under Engineering > Deployments.

---

## Rollback Procedure

If smoke tests fail or metrics degrade significantly:

1. Immediately notify the on-call lead via Slack and phone.
2. Trigger the `rollback-production` pipeline for the previous stable tag.
3. Confirm the rollback has completed by re-running smoke tests.
4. Post in `#deployments` with the rollback details.
5. Open an incident if users were affected — see `runbook-incident-response.md`.

---

## Hotfix Process

For critical production bugs that cannot wait for a standard deployment window:

1. Create a branch from the latest production tag (not `main`).
2. Apply the minimal fix.
3. Get at least 1 reviewer (2 preferred; 1 is acceptable in a critical P1 situation).
4. Deploy following the same steps above, skipping the deployment window requirement.
5. Merge the hotfix back into `main` after deployment.

---

## Related Documents

- Incident Response Runbook: `runbook-incident-response.md`
- Database Backup Runbook: `runbook-database-backup.md`
