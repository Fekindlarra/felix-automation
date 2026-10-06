# FASE 14 Production Deployment Runbook

## Pre-Deployment Checklist

### Infrastructure Requirements
- [ ] SSH access to production server
- [ ] Docker & Docker Compose installed (v20.10+)
- [ ] Minimum 4 CPU cores available
- [ ] Minimum 8GB RAM available
- [ ] 50GB free disk space
- [ ] HTTPS certificates configured
- [ ] PostgreSQL 15+ ready
- [ ] Redis 7+ ready
- [ ] Nginx 1.24+ configured

### Configuration
- [ ] `.env.production` file created with all secrets
- [ ] Database credentials set (DB_USER, DB_PASSWORD)
- [ ] JWT_SECRET configured (min 32 characters)
- [ ] SendGrid API key configured
- [ ] Shopify credentials configured
- [ ] Slack webhook URL for notifications
- [ ] Datadog API key configured (optional)

### Code Quality
- [ ] All tests passing locally (pytest -v)
- [ ] Linting passed (pylint, flake8)
- [ ] Security scanning clean (bandit)
- [ ] Code review approved (2+ reviewers)
- [ ] No merge conflicts
- [ ] No uncommitted changes

### Database
- [ ] Migration scripts validated
- [ ] Backup procedure tested
- [ ] Rollback procedure documented
- [ ] Connection pooling configured
- [ ] Query performance checked

### Security
- [ ] SSL/TLS certificates valid
- [ ] Firewall rules configured
- [ ] Rate limiting configured
- [ ] CORS policies set correctly
- [ ] No hardcoded secrets in code
- [ ] Environment variables validated

---

## Deployment Procedure (Step-by-Step)

### Step 1: Pre-Deployment (30 minutes)

```bash
# 1. SSH into production server
ssh -i ~/.ssh/prod-key ubuntu@prod.enbuenamesa.com

# 2. Verify server state
docker compose -f /opt/felix-automation/docker-compose.prod.yml ps
docker system df

# 3. Create backup
cd /opt/felix-automation
./deploy/backup.sh

# 4. Check current logs
docker compose -f docker-compose.prod.yml logs app --tail 50
docker compose -f docker-compose.prod.yml logs nginx --tail 50
```

### Step 2: Deploy Application (15 minutes)

```bash
# 1. Pull latest code
cd /opt/felix-automation
git fetch origin
git checkout production

# 2. Load environment
source .env.production

# 3. Build and deploy
./deploy/deploy.sh production $(git describe --tags)

# 4. Monitor deployment logs
docker compose -f docker-compose.prod.yml logs -f app
```

### Step 3: Verify Deployment (20 minutes)

```bash
# 1. Check application health
curl -v https://enbuenamesa.com/health

# 2. Run smoke tests
docker compose -f docker-compose.prod.yml exec -T app \
    pytest tests/smoke -v

# 3. Check critical APIs
curl -H "Authorization: Bearer $TEST_TOKEN" \
    https://enbuenamesa.com/api/clients

# 4. Monitor WebSocket connections
docker compose -f docker-compose.prod.yml exec -T app \
    python -c "import psutil; print(psutil.net_connections())"

# 5. Check database replication
docker compose -f docker-compose.prod.yml exec -T db \
    psql -U felix_user -d felix_automation -c "SELECT version();"
```

### Step 4: Post-Deployment (10 minutes)

```bash
# 1. Send notification
curl -X POST $SLACK_WEBHOOK \
    -H 'Content-Type: application/json' \
    -d '{"text": "✅ Production deployment completed successfully"}'

# 2. Update status page
curl -X POST https://status.enbuenamesa.com/api/incidents/resolve

# 3. Archive logs
docker compose -f docker-compose.prod.yml logs app > /backups/logs_$(date +%Y%m%d).log

# 4. Monitor for 30 minutes
./deploy/health_check.sh production 30
```

---

## Rollback Procedure

### Automatic Rollback (if deployment fails)

The deployment script automatically rolls back on:
- Failed health checks
- Failed migrations
- Failed smoke tests
- Service startup failures

**Automatic Actions:**
1. Stop new containers
2. Restore previous containers
3. Restore database from latest backup
4. Send alert notification

### Manual Rollback

If automatic rollback fails or you need to manually rollback:

```bash
cd /opt/felix-automation

# 1. Stop current version
docker compose -f docker-compose.prod.yml down

# 2. Find previous backup
ls -lt backups/db_backup_*.sql | head -5

# 3. Restore from backup
BACKUP_FILE=backups/db_backup_20231006_120000.sql
docker compose -f docker-compose.prod.yml up -d db
sleep 10
docker compose -f docker-compose.prod.yml exec -T db \
    psql -U felix_user -d felix_automation < "$BACKUP_FILE"

# 4. Checkout previous version
git checkout previous_tag  # e.g., v14.0.0

# 5. Restart application
docker compose -f docker-compose.prod.yml up -d

# 6. Verify
curl https://enbuenamesa.com/health

# 7. Send notification
curl -X POST $SLACK_WEBHOOK \
    -H 'Content-Type: application/json' \
    -d '{"text": "⚠️ Rollback completed to previous version"}'
```

---

## Incident Response Procedures

### Alert: API Unavailable

**Severity:** CRITICAL | **Time to Resolve:** 5 minutes

**Symptoms:**
- HTTP 503 from API endpoints
- Response time > 2 seconds
- WebSocket connections dropping

**Steps:**
```bash
# 1. Check application status
docker compose -f docker-compose.prod.yml ps app

# 2. Check logs
docker compose -f docker-compose.prod.yml logs app --tail 100 | grep -i error

# 3. Check resource usage
docker stats felix_app_prod

# 4. Restart application
docker compose -f docker-compose.prod.yml restart app

# 5. If restart doesn't fix it, check database
docker compose -f docker-compose.prod.yml logs db --tail 50

# 6. If database issue, escalate to DBA team
```

---

## Monitoring Dashboard

Production monitoring available at:
- **Datadog:** https://app.datadoghq.com/dashboard/felix-prod
- **Status Page:** https://status.enbuenamesa.com

---

## Post-Incident Review

After any incident:

1. Document in GitHub Issues with label `incident`
2. Complete post-mortem within 24 hours
3. Update runbooks based on findings
4. Implement preventive measures
5. Share lessons learned with team

---

**Deployed:** October 6, 2024
**Version:** FASE 14 v1.0.0
