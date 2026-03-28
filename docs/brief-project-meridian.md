# Project Brief: Project Meridian

**Document ID:** PROJ-004
**Owner:** People & Culture & Engineering
**Status:** Active
**Last Updated:** March 2025

---

## Executive Summary

Project Meridian is a 3-month initiative to redesign and automate the employee onboarding process. The current onboarding process is manual, inconsistent, and time-consuming — averaging 3 hours of IT setup time per new starter and requiring coordination across at least 4 teams. Project Meridian will reduce IT setup time to under 45 minutes and provide new starters with a structured, self-guided onboarding experience from Day 1.

---

## Background

ACME Corporation hires approximately 40 new employees per quarter. The current onboarding process requires:

- IT to manually provision accounts across 6 systems.
- People & Culture to send onboarding documents via email.
- Managers to coordinate inductions individually with no standard structure.
- New starters to navigate multiple systems with minimal guidance, leading to a poor first-week experience.

Exit interviews have identified poor onboarding as a contributing factor in early attrition (within the first 6 months). Project Atlas (`brief-project-atlas.md`) will provide the technical foundation (SSO, automated provisioning) that Meridian will build on.

---

## Objectives

1. **Automated account provisioning** — New starter accounts provisioned across all 6 systems within 2 hours of the employment record being created in the HR system.
2. **Digital onboarding portal** — A structured onboarding checklist and resource hub accessible to new starters from the day they accept their offer.
3. **Manager onboarding toolkit** — Standardised resources and a checklist to help managers run consistent inductions.
4. **30/60/90 day check-ins** — Automated prompts for managers and new starters at 30, 60, and 90 days, with structured questions feeding into People & Culture reporting.

---

## Scope

### In Scope

- Automated provisioning workflow (dependent on Project Atlas SSO layer).
- New starter onboarding portal (built within the Project Atlas employee portal).
- Manager onboarding toolkit (resources, checklist, induction guide).
- 30/60/90 day check-in automation via the HR portal.
- Updated `guide-onboarding.md` and `guide-it-setup.md` documentation.

### Out of Scope

- Changes to the recruitment or offer management process.
- Onboarding for contractors or consultants (Phase 2).
- Learning management system (LMS) integration.

---

## Team

| Role | Name | Responsibility |
|------|------|---------------|
| Project Lead | Rachel Taylor (EMP1018) | Project management, People & Culture alignment |
| Tech Lead | Alex Chen | Portal development, provisioning automation |
| IT Operations | Sam Taylor | Account provisioning workflows |
| UX Designer | Riley Moore | Onboarding portal UX |
| People & Culture | Casey Brown | Onboarding content, manager toolkit |

---

## Timeline

| Milestone | Target Date |
|-----------|------------|
| Current state process mapping complete | April 2025 |
| Automated provisioning workflow live (staging) | May 2025 |
| Onboarding portal MVP delivered | June 2025 |
| Manager toolkit published | June 2025 |
| 30/60/90 day check-ins live | July 2025 |
| Post-launch review | August 2025 |

---

## Dependencies

- **Project Atlas** — Meridian's automated provisioning and onboarding portal are built on the Atlas SSO and employee portal. Atlas must deliver its staging SSO milestone (May 2025) on schedule for Meridian to proceed.
- **HR system data quality** — Automated provisioning requires the employment start date and department to be entered in the HR system at least 5 business days before the start date.

---

## Success Metrics

- IT setup time for new starters < 45 minutes (measured via IT ticket data).
- New starter satisfaction with onboarding experience > 8/10 (measured at 30-day check-in).
- 100% of new starters complete onboarding checklist within first 2 weeks.
- Early attrition rate (< 6 months) reduced by 20% within 2 quarters of launch.

---

## Risks and Mitigations

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|------------|
| Project Atlas delays affect Meridian timeline | High | High | Maintain regular touchpoints with Atlas team; identify manual fallback for provisioning |
| HR data entered late for new starters | Medium | Medium | Implement automated reminder to hiring managers 10 days before start date |
| Manager adoption of toolkit is low | Medium | Medium | Run workshops; make toolkit completion a manager performance objective |
| Onboarding content becomes outdated quickly | Low | Medium | Assign content owners per section with quarterly review cadence |

---

## Related Documents

- Project Atlas Brief: `brief-project-atlas.md`
- New Employee Onboarding Guide: `guide-onboarding.md`
- IT Setup Guide: `guide-it-setup.md`
- HR FAQ: `faq-hr.md`
