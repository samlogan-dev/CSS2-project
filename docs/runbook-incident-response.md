# Incident Response Runbook

**Document ID:** ENG-RUN-002
**Owner:** Platform Engineering
**Last Updated:** March 2025

---

## Overview

This runbook defines the process for detecting, escalating, and resolving production incidents. An incident is any unplanned interruption to a service that affects users or internal operations.

---

## Severity Levels

| Level | Name | Description | Response SLA |
|-------|------|-------------|--------------|
| P1 | Critical | Complete service outage or data loss | 15 minutes |
| P2 | High | Major feature unavailable, significant user impact | 30 minutes |
| P3 | Medium | Partial degradation, workaround exists | 2 hours |
| P4 | Low | Minor issue, cosmetic or edge case | Next business day |

---

## Detection

Incidents may be detected via:

- **Automated alerting** — PagerDuty alerts from monitoring systems.
- **User reports** — via support ticket, Slack `#incidents`, or direct messages.
- **Engineering observation** — during a deployment (see `runbook-deploy.md`) or code review.

All potential incidents must be logged, even if they resolve automatically.

---

## Incident Response Process

### Step 1 — Declare the Incident

When you detect or suspect a P1 or P2 issue:

1. Post in `#incidents` on Slack with the template below.
2. Page the on-call engineer via PagerDuty if they have not already responded.

```
:fire: INCIDENT DECLARED
Severity: P[1/2]
Service: [affected service]
Summary: [brief description]
Impact: [number of users/teams affected]
Declared by: @[your name]
```

### Step 2 — Assign an Incident Commander

The on-call lead assigns an **Incident Commander (IC)** and a **Communications Lead**:

- **IC** — coordinates the technical response, owns the incident channel.
- **Comms Lead** — handles internal and external communications, updates the status page.

For P3/P4 incidents, an IC is optional but the issue must still be tracked.

### Step 3 — Create an Incident Channel

Create a Slack channel named `#inc-YYYY-MM-DD-[brief-slug]`. All incident communication happens here. Do not conduct incident work in DMs.

### Step 4 — Investigate and Mitigate

The IC coordinates investigation:

1. Establish a timeline of when the issue started and what changed.
2. Check recent deployments — see `runbook-deploy.md` for rollback procedures.
3. Check database health — see `runbook-database-backup.md` for DB-related issues.
4. Identify the mitigation (rollback, feature flag toggle, config change, hotfix).
5. Apply mitigation and confirm resolution via smoke tests and metric monitoring.

Post updates to the incident channel every 15 minutes for P1, every 30 minutes for P2.

### Step 5 — Resolve the Incident

When the service is restored:

1. Post the resolution in `#incidents`:
   ```
   :white_check_mark: INCIDENT RESOLVED
   Service: [service name]
   Duration: [start time] – [end time]
   Root cause: [brief summary]
   IC: @[name]
   ```
2. Update the status page to reflect resolution.
3. Close the PagerDuty alert.
4. Archive the incident channel after the post-mortem is complete.

---

## Post-Mortem

A post-mortem is required for all P1 and P2 incidents. It must be completed within **3 business days** of resolution.

### Post-Mortem Template

- **Incident summary** — what happened and what was the impact?
- **Timeline** — when was it detected, escalated, mitigated, and resolved?
- **Root cause** — what was the underlying cause?
- **Contributing factors** — what conditions allowed this to happen?
- **What went well?**
- **What could be improved?**
- **Action items** — specific, assigned, time-bound tasks to prevent recurrence.

Post-mortems are blameless. The goal is systemic improvement, not individual fault. All post-mortems are published in the Engineering Confluence space.

---

## Escalation Contacts

| Role | Contact |
|------|---------|
| On-call engineer | PagerDuty rotation |
| Engineering Manager | manager@company.com |
| Head of Engineering | head-eng@company.com |
| Customer Support Lead | support-lead@company.com |

---

## Related Documents

- Deployment Runbook: `runbook-deploy.md`
- Database Backup Runbook: `runbook-database-backup.md`
