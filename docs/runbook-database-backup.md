# Database Backup and Recovery Runbook

**Document ID:** ENG-RUN-003
**Owner:** Platform Engineering
**Last Updated:** February 2025

---

## Overview

This runbook covers backup procedures, verification, and recovery for all production databases. Backups are a critical prerequisite for any schema migration. Refer to `runbook-deploy.md` for the deployment process that requires pre-migration backups.

---

## Database Inventory

| Database | Type | Environment | Backup Schedule |
|----------|------|-------------|-----------------|
| `app-db-prod` | PostgreSQL 15 | Production | Daily full + hourly WAL |
| `analytics-db-prod` | PostgreSQL 15 | Production | Daily full |
| `app-db-staging` | PostgreSQL 15 | Staging | Daily full |

---

## Automated Backups

### Schedule

Automated backups are managed by the `db-backup` service running in Kubernetes. The schedule is:

- **Full backup:** 2:00 AM AEST daily
- **WAL archiving (app-db-prod only):** Continuous, with files shipped to S3 every 5 minutes

### Storage

Backups are stored in the `company-db-backups` S3 bucket in `ap-southeast-2`:

```
s3://company-db-backups/
├── app-db-prod/
│   ├── full/YYYY-MM-DD/
│   └── wal/YYYY-MM-DD/HH/
└── analytics-db-prod/
    └── full/YYYY-MM-DD/
```

Retention policy: 30 days for full backups, 7 days for WAL archives.

### Monitoring

Backup success is monitored via Datadog. Alerts are sent to `#alerts-database` in Slack if a scheduled backup fails or takes more than 2 hours. Investigate immediately — a missed backup means the recovery point objective (RPO) is at risk.

---

## Manual Backup (Pre-Migration)

Before any schema migration, a manual full backup is required. This is a hard requirement in the pre-deployment checklist (`runbook-deploy.md`).

```bash
# Set environment variables
export DB_HOST=app-db-prod.internal
export DB_NAME=appdb
export BACKUP_BUCKET=company-db-backups
export TIMESTAMP=$(date +%Y%m%d-%H%M%S)

# Run the backup
pg_dump -h $DB_HOST -U backup_user -Fc $DB_NAME \
  > /tmp/pre-migration-$TIMESTAMP.dump

# Upload to S3
aws s3 cp /tmp/pre-migration-$TIMESTAMP.dump \
  s3://$BACKUP_BUCKET/app-db-prod/pre-migration/$TIMESTAMP.dump

# Verify the upload
aws s3 ls s3://$BACKUP_BUCKET/app-db-prod/pre-migration/$TIMESTAMP.dump
```

Record the backup S3 path in the deployment PR before proceeding.

---

## Backup Verification

Backups should be verified monthly using the following process:

1. Spin up a temporary PostgreSQL instance in the staging VPC.
2. Restore the latest full backup to it.
3. Run the verification script: `./scripts/db-verify.sh --env restored`
4. Confirm row counts match expectations (script outputs a summary).
5. Terminate the temporary instance.

Document verification results in the `#platform-engineering` channel.

---

## Point-in-Time Recovery (PITR)

For `app-db-prod`, WAL archiving enables recovery to any point in the last 7 days.

### When to Use PITR

Use PITR when:
- Data corruption has occurred and the exact time of corruption is known.
- An accidental data deletion or destructive migration must be reversed.

### PITR Procedure

1. Declare an incident first — see `runbook-incident-response.md`.
2. Identify the target recovery time (just before the corruption event).
3. Notify the on-call lead and get explicit approval before proceeding.
4. Restore the base backup closest to the target time:
   ```bash
   aws s3 sync s3://company-db-backups/app-db-prod/full/YYYY-MM-DD/ /restore/base/
   ```
5. Configure `recovery.conf` with the target time:
   ```
   restore_command = 'aws s3 cp s3://company-db-backups/app-db-prod/wal/%f %p'
   recovery_target_time = 'YYYY-MM-DD HH:MM:SS+10'
   recovery_target_action = 'promote'
   ```
6. Start PostgreSQL in recovery mode and monitor logs.
7. Validate the recovered data before switching production traffic.

---

## Recovery Time Objectives

| Scenario | Target RTO |
|----------|-----------|
| Full restore from daily backup | < 2 hours |
| PITR recovery | < 4 hours |
| Schema migration rollback | < 30 minutes |

---

## Related Documents

- Deployment Runbook: `runbook-deploy.md`
- Incident Response Runbook: `runbook-incident-response.md`
