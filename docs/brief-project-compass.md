# Project Brief: Project Compass

**Document ID:** PROJ-004
**Owner:** Product
**Status:** Active
**Last Updated:** March 2025

---

## Executive Summary

Project Compass is a 4-month initiative to launch a self-service customer portal. Currently, all customer account management is handled through a combination of inbound support tickets and manual operations by the Customer Success team. Compass will give customers direct access to manage their accounts, view usage data, update billing information, and raise support requests — reducing operational load on Customer Success and improving customer satisfaction.

---

## Problem Statement

The Customer Success team currently handles an average of 320 support tickets per week. An internal analysis found that 58% of these tickets are self-serviceable — tasks that customers could complete themselves if a portal existed:

| Ticket Category | Weekly Volume | % of Total |
|---|---|---|
| Invoice and billing queries | 72 | 23% |
| Usage and licence queries | 61 | 19% |
| Password reset and access | 48 | 15% |
| Contract and renewal queries | 33 | 10% |
| Technical support (not self-serviceable) | 106 | 33% |

The absence of a self-service channel creates delays for customers (median first response time is 6.2 hours), drives unnecessary ticket volume, and limits the Customer Success team's ability to focus on high-value proactive engagement.

---

## Objectives

1. **Self-service account management** — Customers can view and update their account details, contacts, and billing information without contacting support.
2. **Usage and licence visibility** — Customers can view real-time usage dashboards and licence consumption against their contracted limits.
3. **Invoice and billing portal** — Customers can download invoices, view payment history, and update payment methods.
4. **Integrated support ticketing** — Customers can raise, track, and respond to support tickets through the portal, replacing the current email-only channel.
5. **Reduce self-serviceable ticket volume by 50%** within 3 months of launch.

---

## Scope

### In Scope

- Customer-facing web portal at `account.company.com`.
- SSO via existing identity provider (Azure AD B2C for external users).
- Account and contact management (read/write).
- Usage dashboard (read-only; data sourced from internal analytics platform — see `brief-project-meridian.md`).
- Invoice portal with PDF download and Stripe payment method management.
- Support ticket submission and tracking (integrated with Zendesk).
- Email notifications for ticket updates and invoice availability.

### Out of Scope

- Mobile native app (Phase 2).
- Contract management or e-signature (separate initiative).
- Customer-to-customer community or forum features.
- White-labelling or multi-tenant customisation for enterprise customers (Phase 2).

---

## Team

| Role | Name | Responsibility |
|------|------|---------------|
| Product Manager | Jordan Smith | Roadmap, customer research, stakeholder management |
| Tech Lead | TBD | Architecture, engineering lead |
| Backend Engineer (×2) | TBD | API development, Zendesk and Stripe integration |
| Frontend Engineer | TBD | Portal UI |
| UX Designer | Riley Moore | User research, wireframes, usability testing |
| Customer Success Lead | Dana Okafor | Requirements, UAT, customer communications |
| Security Review | Sam Taylor | Access control, penetration test coordination |

---

## Timeline

| Milestone | Target Date |
|-----------|------------|
| Discovery and UX research complete | April 2025 |
| Architecture and security design approved | April 2025 |
| Account management and billing portal (beta) | June 2025 |
| Usage dashboard and ticket portal (beta) | July 2025 |
| Customer pilot (20 accounts) | July 2025 |
| General availability launch | August 2025 |

---

## Customer Research

UX Designer Riley Moore will conduct 10 moderated user research sessions with current customers in April. Research goals: validate priority features, identify friction points in current support experience, and test early wireframes. A research summary will be circulated to the steering committee before architecture is finalised.

---

## Success Metrics

- Self-serviceable ticket volume reduced by ≥ 50% within 90 days of launch.
- Customer portal adoption: ≥ 70% of active accounts log in within 60 days.
- Customer satisfaction (CSAT) for portal interactions ≥ 4.2 / 5.
- Median support ticket first response time reduced from 6.2 hours to < 2 hours (due to reduced volume).
- Zero P1 security incidents related to customer data access in first 6 months.

---

## Risks and Mitigations

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|------------|
| Low customer adoption | Medium | High | Early pilot with 20 customers; iterate before GA |
| Stripe or Zendesk integration complexity | Medium | Medium | Spike integrations in week 1 of build |
| Customer data exposure via misconfigured access | Low | Critical | Security design review + penetration test before GA |
| Tech lead hiring delayed | High | High | Engage contractor; PM and platform team to cover interim |
| Scope creep from enterprise customer requests | High | Medium | Strict Phase 1 scope; enterprise features logged for Phase 2 |

---

## Governance

Project Compass is sponsored by the Chief Revenue Officer and governed by a fortnightly steering committee: CRO, Head of Product, Head of Engineering, and Head of Customer Success. The project team escalates to Jordan Smith (PM) and the Tech Lead in the first instance.

A security sign-off gate is required before the customer pilot begins. Sam Taylor from IT Operations will coordinate this review and align with Project Sentinel (`brief-project-sentinel.md`) for threat detection coverage of the new portal.

---

## Related Documents

- Project Meridian Brief (usage data source): `brief-project-meridian.md`
- Project Sentinel Brief (security): `brief-project-sentinel.md`
- Project Atlas Brief (SSO infrastructure): `brief-project-atlas.md`
- Incident Response Runbook: `runbook-incident-response.md`
- Deployment Runbook: `runbook-deploy.md`
- IT FAQ: `faq-it.md`
