# 🚀 FASE 14 Phase 2 - DEPLOYMENT CHECKLIST

**Status:** Ready for Production Deployment  
**Date:** October 6, 2026  
**Target Environment:** Production  
**Rollback Plan:** Available (snapshot database)

---

## PRE-DEPLOYMENT VERIFICATION

- [x] Database schema complete (verify with: `sqlite3 database.sqlite ".tables"`)
- [x] All 7 API endpoints tested
- [x] EmailVariantAssigner verified (deterministic assignment)
- [x] StatisticalTester verified (chi-square calculations)
- [x] Email sender integration verified
- [x] Dashboard files present and functional
- [x] Dependencies installed (scipy, numpy)
- [x] Verification script: 100% passing (7/7)

---

## DEPLOYMENT STEPS

### Step 1: Database Verification
```bash
# Verify database exists and has tables
ls -la database.sqlite
sqlite3 database.sqlite ".tables"

# Expected output should include:
# ab_tests ab_test_results ab_test_assignments

# Verify schema
sqlite3 database.sqlite ".schema ab_tests"
```

### Step 2: Dependencies Check
```bash
# Verify scipy and numpy installed
python3 -c "import scipy; import numpy; print(f'scipy {scipy.__version__}, numpy {numpy.__version__}')"

# Expected output: scipy 1.18.1+, numpy 2.5.3+
```

### Step 3: Backend Integration
```bash
# In backend/app.py, add this to startup:

from backend.routes.ab_testing_routes import init_ab_testing
from backend.app_init import database  # or however database is initialized

# In the @app.on_event("startup") or app initialization:
if database:
    init_ab_testing(database)
    logger.info("✅ A/B Testing routes initialized")
```

### Step 4: Frontend Deployment
```bash
# Copy dashboard files to web server
cp frontend/ab_testing_dashboard.html /var/www/html/dashboards/
cp frontend/dashboard_mobile.html /var/www/html/dashboards/

# Verify accessibility
curl http://localhost:8000/dashboards/ab_testing_dashboard.html | head -20
```

### Step 5: API Testing
```bash
# Test that API endpoints are responding
curl http://localhost:8000/api/tests -H "Content-Type: application/json"

# Expected: 200 OK with empty list or existing tests
```

### Step 6: Email Sender Test
```bash
# Send test email with A/B test (via admin API or test script)
# This will:
# 1. Check for active test
# 2. Assign variant to client
# 3. Send variant-specific email
# 4. Record in ab_test_results table
```

### Step 7: Verification Post-Deployment
```bash
# Run verification script
python3 verify_fase14_phase2_complete.py

# Expected: 100% success rate (7/7 tests)
```

---

## DEPLOYMENT CONFIGURATION

### Environment Variables
```bash
# If using environment-based configuration:
export AB_TESTING_ENABLED=true
export AB_TEST_DURATION_DAYS=14
export AB_TEST_SIGNIFICANCE_THRESHOLD=0.05
```

### Database Backup
```bash
# Before deployment, backup current database
cp database.sqlite database.sqlite.backup.$(date +%Y%m%d_%H%M%S)

# Verify backup
sqlite3 database.sqlite.backup.20261006_000000 ".tables"
```

---

## MONITORING POST-DEPLOYMENT

### Health Checks
```bash
# Monitor A/B testing health (add to monitoring dashboard)
curl http://localhost:8000/api/tests | jq '.[] | {id, test_name, active, email_type}'

# Check for any errors in logs
tail -f logs/phase2_deployment.log | grep -i "error\|warning"
```

### Key Metrics to Monitor
1. **API Response Times**
   - Target: <100ms for all endpoints
   - Critical: >500ms

2. **Database Performance**
   - Variant assignment queries: <1ms
   - Statistical calculations: <100ms
   - Dashboard queries: <500ms

3. **Email Integration**
   - Emails sent with variant tracking: 100% success
   - No errors in ab_test_results insertion
   - Tracking pixel fires correctly

4. **Statistical Accuracy**
   - Chi-square calculations within expected range
   - P-values between 0 and 1
   - Confidence intervals properly bounded

### Alerts to Configure
- [ ] API latency > 200ms
- [ ] Database query > 500ms
- [ ] A/B test record insertion failures
- [ ] Statistical calculation errors

