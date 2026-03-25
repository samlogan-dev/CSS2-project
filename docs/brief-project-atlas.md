# Project Brief: Project Atlas

**Document ID:** PROJ-001
**Owner:** Product & Engineering
**Status:** Active
**Last Updated:** March 2025

---

## Executive Summary

Project Atlas is a 6-month initiative to replace the company's fragmented internal tooling with a unified employee portal. The portal will consolidate HR, IT, Finance, and Engineering workflows into a single authenticated interface, reducing context switching and improving data consistency across departments.

---

## Problem Statement

Currently, employees must navigate at least 6 separate systems to complete routine administrative tasks:

- `hr.internal` — leave and payroll
- `finance.internal/expenses` — expense claims
- `it.internal/requests` — IT support and software requests
- Jira — project and task tracking
- Confluence — internal documentation
- Slack — communication (with bots providing partial automation)

The fragmentation causes:
- High cognitive load for employees, particularly new starters (see `guide-onboarding.md` for current onboarding complexity).
- Duplicate data entry across systems, leading to inconsistencies (e.g., address changes must be updated in 3 separate systems).
- Difficulty for IT and People & Culture teams to get a single view of an employee's access, status, and history.

---

## Objectives

1. **Unify authentication** — Single Sign-On (SSO) across all systems by Q3 2025.
2. **Consolidated employee portal** — A single web app at `portal.company.com` that surfaces the most common workflows from all 6 systems.
3. **Reduce onboarding IT setup time** — From the current average of 3 hours to under 45 minutes (see `guide-it-setup.md` for the current process that Atlas will streamline).
4. **Improve data consistency** — Personal detail changes propagate automatically to all integrated systems within 24 hours.

---

## Scope

### In Scope

- SSO integration for HR, IT, Finance, and Jira systems.
- Employee self-service portal (leave requests, expense submissions, IT ticket logging).
- Automated account provisioning and deprovisioning for new and departing employees.
- Manager dashboard for leave approvals and team access overview.
- API integration with existing systems (read/write where required).

### Out of Scope

- Replacement of the underlying HR, Finance, or IT systems (these remain as backends).
- Mobile native app (web responsive is sufficient for Phase 1).
- External client or vendor access.

---

## Team

| Role | Name | Responsibility |
|------|------|---------------|
| Product Manager | Jordan Smith | Roadmap, stakeholder management |
| Tech Lead | Alex Chen | Architecture, engineering lead |
| Backend Engineer (×2) | TBD | API development, SSO integration |
| Frontend Engineer | TBD | Portal UI |
| UX Designer | Riley Moore | User research, design system |
| IT Operations Rep | Sam Taylor | IT system integration, security review |
| People & Culture Rep | Casey Brown | HR system integration, policy alignment |

---

## Timeline

| Milestone | Target Date |
|-----------|------------|
| Discovery and architecture complete | April 2025 |
| SSO integration live (staging) | May 2025 |
| Employee portal MVP (internal beta) | June 2025 |
| Full rollout with onboarding automation | August 2025 |

---

## Success Metrics

- Average IT setup time for new starters < 45 minutes (measured via onboarding survey).
- Data consistency rate > 99% across integrated systems (measured by quarterly audit).
- Employee satisfaction score for internal tools > 7/10 (measured via quarterly survey).
- IT helpdesk ticket volume for account/access issues reduced by 40%.

---

## Risks and Mitigations

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|------------|
| Legacy system APIs insufficient | Medium | High | Conduct API audit in Discovery phase |
| SSO rollout disrupts existing access | Medium | High | Phased rollout with parallel access period |
| Low adoption of new portal | Low | Medium | Involve HR and IT in UX design; comms plan |
| Timeline slippage due to hiring | High | Medium | Begin recruitment immediately; scope MVP tightly |

---

## Governance

The project is governed by a steering committee that meets fortnightly: Head of Engineering, Head of People & Culture, Head of Finance, and CTO. Escalations from the project team go to the Tech Lead and Product Manager in the first instance, then to the steering committee if unresolved.

---

## Related Documents

- IT Setup Guide: `guide-it-setup.md`
- New Employee Onboarding Guide: `guide-onboarding.md`
- IT FAQ: `faq-it.md`
