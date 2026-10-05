# 🚀 DEPLOYMENT READINESS - FASE 13

**Status:** ✅ READY FOR PRODUCTION  
**Release Version:** v13.0.0  
**Date:** 2026-10-05  
**Deployment Window:** Flexible (backward compatible, no downtime required)

---

## 📋 Pre-Deployment Checklist

### 1. Infrastructure Requirements
- [ ] Linux/macOS server or container
- [ ] Python 3.11+ installed
- [ ] 2GB+ RAM available
- [ ] 500MB+ disk space for logs/data
- [ ] Internet access for API calls (Facebook, Google, SendGrid)

### 2. External APIs - Configuration Required

#### Facebook Ads API
- [ ] **App Created** at developers.facebook.com
  - App ID: `______________`
  - App Secret: `______________`
  
- [ ] **OAuth Token Obtained**
  - User Access Token: `______________`
  - Business Account ID: `______________`
  
- [ ] **Scopes Authorized** (required):
  - `ads_management` ✓
  - `ads_read` ✓
  - `business_management` ✓

**Test Connection:**
```bash
python -c "
from whitebox.facebook_ads_live_auditor import FacebookAdsLiveAuditor
auditor = FacebookAdsLiveAuditor(None)
result = auditor.validate_token('YOUR_TOKEN_HERE')
print(f'✅ Valid' if result else '❌ Invalid')
"
```

#### Google Ads API
- [ ] **Project Created** at console.cloud.google.com
  - Project ID: `______________`
  - Developer Token: `______________`
  
- [ ] **OAuth Credentials Set Up**
  - Client ID: `______________`
  - Client Secret: `______________`
  
- [ ] **Required APIs Enabled**:
  - Google Ads API ✓
  - Google Analytics API ✓ (optional, for enhanced metrics)

**Test Connection:**
```bash
python -c "
from whitebox.google_ads_live_auditor import GoogleAdsLiveAuditor
auditor = GoogleAdsLiveAuditor(None)
result = auditor.validate_credentials('TOKEN', 'CUSTOMER_ID')
print(f'✅ Valid' if result else '❌ Invalid')
"
```

#### SendGrid API
- [ ] **Account Created** at sendgrid.com
  - API Key: `SG.xxxxxxxxxxxxxxxxxxxx`
  - Verified Sender Email: `noreply@enbuenamesa.com`
  
- [ ] **Webhooks Configured** (for tracking):
  - Endpoint URL: `https://your-domain.com/webhooks/sendgrid`
  - Events: Bounces, Opens, Clicks, Unsubscribes

**Test Connection:**
```bash
python -c "
from agents.email_sender_agent import EmailSenderAgent
sender = EmailSenderAgent(None)
result = sender.test_connection('YOUR_API_KEY')
print(f'✅ Connected' if result else '❌ Failed')
"
```

### 3. Environment Configuration

**Create `.env` file** (from `.env.example`):
```bash
cp .env.example .env
```

**Edit `.env` with production values:**
```bash
# Database
DATABASE_PATH=./data/felix.db
# Or for PostgreSQL:
DATABASE_URL=postgresql://user:pass@host:5432/felix

# Facebook Ads
FACEBOOK_APP_ID=your_app_id
FACEBOOK_APP_SECRET=your_app_secret
FACEBOOK_ACCESS_TOKEN=your_access_token
FACEBOOK_BUSINESS_ID=your_business_id

# Google Ads
GOOGLE_DEVELOPER_TOKEN=your_developer_token
GOOGLE_CLIENT_ID=your_client_id
GOOGLE_CLIENT_SECRET=your_client_secret

# SendGrid
SENDGRID_API_KEY=SG.xxxxxxxxxxxxxxxxxxxx
SENDGRID_FROM_EMAIL=noreply@enbuenamesa.com
SENDGRID_FROM_NAME=Felix Automation

# Security
WHITEBOX_MASTER_KEY=generate_random_secure_key_here
WHITEBOX_TTL_SECONDS=3600  # 1 hour

# Flask (backend)
FLASK_ENV=production
FLASK_DEBUG=false
SECRET_KEY=generate_random_secret_key_here

# Logging
LOG_LEVEL=INFO
LOG_PATH=./data/logs

# Optional: Error tracking
SENTRY_DSN=https://your-sentry-dsn@sentry.io/project

# Optional: Analytics
SEGMENT_WRITE_KEY=your_segment_key
```

