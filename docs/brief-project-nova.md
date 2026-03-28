# Project Brief: Project Nova

**Document ID:** PROJ-003
**Owner:** Data Science & Engineering
**Status:** Active
**Last Updated:** March 2025

---

## Executive Summary

Project Nova is a 5-month initiative to build and deploy a real-time analytics platform that consolidates operational data from across the business into a single queryable data warehouse. The platform will replace the current fragmented reporting approach — where each department maintains its own spreadsheets and ad hoc SQL queries — with a governed, self-service analytics layer accessible to all department heads.

---

## Background

ACME Corporation currently has no centralised source of truth for operational data. Key business metrics — headcount, project burn rates, IT ticket resolution times, and finance actuals — are tracked independently by each department with no cross-departmental visibility. This has led to:

- Conflicting figures presented at steering committee meetings.
- Inability to identify cross-departmental bottlenecks (e.g., IT ticket backlogs affecting project delivery).
- Significant manual effort consolidating data for monthly board reporting.

Project Nova addresses this by building a governed data warehouse with a self-service reporting layer.

---

## Objectives

1. **Centralised data warehouse** — Ingest data from HR, Finance, IT, and Engineering systems into a single warehouse updated daily.
2. **Self-service dashboards** — Deliver a suite of 10 core dashboards covering headcount, leave, IT operations, project status, and Finance actuals.
3. **Governed data model** — Establish a single definition for key metrics (e.g., "active headcount", "project cost to date") agreed across departments.
4. **Automated board reporting** — Replace the manual monthly board report with an auto-generated PDF exported from the platform.

---

## Scope

### In Scope

- Data ingestion from: HR portal (`hr.internal`), IT ticketing system (`it.internal`), Finance system, and Jira.
- Data warehouse deployment on the company's existing cloud infrastructure.
- 10 core dashboards built in the selected BI tool (Metabase).
- Data governance framework: metric definitions, data dictionary, and refresh schedules.
- Automated monthly board report.

### Out of Scope

- Real-time streaming data (batch ingestion is sufficient for Phase 1).
- Ingestion from Confluence or Slack.
- Predictive analytics or machine learning models (Phase 2).
- External client-facing reporting.

---

## Team

| Role | Name | Responsibility |
|------|------|---------------|
| Project Lead | Isabella Jones (EMP1009) | Project management, stakeholder alignment |
| Data Engineer (×2) | TBD | Pipeline development, warehouse build |
| Analytics Engineer | TBD | Data modelling, metric definitions |
| BI Developer | TBD | Dashboard development in Metabase |
| Finance Rep | Liam Garcia (EMP1012) | Finance data requirements and sign-off |
| People & Culture Rep | Rachel Taylor (EMP1018) | HR data requirements and sign-off |
| IT Rep | Carlos Harris (EMP1029) | IT data access and infrastructure |

---

## Timeline

| Milestone | Target Date |
|-----------|------------|
| Data source audit and architecture design complete | April 2025 |
| Data warehouse deployed to staging | May 2025 |
| Core data pipelines live (HR, IT, Finance) | June 2025 |
| 10 dashboards delivered and signed off | July 2025 |
| Automated board report live | August 2025 |

---

## Success Metrics

- All 4 data sources ingested and refreshed daily with < 2 hour latency.
- 10 dashboards delivered and rated as useful by > 80% of department heads in a post-launch survey.
- Monthly board report preparation time reduced from 8 hours to under 30 minutes.
- Zero conflicting metric definitions across departments at project closeout.

---

## Risks and Mitigations

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|------------|
| Data quality issues in source systems | High | High | Conduct data profiling in discovery; implement data quality checks in pipelines |
| Disagreement on metric definitions | Medium | High | Facilitate metric definition workshops with all department heads in Month 1 |
| Finance system API access delayed | Medium | High | Engage Finance IT lead early; identify manual extract fallback |
| Low adoption of self-service dashboards | Medium | Medium | Run training sessions for department heads; assign dashboard champions per team |

---

## Governance

Project Nova is sponsored by the CTO and Head of Finance. The project team reports to a fortnightly steering committee. Dashboard definitions and metric changes require sign-off from at least two department representatives before deployment.

---

## Related Documents

- Project Atlas Brief: `brief-project-atlas.md`
- IT FAQ: `faq-it.md`
- HR FAQ: `faq-hr.md`
- Incident Response Runbook: `runbook-incident-response.md`
