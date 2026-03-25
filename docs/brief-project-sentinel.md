# Project Brief: Project Sentinel

**Document ID:** PROJ-002
**Owner:** Platform Engineering & Security
**Status:** Active
**Last Updated:** February 2025

---

## Executive Summary

Project Sentinel is a 4-month security uplift initiative focused on strengthening the company's detection and response capabilities. The project will implement centralised log aggregation, automated threat detection, and a formal Security Incident Response process that integrates with the existing Engineering Incident Response process.

---

## Background

A recent external security audit identified three critical gaps:

1. **No centralised logging** — Application, infrastructure, and access logs are stored in silos across multiple systems, making it difficult to correlate events during an incident.
2. **No automated threat detection** — The company relies on manual review of alerts, which is not scalable and introduces significant detection delays.
3. **Undefined security incident process** — The Engineering Incident Response Runbook (`runbook-incident-response.md`) covers service availability incidents but does not address security-specific scenarios (e.g., credential compromise, data exfiltration).

Project Sentinel addresses all three gaps.

---

## Objectives

1. **Centralised SIEM** — Deploy a Security Information and Event Management (SIEM) system that ingests logs from all production systems, the VPN, and identity providers.
2. **Automated threat detection** — Implement detection rules for the top 10 threat scenarios identified in the audit (credential stuffing, unusual data access, lateral movement, etc.).
3. **Security incident playbooks** — Develop and publish playbooks for the top 5 security incident types, integrated into the existing incident response process.
4. **24/7 alerting** — Extend the existing PagerDuty on-call rotation to include security alerts.

---

## Scope

### In Scope

- SIEM deployment (selected vendor: Elastic Security).
- Log ingestion from: production Kubernetes clusters, PostgreSQL databases (`runbook-database-backup.md` covers DB access audit logging), VPN gateway, Azure AD (identity provider), and GitHub.
- Detection rule development for the 10 audit-identified scenarios.
- Security incident playbooks (credential compromise, data breach, ransomware, insider threat, phishing response).
- Training for on-call engineers on security incident response.

### Out of Scope

- Penetration testing (a separate engagement, scheduled for Q4 2025).
- Application-level security changes (WAF, SAST/DAST tooling) — covered in a separate backlog.
- Physical security.

---

## Team

| Role | Name | Responsibility |
|------|------|---------------|
| Project Lead | Morgan Lee | Project management, stakeholder comms |
| Security Engineer (×2) | TBD | SIEM deployment, rule development |
| Platform Engineer | Alex Chen | Log pipeline, infrastructure integration |
| IT Operations | Sam Taylor | VPN and identity provider integration |
| Legal / Compliance | Jamie Wu | Data handling requirements, audit evidence |

---

## Timeline

| Milestone | Target Date |
|-----------|------------|
| SIEM deployed to staging | March 2025 |
| Log ingestion from all sources live | April 2025 |
| Detection rules deployed | May 2025 |
| Security playbooks published | May 2025 |
| On-call training complete | June 2025 |
| Project closeout and audit review | July 2025 |

---

## Integration with Existing Processes

### Incident Response

Security incidents will be declared and managed using the same framework as service incidents — see `runbook-incident-response.md`. Security incidents will use the same severity levels (P1–P4) and the same incident channel and post-mortem process.

Security-specific additions:
- The Comms Lead must notify Legal within 30 minutes of a P1 security incident.
- If a data breach is suspected, Legal will determine whether regulatory notification is required.
- Post-mortems for security incidents are marked **confidential** and shared only with the steering committee.

### Deployment and Change Management

SIEM configuration changes will follow the standard deployment process in `runbook-deploy.md`. Detection rule changes are lower risk and can be deployed outside standard windows with on-call approval.

---

## Success Metrics

- Mean Time to Detect (MTTD) for the 10 target threat scenarios < 15 minutes.
- 100% of production log sources ingested into SIEM.
- All 5 security playbooks published and reviewed by Legal.
- Zero critical findings in follow-up audit (Q4 2025).

---

## Risks and Mitigations

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|------------|
| High false positive rate in detection rules | High | Medium | Tune rules in staging for 4 weeks before production |
| Log volume exceeds SIEM capacity | Medium | High | Size cluster based on 2× current log volume; set alerts |
| Security engineer hiring delayed | High | High | Engage a specialist contractor as interim measure |
| Regulatory notification triggered during testing | Low | High | Use synthetic data in staging; document test periods |

---

## Related Documents

- Incident Response Runbook: `runbook-incident-response.md`
- Deployment Runbook: `runbook-deploy.md`
- Database Backup Runbook: `runbook-database-backup.md`
- IT FAQ: `faq-it.md`