### 4. Database Setup

**Initialize/Migrate Database:**
```bash
# SQLite (default)
python scripts/init_db.py

# PostgreSQL (if using)
python scripts/migrate_to_postgresql.py
```

**Verify Schema:**
```bash
python -c "
from orchestrator import FelixAutomationOrchestrator
orch = FelixAutomationOrchestrator()
orch.connect_database()
tables = orch.get_database_status()
print('✅ Database ready' if tables['status'] == 'ready' else '❌ Issues found')
print(tables)
"
```

### 5. Dependencies Installation

```bash
# Install/upgrade all requirements
pip install -r requirements.txt --upgrade

# Verify installations
python -c "
import facebook_business
import google.ads.googleads.client
import sendgrid
import reportlab
import weasyprint
import cryptography
print('✅ All dependencies installed')
"
```

### 6. Application Startup Test

**Run Health Check:**
```bash
python -c "
from orchestrator import FelixAutomationOrchestrator
orch = FelixAutomationOrchestrator()
orch.connect_database()
status = orch.get_system_status()

# Check all systems
assert status['database'] == 'connected'
assert status['agents'] >= 7
print('✅ All systems operational')
print(f'Database: {status[\"database\"]}')
print(f'Agents loaded: {status[\"agents\"]}')
"
```

**Load All Agents:**
```bash
python -c "
from agents.multi_platform_auditor_agent import MultiPlatformAuditorAgent
from agents.lead_scorer_agent import LeadScorerAgent
from agents.email_sender_agent import EmailSenderAgent
from agents.sales_pipeline_agent import SalesPipelineAgent
from agents.report_generator_agent import ReportGeneratorAgent
from agents.analytics_agent import AnalyticsAgent
from agents.funnel_management_agent import FunnelManagementAgent

print('✅ All 7+ agents loaded successfully')
"
```

---

## 🔄 Deployment Process

### Option A: Manual Deployment (Recommended for First Time)

**Step 1: Prepare Server**
```bash
# SSH into production server
ssh user@your-server.com

# Create application directory
sudo mkdir -p /opt/felix-automation
sudo chown $USER:$USER /opt/felix-automation

# Clone/copy code
cd /opt/felix-automation
git clone https://github.com/your-org/felix-automation.git . 2>/dev/null || \
  cp -r /path/to/local/felix-automation/* .
```

**Step 2: Setup Environment**
```bash
# Copy configuration from template
cp .env.example .env

# Edit with production values
nano .env  # Fill in API keys, database URL, secrets

# Set permissions
chmod 600 .env
```

**Step 3: Install & Verify**
```bash
# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Run startup checks (from Step 6 above)
python scripts/verify_deployment.py
```

**Step 4: Start Services**
```bash
# Start orchestrator
python orchestrator.py &

# Start Flask backend (if using)
python backend/app.py &

# Monitor logs
tail -f data/logs/orchestrator.log
```

**Step 5: Verify in Production**
```bash
# Test API endpoint
curl https://your-domain.com/health
# Expected: {"status": "ok", "version": "13.0.0"}

# Test auditing endpoint
curl -X POST https://your-domain.com/api/audit \
  -H "Content-Type: application/json" \
  -d '{"client_id": 1}'
# Expected: {"status": "processing", "audit_id": "..."}

# Check email
python -c "
from agents.email_sender_agent import EmailSenderAgent
sender = EmailSenderAgent()
sender.send_test_email('your-email@example.com')
"
```

### Option B: Docker Deployment