---

## ROLLBACK PLAN

If issues occur during deployment:

### Immediate Rollback
```bash
# 1. Stop the application
sudo systemctl stop fasé14-app

# 2. Restore database backup
cp database.sqlite.backup.20261006_000000 database.sqlite

# 3. Remove A/B testing route initialization from app.py
# (comment out init_ab_testing() call)

# 4. Restart application
sudo systemctl start fasé14-app

# 5. Verify previous version is working
curl http://localhost:8000/api/tests
# Should fail with 404 if route removed (expected)
```

### Restore Specific Component
- **Remove A/B Testing Dashboard**: Delete `frontend/ab_testing_dashboard.html`
- **Disable Email A/B Testing**: Comment out `_check_and_apply_ab_test()` in email_sender_agent.py
- **Restore Old Routes**: Revert changes to `backend/app.py`

---

## TESTING SCENARIOS POST-DEPLOYMENT

### Scenario 1: Create and Run A/B Test
```
1. Create test via API: POST /api/tests
   - test_name: "Welcome Email Subject Test"
   - email_type: "audit_report"
   - variant_a: subject: "Your Audit is Ready", body: "Content A"
   - variant_b: subject: "Check Your Audit Results", body: "Content B"
   - duration_days: 14

2. Send emails to 10 clients
   - Expect ~5 get variant A, ~5 get variant B
   
3. Record opens/clicks
   - Variant A: 3 opens, 1 click
   - Variant B: 4 opens, 2 clicks
   
4. Get results: GET /api/tests/{test_id}/results
   - Should show statistical comparison
   - Calculate p-value
   - Show confidence intervals
```

### Scenario 2: Dashboard Verification
```
1. Navigate to ab_testing_dashboard.html
2. Should display:
   - Active tests list
   - Running test metrics
   - Variant comparison bars
   - Statistical significance indicator
   - Winner (if determined)
   - Recommendations (in Spanish)
```

### Scenario 3: Pause and Resume Test
```
1. Create test
2. Send some emails (variant assignment)
3. Pause test: POST /api/tests/{test_id}/pause
   - Should not assign variants to new clients
   - Existing assignments preserved
4. Resume test: POST /api/tests/{test_id}/resume
   - Should resume variant assignment
5. Verify assignments are consistent
```

---

## POST-DEPLOYMENT DOCUMENTATION

### Update Internal Docs
- [ ] Add Phase 2 to project README
- [ ] Document API endpoints in internal wiki
- [ ] Create runbook for managing A/B tests
- [ ] Document statistical methods used
- [ ] Add troubleshooting guide

### Update Client Docs (if applicable)
- [ ] Explain A/B testing feature
- [ ] Show how to view test results
- [ ] Explain statistical significance
- [ ] Provide best practices

---

## DEPLOYMENT SIGN-OFF

**Prepared By:** Claude Haiku 4.5  
**Date:** October 6, 2026  
**Status:** ✅ READY FOR DEPLOYMENT

### Pre-Deployment Review
- [x] Code reviewed (7 components verified)
- [x] Tests passing (100% success rate)
- [x] Database schema validated
- [x] Documentation complete
- [x] Monitoring prepared

### Approval Required
- [ ] Development Lead
- [ ] QA Lead
- [ ] DevOps/Infrastructure
- [ ] Product Manager

---

## NEXT STEPS AFTER DEPLOYMENT

1. **Monitor for 24 hours** - Watch metrics and logs
2. **Send test emails** - Verify A/B testing works end-to-end
3. **Create real test** - First production A/B test
4. **Gather feedback** - Get team input
5. **Begin Phase 3** - Start real-time features

---

## SUPPORT CONTACTS

If issues arise during deployment:

1. **Database Issues**: Check `database.sqlite` file permissions
2. **API Issues**: Check `backend/routes/ab_testing_routes.py` initialization
3. **Email Issues**: Check `agents/email_sender_agent.py` A/B test integration
4. **Dashboard Issues**: Check `frontend/ab_testing_dashboard.html` file location

---

**Deployment Checklist Version:** 1.0  
**Last Updated:** October 6, 2026  
**Status:** ✅ READY TO DEPLOY
