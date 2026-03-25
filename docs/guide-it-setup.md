# IT Setup Guide

**Document ID:** IT-GUIDE-001
**Owner:** IT Operations
**Last Updated:** February 2025

---

## Overview

This guide covers the initial IT setup for all new employees and for employees setting up a new device. Complete these steps on Day 1 before doing anything else. If you get stuck, contact the IT helpdesk at helpdesk@company.com or via `#it-help` on Slack.

For a broader overview of your first week, see `guide-onboarding.md`.

---

## Step 1 — Unbox and Power On

Power on your company-issued MacBook. Follow the initial macOS setup wizard. When prompted for an Apple ID, skip this step — do not sign in with a personal Apple ID on a company device. The IT helpdesk will configure managed Apple ID access separately if required.

---

## Step 2 — Enrol in Device Management

Your device must be enrolled in our Mobile Device Management (MDM) system before you can access company resources.

1. Open **System Preferences > Privacy & Security > Profiles**.
2. If the company MDM profile is not already installed, visit `mdm.internal/enrol` in Safari.
3. Download and install the enrolment profile.
4. Restart your device when prompted.

After restart, the MDM will automatically install required software in the background. This may take 20–30 minutes. Do not interrupt this process.

---

## Step 3 — Set Up Your Company Email

1. Open **Mail** and click **Add Account**.
2. Select **Microsoft Exchange**.
3. Enter your company email address (firstname.lastname@company.com) and click **Sign In**.
4. You will be redirected to the company SSO login. Use your employee ID and the temporary password from your welcome email.
5. Change your password immediately after first login. Password requirements: minimum 12 characters, at least 1 uppercase, 1 number, 1 special character.

---

## Step 4 — Enable Multi-Factor Authentication (MFA)

MFA is mandatory for all accounts. You will be prompted to set it up on first login.

1. Download the **Microsoft Authenticator** app on your personal or company mobile phone.
2. Follow the prompts to scan the QR code and register your device.
3. Test MFA by logging out and back in.

If you do not have a mobile phone, contact the IT helpdesk for a hardware token alternative.

---

## Step 5 — Install and Configure the VPN

The company VPN (Cisco AnyConnect) is required for accessing all internal systems when working remotely. Even when on-site, some systems require VPN access.

1. Open **Self Service** (installed by MDM) and find **Cisco AnyConnect**.
2. Click **Install**.
3. Once installed, open AnyConnect and enter the VPN gateway: `vpn.company.com`.
4. Log in with your company SSO credentials.

Confirm VPN is working by navigating to `finance.internal/expenses` — this URL is only accessible via VPN.

---

## Step 6 — Set Up Slack

1. Go to `slack.com/downloads` and download the macOS app.
2. Sign in to the workspace: `company.slack.com`.
3. Use your company SSO credentials.
4. Join the following default channels: `#general`, `#announcements`, `#it-help`, `#your-team-channel`.

Your manager will send you an invite to any additional team channels.

---

## Step 7 — Install Core Tools

The following tools are installed automatically by MDM. Verify each is present in your Applications folder:

- Google Chrome (default browser for internal tools)
- 1Password (company password manager — your manager will invite you to the team vault)
- Zoom (video conferencing)
- Microsoft Office (Word, Excel, PowerPoint)

Additional tools specific to your role (e.g., VS Code, Docker, Figma) can be found in **Self Service** or requested via the IT helpdesk.

---

## Step 8 — Set Up 1Password

1. Open 1Password and accept the invite from your manager.
2. Set a strong master password (this is the one password you must not forget or store elsewhere).
3. Install the 1Password browser extension in Chrome.
4. Do not use the browser's built-in password manager — use 1Password exclusively.

---

## Security Requirements

All company devices must comply with the following at all times:

- **Full-disk encryption** (FileVault on Mac) — enabled automatically by MDM.
- **Screen lock** — set to activate after no more than 5 minutes of inactivity.
- **Automatic updates** — do not defer macOS or app updates.
- **No personal software** — do not install software that is not available via Self Service or approved by IT.

When working remotely, additional security requirements apply — see `policy-remote-work.md`.

---

## Getting Help

| Issue | Contact |
|-------|---------|
| Can't log in or MFA issues | helpdesk@company.com / `#it-help` |
| VPN not connecting | helpdesk@company.com |
| Lost or stolen device | Call IT on-call: +61 2 XXXX XXXX (see `faq-it.md`) |
| Software request | Submit via IT portal: `it.internal/requests` |

---

## Related Documents

- New Employee Onboarding Guide: `guide-onboarding.md`
- Remote Work Policy: `policy-remote-work.md`
- IT FAQ: `faq-it.md`