**Step 1: Build Image**
```bash
docker build -t felix-automation:v13.0.0 .
```

**Step 2: Run Container**
```bash
docker run -d \
  --name felix \
  -p 5000:5000 \
  -v /opt/felix/data:/app/data \
  -v /opt/felix/.env:/app/.env:ro \
  -e PYTHONUNBUFFERED=1 \
  felix-automation:v13.0.0
```

**Step 3: Verify**
```bash
docker logs felix  # Check logs
docker exec felix python scripts/verify_deployment.py  # Health check
```

### Option C: Kubernetes Deployment

**See:** `deployment.yaml` in `.github/` directory
```bash
kubectl apply -f .github/deployment.yaml
kubectl get pods -l app=felix-automation
```

---

## ✅ Post-Deployment Verification

### Immediate Checks (First 5 minutes)

**1. Service Status**
```bash
# Check all processes running
ps aux | grep python | grep -v grep
# Expected: 2-3 python processes (orchestrator, flask, etc.)

# Check port availability
netstat -tuln | grep 5000
# Expected: LISTEN on port 5000
```

**2. API Connectivity**
```bash
# Health endpoint
curl -s http://localhost:5000/health | python -m json.tool

# Expected output:
# {
#   "status": "ok",
#   "version": "13.0.0",
#   "components": {
#     "database": "connected",
#     "agents": 7,
#     "email": "ready"
#   }
# }
```

**3. Database**
```bash
# Check database tables
python -c "
from orchestrator import FelixAutomationOrchestrator
orch = FelixAutomationOrchestrator()
orch.connect_database()
print(orch.get_database_status())
"

# Expected: All tables present and accessible
```

**4. External API Connectivity**
```bash
# Facebook
python -c "
from whitebox.facebook_ads_live_auditor import FacebookAdsLiveAuditor
auditor = FacebookAdsLiveAuditor(None)
result = auditor.validate_token(os.getenv('FACEBOOK_ACCESS_TOKEN'))
print(f'Facebook: {\"✅\" if result else \"❌\"}')
"

# Google
python -c "
from whitebox.google_ads_live_auditor import GoogleAdsLiveAuditor
auditor = GoogleAdsLiveAuditor(None)
result = auditor.validate_credentials(os.getenv('GOOGLE_DEVELOPER_TOKEN'), ...)
print(f'Google: {\"✅\" if result else \"❌\"}')
"

# SendGrid
python -c "
from agents.email_sender_agent import EmailSenderAgent
sender = EmailSenderAgent(None)
result = sender.test_connection(os.getenv('SENDGRID_API_KEY'))
print(f'SendGrid: {\"✅\" if result else \"❌\"}')
"
```

### First Day Monitoring

**Monitor logs every hour:**
```bash
# Check for errors
grep ERROR data/logs/orchestrator.log | tail -20

# Check for API rate limits
grep "rate_limit\|429" data/logs/orchestrator.log

# Check for database issues
grep "database\|sqlite" data/logs/orchestrator.log | grep -i error
```

**Run sample audit:**
```bash
python -c "
from orchestrator import FelixAutomationOrchestrator
from agents.multi_platform_auditor_agent import MultiPlatformAuditorAgent

orch = FelixAutomationOrchestrator()
orch.connect_database()

auditor = MultiPlatformAuditorAgent(orch)
results = auditor.audit_client(client_id=1)

print(f'Audit status: {results[\"status\"]}')
print(f'Audit time: {results[\"execution_time\"]}s')
"
```

### Weekly Monitoring

- [ ] Check email delivery rate (SendGrid dashboard)
- [ ] Review API quota usage (Facebook, Google)
- [ ] Monitor database size growth
- [ ] Check for any error patterns in logs
- [ ] Verify backup completion

---

## 🚨 Rollback Plan

**If deployment fails or issues found:**

