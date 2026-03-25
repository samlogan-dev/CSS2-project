# IT Frequently Asked Questions

**Document ID:** IT-FAQ-001
**Owner:** IT Operations
**Last Updated:** February 2025

---

## General

### How do I contact IT support?

- **Slack:** `#it-help` (fastest response during business hours)
- **Email:** helpdesk@company.com
- **Phone (after-hours, urgent only):** +61 2 XXXX XXXX
- **Portal:** `it.internal/requests` (for non-urgent requests and tracking ticket status)

Response SLAs: urgent issues (account lockouts, device loss) — 1 hour. Standard requests — 1 business day.

### What is covered by IT support?

IT supports all company-issued hardware and software, and any personal devices used to access company systems. IT does not support personal software or personal use of devices.

---

## Account and Access

### I forgot my password / I'm locked out of my account.

Contact the IT helpdesk immediately via Slack (`#it-help`) or phone. Do not attempt to reset your password more than 3 times — repeated failures will lock your account and require manual intervention.

For initial setup of your account and MFA, refer to `guide-it-setup.md`.

### How do I request access to a new system or tool?

Submit a request via the IT portal at `it.internal/requests`. Include the system name, the business justification, and your line manager's approval (attach an email or screenshot). Access requests typically take 1–2 business days.

### I need to share access to a system with a contractor or vendor.

Contractors and vendors must have their own accounts — sharing company accounts is a security policy violation. Contact the IT helpdesk to provision a temporary account for external parties. The request must be approved by a Director.

---

## Devices and Hardware

### My laptop is running slowly / crashing.

First steps:
1. Restart the device.
2. Check for pending macOS updates (do not defer these — see `guide-it-setup.md`).
3. If the issue persists, log a ticket at `it.internal/requests` with a description of the problem.

Do not attempt to reinstall macOS or perform your own hardware repairs — this voids the device warranty and may violate MDM policy.

### I've lost or had my device stolen. What do I do?

**Immediately** contact IT on the after-hours line: +61 2 XXXX XXXX. Do not wait until business hours. IT will remotely wipe the device and revoke credentials. You must also report the loss to your line manager within 1 hour.

If the device was stolen, file a police report and provide the report number to IT and People & Culture.

### Can I use my personal laptop for work?

Personal devices may only be used for work if they meet the security requirements in `policy-remote-work.md`. Before using a personal device, contact IT to have it assessed and approved. Unapproved personal devices must not connect to internal systems or store company data.

### How do I get a replacement device?

Replacement devices are issued when:
- Your device is beyond repair (confirmed by IT).
- Your device is lost or stolen (see above).
- You are due for a hardware refresh (typically every 3 years).

Submit a request via `it.internal/requests` with the reason for replacement.

---

## VPN and Remote Access

### The VPN is not connecting. What should I do?

1. Check your internet connection.
2. Ensure Cisco AnyConnect is up to date.
3. Try disconnecting and reconnecting.
4. If MFA is failing, ensure your authenticator app is synced to the correct time.
5. If still failing, contact the helpdesk via email or phone (VPN issues prevent Slack access).

### Do I need to use the VPN when I'm in the office?

Some internal systems (e.g., `finance.internal`, `hr.internal`) require VPN even on-site. As a general practice, keeping the VPN connected at all times is recommended and causes minimal performance impact.

---

## Software and Tools

### How do I install new software?

First check **Self Service** (installed on your Mac) — many approved tools are available there without needing IT approval. For anything not in Self Service, submit a request at `it.internal/requests`.

Do not download and install software from the internet without IT approval. Unapproved software that creates a security risk may be remotely removed by IT.

### My software licence has expired / I'm getting a licence error.

Contact the IT helpdesk with the software name and the error message. Do not attempt to use personal licences for company software.

---

## Security

### I received a suspicious email. What should I do?

Do not click any links or open attachments. Forward the email to security@company.com and then delete it. If you believe you have already clicked a link or provided credentials, contact the IT helpdesk immediately — this is treated as a potential security incident.

### I think my account has been compromised.

Contact the IT helpdesk immediately via phone (+61 2 XXXX XXXX). This is treated as a P1 security incident. IT will revoke your credentials, investigate, and re-provision your access. See `runbook-incident-response.md` for how security incidents are managed.

---

## Related Documents

- IT Setup Guide: `guide-it-setup.md`
- New Employee Onboarding Guide: `guide-onboarding.md`
- Remote Work Policy: `policy-remote-work.md`
- Incident Response Runbook: `runbook-incident-response.md`