### Quick Rollback (< 5 minutes)
```bash
# Stop current version
pkill -f "python orchestrator.py"
pkill -f "python backend/app.py"

# Checkout previous version
git checkout v12.0.0  # Last stable version

# Reinstall dependencies
pip install -r requirements.txt

# Restart services
python orchestrator.py &
python backend/app.py &

# Verify
curl http://localhost:5000/health
```

### Database Rollback (if schema changed)
```bash
# Restore from backup
./restore.sh production_latest.db

# Restart services
pkill -f orchestrator
python orchestrator.py &
```

### Full System Rollback (worst case)
```bash
# Stop all services
systemctl stop felix-automation

# Restore from full backup
sudo /opt/felix-automation/restore.sh full_backup_2026-10-04.tar.gz

# Restart
systemctl start felix-automation

# Verify
systemctl status felix-automation
```

---

## 📊 Success Criteria

**Deployment is successful when:**

- [ ] All health checks pass (5/5 green)
- [ ] Database connected and schema verified
- [ ] All 7+ agents load without errors
- [ ] Facebook Ads API responding correctly
- [ ] Google Ads API responding correctly
- [ ] SendGrid integration operational
- [ ] PDF reports generating successfully
- [ ] Email tracking working (test email sent/opened)
- [ ] Dashboard loading and displaying data
- [ ] No ERROR entries in logs (INFO/DEBUG allowed)
- [ ] <1% error rate on test audits (20+ audits)
- [ ] Response time <5 seconds for audit endpoint

**If any criterion fails:** Follow rollback procedure

---

## 📞 Support During Deployment

**Contact Information:**
- Primary: Felipe Fernández (felipe@enbuenamesa.com)
- Backup: Development Team
- Escalation: CTO

**Critical Issues During Deployment:**
- Check logs: `tail -100 data/logs/orchestrator.log`
- Verify .env file has all required keys
- Ensure all external APIs are accessible
- Check disk space: `df -h /opt/felix-automation`
- Verify permissions: `ls -la .env` (should be 600)

---

## 📈 Post-Deployment Metrics to Track

### Daily
- [ ] Audit completion rate (target: 100%)
- [ ] Average audit time (target: <5s per client)
- [ ] Email delivery success rate (target: >98%)
- [ ] System error rate (target: <0.1%)

### Weekly
- [ ] PDF report generation success
- [ ] API rate limit usage
- [ ] Database growth rate
- [ ] User engagement metrics

### Monthly
- [ ] System availability (target: 99.9%)
- [ ] Performance trends
- [ ] Cost analysis (API usage)
- [ ] Feature adoption

---

## 🔐 Security Checklist

- [ ] `.env` file not committed to git
- [ ] All API keys rotated from development
- [ ] HTTPS enabled for all endpoints
- [ ] SSL certificate valid (not self-signed in production)
- [ ] Database credentials in environment variables only
- [ ] Logs don't contain sensitive data (credentials, tokens)
- [ ] Master key for encryption is secure
- [ ] Firewall rules restrict access appropriately
- [ ] Database backups encrypted
- [ ] Access logs enabled

---

## 📝 Final Deployment Sign-Off

**Before going live, confirm:**

```
☑ Infrastructure prepared (all requirements met)
☑ External APIs configured and tested
☑ Environment variables configured (.env complete)
☑ Database initialized and schema verified
☑ Dependencies installed without warnings
☑ All startup checks passing
☑ Health check endpoint responds correctly
☑ Sample audit executed successfully
☑ Email sending tested
☑ PDF generation working
☑ Logs monitoring in place
☑ Rollback procedure documented and tested
☑ Team trained on new components
☑ Monitoring/alerts configured
☑ Backup procedure verified
☑ Security checklist completed
```

**Deployment Ready? YES / NO**

If YES, proceed to deployment window.
If NO, resolve blocking items before proceeding.

---

**Version:** 13.0.0  
**Date:** 2026-10-05  
**Status:** ✅ Ready for Production Deployment

For detailed technical information, see `RELEASE_NOTES_v13.0.0.md`
