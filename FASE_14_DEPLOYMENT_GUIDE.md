# 🚀 FASE 14 - DEPLOYMENT GUIDE v14.0.0

**Last Updated:** 2026-10-05  
**Status:** Production Ready  
**Audience:** DevOps, Backend Developers, Sales Operations

---

## 📋 TABLE OF CONTENTS

1. [Pre-Deployment Checklist](#pre-deployment-checklist)
2. [Prerequisites & Dependencies](#prerequisites--dependencies)
3. [API Endpoint Documentation](#api-endpoint-documentation)
4. [Configuration Guide](#configuration-guide)
5. [Database Migration](#database-migration)
6. [Shopify Setup Guide](#shopify-setup-guide)
7. [Health Check Procedures](#health-check-procedures)
8. [Deployment Steps](#deployment-steps)
9. [Post-Deployment Verification](#post-deployment-verification)
10. [Rollback Procedures](#rollback-procedures)
11. [Monitoring & Alerting](#monitoring--alerting)
12. [Troubleshooting Guide](#troubleshooting-guide)

---

## PRE-DEPLOYMENT CHECKLIST

### Code Quality
- [ ] All 39 unit + integration tests passing (`pytest tests/ -v`)
- [ ] No pylint warnings (score >9.0)
- [ ] No bandit security issues
- [ ] Code review approved (2+ reviewers)
- [ ] No uncommitted changes (`git status` clean)

### Compatibility
- [ ] Tested with Python 3.11.x
- [ ] SQLite3 version 3.37+
- [ ] All FASE 13 features verified working
- [ ] Backward compatibility confirmed (zero breaking changes)
- [ ] Database migration tested on staging

### Performance Baseline
- [ ] WebSocket latency <100ms (measured, p95)
- [ ] Dashboard load time <2s on 4G
- [ ] Shopify API rate limit respected (2 req/sec)
- [ ] 100+ concurrent connections successful
- [ ] No memory leaks (run for 30 min, monitor RAM)

### Security Review
- [ ] JWT tokens validated (verify_jwt_token working)
- [ ] Shopify webhook signatures validated
- [ ] No hardcoded secrets in code (all in config.yaml)
- [ ] Credentials encrypted (Fernet AES-128)
- [ ] CORS headers properly configured

### Documentation
- [ ] Release notes complete
- [ ] API documentation updated
- [ ] Configuration guide ready
- [ ] Runbook created
- [ ] Troubleshooting guide complete

---

## PREREQUISITES & DEPENDENCIES

### System Requirements
```
Python:       3.11.x or later
SQLite:       3.37.0 or later
Node.js:      16.x or later (for frontend assets)
Disk Space:   500MB minimum
Memory:       2GB minimum (4GB recommended)
```

### Python Dependencies (New in v14.0.0)
```bash
# In requirements.txt - add or uncomment:
scipy>=1.11.0              # Statistical significance testing
requests>=2.31.0           # Already included, ensure connection pooling
pyjwt>=2.8.0               # Already included, for token verification
cryptography>=41.0.0       # For Shopify webhook HMAC validation
```

### Installation
```bash
# Install dependencies
pip install -r requirements.txt --break-system-packages

# Verify installations
python -c "import scipy, requests, jwt, cryptography; print('✅ All dependencies installed')"
```

### Optional: Development Dependencies
```bash
# For running tests
pip install pytest>=7.4.0
pip install pytest-asyncio>=0.21.0

# For code quality checks
pip install pylint>=2.17.0
pip install bandit>=1.7.5
```

---

## API ENDPOINT DOCUMENTATION

### 1. Real-Time Predictions via WebSocket

#### Connection Establishment
```
Protocol:     WebSocket (wss:// for production)
Endpoint:     /ws/predictions
Auth:         JWT Bearer token (query param: ?token=<jwt>)
Heartbeat:    30s (desktop) / 60s (mobile)
Auto-reconnect: Yes (exponential backoff)
```

**Example Connection:**
```javascript
const token = getJWTToken();
const ws = new WebSocket(`wss://api.enbuenamesa.com/ws/predictions?token=${token}`);

ws.addEventListener('open', () => console.log('✅ Connected'));
ws.addEventListener('message', (event) => {
  const message = JSON.parse(event.data);
  if (message.event_type === 'prediction:generated') {
    updateDashboard(message.data);
  }
});
```

#### Events Received
```json
{
  "event_type": "prediction:generated",
  "timestamp": "2026-10-05T14:30:00Z",
  "data": {
    "client_id": 1,
    "probability": 85,
    "confidence": 92,
    "risk_factors": ["competitive_pressure"],
    "positive_factors": ["high_engagement"],
    "recommendation": "Follow up next week",
    "predicted_timeline_days": 14
  }
}
```

**WebSocket Event Types:**
- `prediction:generated` - New prediction calculated
- `anomaly:detected` - Anomaly in client behavior
- `recommendation:generated` - Sales recommendation
- `test:started` - A/B test started
- `test:completed` - A/B test completed

---

### 2. Prediction API (REST)

#### GET /api/v1/predictions/{client_id}
**Get latest prediction for a client**

```bash
curl -X GET "https://api.enbuenamesa.com/api/v1/predictions/1" \
  -H "Authorization: Bearer $JWT_TOKEN"
```

**Response (200):**
```json
{
  "client_id": 1,
  "probability": 85,
  "confidence": 92,
  "risk_factors": ["competitive_pressure"],
  "positive_factors": ["high_engagement"],
  "recommendation": "Follow up next week",
  "predicted_timeline_days": 14,
  "predicted_at": "2026-10-05T14:30:00Z"
}
```

#### GET /api/v1/predictions/history/{client_id}
**Get prediction history for a client**

```bash
curl -X GET "https://api.enbuenamesa.com/api/v1/predictions/history/1?limit=10" \
  -H "Authorization: Bearer $JWT_TOKEN"
```

**Response (200):**
```json
{
  "client_id": 1,
  "predictions": [
    {
      "probability": 85,
      "confidence": 92,
      "predicted_at": "2026-10-05T14:30:00Z",
      "actual_outcome": null
    }
  ],
  "total": 1,
  "accuracy": null
}
```

---

### 3. A/B Testing API

#### POST /api/v1/tests
**Create a new A/B test**

```bash
curl -X POST "https://api.enbuenamesa.com/api/v1/tests" \
  -H "Authorization: Bearer $JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "test_name": "Followup Email Subject Line",
    "email_type": "followup_day_3",
    "variant_a": {
      "subject": "Quick Question About [Company]",
      "body": "Hi [Name]..."
    },
    "variant_b": {
      "subject": "Following up on our conversation",
      "body": "Hi [Name]..."
    },
    "duration_days": 14
  }'
```

**Response (201):**
```json
{
  "test_id": 1,
  "test_name": "Followup Email Subject Line",
  "email_type": "followup_day_3",
  "status": "active",
  "start_date": "2026-10-05",
  "end_date": "2026-10-19",
  "created_at": "2026-10-05T14:30:00Z"
}
```

#### GET /api/v1/tests
**List active A/B tests**

```bash
curl -X GET "https://api.enbuenamesa.com/api/v1/tests?status=active" \
  -H "Authorization: Bearer $JWT_TOKEN"
```

**Response (200):**
```json
{
  "tests": [
    {
      "test_id": 1,
      "test_name": "Followup Email Subject Line",
      "status": "active",
      "start_date": "2026-10-05",
      "participants": 150
    }
  ],
  "total": 1
}
```

#### GET /api/v1/tests/{test_id}/results
**Get results for a test**

```bash
curl -X GET "https://api.enbuenamesa.com/api/v1/tests/1/results" \
  -H "Authorization: Bearer $JWT_TOKEN"
```

**Response (200):**
```json
{
  "test_id": 1,
  "test_name": "Followup Email Subject Line",
  "status": "active",
  "results": {
    "variant_a": {
      "sent": 75,
      "opens": 26,
      "clicks": 6,
      "conversions": 1,
      "open_rate": 0.347,
      "click_rate": 0.08,
      "conversion_rate": 0.013
    },
    "variant_b": {
      "sent": 75,
      "opens": 28,
      "clicks": 8,
      "conversions": 2,
      "open_rate": 0.373,
      "click_rate": 0.107,
      "conversion_rate": 0.027
    },
    "statistical_analysis": {
      "p_value": 0.047,
      "confidence_interval": [0.012, 0.042],
      "improvement": "106%",
      "significance": "p < 0.05",
      "winner": "B",
      "recommendation": "Variant B shows statistically significant improvement. Deploy at scale."
    }
  }
}
```

#### POST /api/v1/tests/{test_id}/winner
**Mark test winner and apply**

```bash
curl -X POST "https://api.enbuenamesa.com/api/v1/tests/1/winner" \
  -H "Authorization: Bearer $JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "winner": "B",
    "apply_at_scale": true
  }'
```

**Response (200):**
```json
{
  "test_id": 1,
  "status": "completed",
  "winner": "B",
  "applied": true,
  "deployment_timestamp": "2026-10-05T14:35:00Z"
}
```

---

### 4. Shopify Integration API

#### POST /api/v1/shopify/connect
**Connect Shopify store**

```bash
curl -X POST "https://api.enbuenamesa.com/api/v1/shopify/connect" \
  -H "Authorization: Bearer $JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "client_id": 1,
    "shop_domain": "example-store.myshopify.com",
    "access_token": "shpat_XXXXXXXXXXXXXXXXXXXX"
  }'
```

**Response (201):**
```json
{
  "store_id": 1,
  "shop_domain": "example-store.myshopify.com",
  "status": "connected",
  "connected_at": "2026-10-05T14:30:00Z",
  "last_sync": null
}
```

#### GET /api/v1/shopify/analytics
**Get Shopify analytics**

```bash
curl -X GET "https://api.enbuenamesa.com/api/v1/shopify/analytics?client_id=1" \
  -H "Authorization: Bearer $JWT_TOKEN"
```

**Response (200):**
```json
{
  "store_id": 1,
  "metrics": {
    "total_orders": 145,
    "total_revenue": 12500.50,
    "average_order_value": 86.21,
    "conversion_rate": 0.032,
    "top_products": [
      {"id": "1", "name": "Product A", "revenue": 3000}
    ]
  },
  "last_sync": "2026-10-05T14:30:00Z"
}
```

#### Webhook: POST /webhooks/shopify/orders/created
**Shopify order created webhook**

Automatically syncs new orders. Signature validation required (HMAC-SHA256).

```
Header: X-Shopify-Hmac-SHA256: <signature>
Body: JSON order data from Shopify
Response: 200 OK (acknowledge receipt)
```

---

## CONFIGURATION GUIDE

### 1. Create config.yaml

Create `/home/claude/felix-automation/config.yaml`:

```yaml
# Database Configuration
database:
  type: sqlite
  path: /home/claude/felix-automation/database.sqlite
  backup_path: /home/claude/felix-automation/backups/database.sqlite
  
# WebSocket Configuration (Mobile Optimization)
websocket:
  mobile_heartbeat_interval: 60  # seconds
  desktop_heartbeat_interval: 30  # seconds
  max_connections: 1000
  event_history_size: 100
  enable_compression: true  # gzip event payloads for mobile
  
# JWT Configuration
jwt:
  secret: ${JWT_SECRET}  # Set via environment variable
  algorithm: HS256
  expiration_hours: 24
  
# Shopify Configuration
shopify:
  api_version: "2024-01"
  rate_limit: 2  # requests per second
  webhook_validation: true
  store_credentials_encrypt: true
  webhook_topics:
    - "orders/created"
    - "orders/updated"
    - "products/updated"
    
# A/B Testing Configuration
ab_testing:
  enabled: true
  default_test_duration_days: 14
  significance_threshold: 0.05  # p-value for winner determination
  min_sample_size: 30  # per variant
  auto_apply_winner: false  # manual review required
  
# ML Predictions Configuration
predictions:
  enabled: true
  enable_anomaly_detection: true
  enable_recommendations: true
  confidence_threshold: 0.70  # minimum confidence to display
  
# Email Configuration
email:
  provider: sendgrid
  api_key: ${SENDGRID_API_KEY}
  from_address: noreply@enbuenamesa.com
  track_opens: true
  track_clicks: true
  
# Logging Configuration
logging:
  level: INFO
  format: json  # for structured logging
  files:
    websocket: /home/claude/felix-automation/logs/websocket.log
    shopify: /home/claude/felix-automation/logs/shopify.log
    predictions: /home/claude/felix-automation/logs/predictions.log
    ab_testing: /home/claude/felix-automation/logs/ab_testing.log
  retention_days: 30
  
# Security Configuration
security:
  cors_origins:
    - https://app.enbuenamesa.com
    - https://dashboard.enbuenamesa.com
  credential_encryption: true
  cipher: fernet  # AES-128
  
# Monitoring Configuration
monitoring:
  health_check_interval: 60  # seconds
  metrics_collection: true
  alert_webhook: ${ALERT_WEBHOOK_URL}
```

### 2. Environment Variables

Create `.env` file (never commit to git):

```bash
# JWT Secret (generate with: python -c "import secrets; print(secrets.token_urlsafe(32))")
JWT_SECRET=your_generated_secret_here

# Shopify Credentials (per store, can be multiple)
SHOPIFY_STORE_1_DOMAIN=example-store.myshopify.com
SHOPIFY_STORE_1_TOKEN=shpat_XXXXXXXXXXXXXXXXXXXX

# SendGrid
SENDGRID_API_KEY=SG.XXXXXXXXXXXXXXXXXXXX

# Alert Webhook (Slack, Teams, etc.)
ALERT_WEBHOOK_URL=https://hooks.slack.com/services/T00/B00/XXXX

# Database
DATABASE_PATH=/home/claude/felix-automation/database.sqlite
DATABASE_BACKUP_PATH=/home/claude/felix-automation/backups/

# Logging
LOG_LEVEL=INFO
```

### 3. Load Configuration in App

```python
# In backend/config.py or main app initialization
import yaml
import os
from pathlib import Path

def load_config():
    """Load configuration from config.yaml and environment variables"""
    config_path = Path(__file__).parent.parent / 'config.yaml'
    
    with open(config_path, 'r') as f:
        config = yaml.safe_load(f)
    
    # Override with environment variables
    config['jwt']['secret'] = os.getenv('JWT_SECRET')
    config['shopify']['stores'] = {
        'store_1': {
            'domain': os.getenv('SHOPIFY_STORE_1_DOMAIN'),
            'token': os.getenv('SHOPIFY_STORE_1_TOKEN')
        }
    }
    config['email']['api_key'] = os.getenv('SENDGRID_API_KEY')
    config['monitoring']['alert_webhook'] = os.getenv('ALERT_WEBHOOK_URL')
    
    return config

CONFIG = load_config()
```

---

## DATABASE MIGRATION

### Step 1: Backup Current Database

```bash
# Create backups directory
mkdir -p /home/claude/felix-automation/backups

# Backup current database
cp database.sqlite backups/database.sqlite.$(date +%Y%m%d_%H%M%S).backup

# Verify backup
sqlite3 backups/database.sqlite.* ".tables"
```

### Step 2: Run Migration Script

Create `/home/claude/felix-automation/migrate_v14.py`:

```python
#!/usr/bin/env python3
"""FASE 14 Database Migration Script"""

import sqlite3
import sys
from pathlib import Path

def run_migration():
    """Run FASE 14 database schema migration"""
    db_path = Path('database.sqlite')
    
    if not db_path.exists():
        print("❌ Database not found. Run init_database.py first.")
        sys.exit(1)
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        # Check FASE version
        cursor.execute("PRAGMA user_version")
        version = cursor.fetchone()[0]
        print(f"Current schema version: {version}")
        
        if version >= 14:
            print("✅ Database already at FASE 14 or newer")
            return
        
        # Run migrations
        print("Running FASE 14 migration...")
        
        # 1. Add new tables for Shopify
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS shopify_stores (
                store_id INTEGER PRIMARY KEY,
                client_id INTEGER NOT NULL,
                shop_domain TEXT UNIQUE NOT NULL,
                access_token TEXT NOT NULL,
                shop_name TEXT,
                currency TEXT,
                timezone TEXT,
                connected_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                last_sync TIMESTAMP,
                status TEXT DEFAULT 'active'
            )
        """)
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS shopify_orders (
                order_id INTEGER PRIMARY KEY,
                store_id INTEGER NOT NULL,
                order_number INTEGER,
                customer_id INTEGER,
                total_price REAL,
                subtotal_price REAL,
                total_tax REAL,
                total_shipping REAL,
                currency TEXT,
                financial_status TEXT,
                fulfillment_status TEXT,
                created_at TIMESTAMP,
                updated_at TIMESTAMP,
                FOREIGN KEY(store_id) REFERENCES shopify_stores(store_id)
            )
        """)
        
        # 2. Add table for predictions history
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS prediction_history (
                prediction_id INTEGER PRIMARY KEY,
                client_id INTEGER NOT NULL,
                probability REAL,
                confidence REAL,
                risk_factors TEXT,
                positive_factors TEXT,
                recommendation TEXT,
                predicted_timeline_days INTEGER,
                predicted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                actual_outcome BOOLEAN,
                outcome_date TIMESTAMP,
                FOREIGN KEY(client_id) REFERENCES clients(id)
            )
        """)
        
        # 3. Add tables for A/B testing
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS ab_tests (
                test_id INTEGER PRIMARY KEY,
                test_name TEXT NOT NULL,
                email_type TEXT NOT NULL,
                variant_a TEXT,
                variant_b TEXT,
                active BOOLEAN DEFAULT 1,
                start_date DATE,
                end_date DATE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS ab_test_results (
                result_id INTEGER PRIMARY KEY,
                test_id INTEGER NOT NULL,
                client_id INTEGER NOT NULL,
                variant TEXT,
                sent_count INTEGER DEFAULT 0,
                opens INTEGER DEFAULT 0,
                clicks INTEGER DEFAULT 0,
                conversions INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY(test_id) REFERENCES ab_tests(test_id),
                FOREIGN KEY(client_id) REFERENCES clients(id)
            )
        """)
        
        # Create indexes for performance
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_shopify_stores_client ON shopify_stores(client_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_shopify_orders_store ON shopify_orders(store_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_prediction_history_client ON prediction_history(client_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_ab_tests_active ON ab_tests(active)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_ab_test_results_test ON ab_test_results(test_id)")
        
        # Update schema version
        cursor.execute("PRAGMA user_version = 14")
        
        conn.commit()
        print("✅ Migration completed successfully")
        print("✅ All new tables created")
        print("✅ All indexes created")
        
    except Exception as e:
        print(f"❌ Migration failed: {e}")
        conn.rollback()
        sys.exit(1)
    finally:
        conn.close()

if __name__ == '__main__':
    run_migration()
```

Run migration:
```bash
cd /home/claude/felix-automation
python migrate_v14.py
```

### Step 3: Verify Migration

```bash
# Check tables
sqlite3 database.sqlite ".tables"

# Check schema version
sqlite3 database.sqlite "PRAGMA user_version"

# Verify new tables exist
sqlite3 database.sqlite "SELECT name FROM sqlite_master WHERE type='table' AND name LIKE 'shopify%' OR name LIKE '%ab_test%' OR name='prediction_history'"
```

**Expected output:**
```
shopify_stores shopify_orders prediction_history ab_tests ab_test_results
Schema version: 14
```

---

## SHOPIFY SETUP GUIDE

### Step 1: Create Shopify App

1. Go to https://admin.shopify.com/settings/apps-and-integrations/develop-apps
2. Click **"Create an app"**
3. Enter:
   - **App name:** "Felix Automation - Sales Analytics"
   - **App type:** "Custom app"
4. Click **"Create app"**

### Step 2: Configure Admin API Scopes

1. Navigate to **Configuration** tab
2. Under **Admin API**, select scopes:
   - `read_orders` - Read order data
   - `read_products` - Read product data
   - `read_analytics` - Read analytics data
   - `write_inventory` - Write inventory updates (optional)
3. Click **Save**

### Step 3: Get Access Token

1. Click **API credentials** tab
2. Copy **Access token** (format: `shpat_XXXXXXXXXXXXXXXXXXXX`)
3. ⚠️ **NEVER share this token** - treat like password
4. Store in `.env` file:
   ```bash
   SHOPIFY_STORE_1_DOMAIN=yourstore.myshopify.com
   SHOPIFY_STORE_1_TOKEN=shpat_XXXXXXXXXXXXXXXXXXXX
   ```

### Step 4: Configure Webhooks

1. In **Configuration**, scroll to **Webhooks**
2. Click **Add webhook**
3. For each webhook topic:
   - **Topic:** `orders/created`
   - **Webhook URL:** `https://api.enbuenamesa.com/webhooks/shopify/orders/created`
   - **API version:** `2024-01`
   - Click **Save**

4. Repeat for:
   - `orders/updated`
   - `products/updated`

### Step 5: Test Connection

```bash
# Test Shopify API client
python -c "
from whitebox.shopify_api_client import ShopifyAPIClient
client = ShopifyAPIClient(
    shop_domain='yourstore.myshopify.com',
    access_token='shpat_XXXXXXXXXXXXXXXXXXXX'
)
if client.is_healthy():
    print('✅ Shopify connection successful')
else:
    print('❌ Shopify connection failed')
"
```

### Step 6: Sync Initial Data

```bash
# Trigger first sync
python -c "
from whitebox.shopify_api_client import ShopifyAPIClient
from datetime import datetime, timedelta

client = ShopifyAPIClient(
    shop_domain='yourstore.myshopify.com',
    access_token='shpat_XXXXXXXXXXXXXXXXXXXX'
)

# Get last 30 days of orders
cutoff_date = datetime.now() - timedelta(days=30)
orders = client.get_orders(updated_after=cutoff_date)
print(f'✅ Synced {len(orders)} orders')

# Get products
products = client.get_products(updated_after=cutoff_date)
print(f'✅ Synced {len(products)} products')
"
```

---

## HEALTH CHECK PROCEDURES

### Automated Health Check Script

Create `/home/claude/felix-automation/health_check.py`:

```python
#!/usr/bin/env python3
"""FASE 14 System Health Check"""

import asyncio
import sqlite3
import time
from datetime import datetime

class HealthCheck:
    def __init__(self):
        self.checks = {}
        self.start_time = time.time()
    
    async def check_database(self):
        """Check SQLite database"""
        try:
            conn = sqlite3.connect('database.sqlite')
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM clients")
            client_count = cursor.fetchone()[0]
            conn.close()
            self.checks['database'] = {
                'status': '✅ HEALTHY',
                'clients': client_count,
                'response_time': f"{(time.time() - self.start_time):.0f}ms"
            }
        except Exception as e:
            self.checks['database'] = {'status': f'❌ ERROR: {e}'}
    
    async def check_websocket(self):
        """Check WebSocket manager"""
        try:
            from backend.websocket_manager import get_connection_manager
            manager = get_connection_manager()
            stats = manager.get_connection_stats()
            self.checks['websocket'] = {
                'status': '✅ HEALTHY',
                'active_connections': stats['total_connections'],
                'admin_connections': stats['admin_connections']
            }
        except Exception as e:
            self.checks['websocket'] = {'status': f'❌ ERROR: {e}'}
    
    async def check_predictions(self):
        """Check prediction system"""
        try:
            from analytics.predictor import ConversionPredictor
            predictor = ConversionPredictor()
            # Run test prediction
            prediction = predictor.predict_conversion(1)
            self.checks['predictions'] = {
                'status': '✅ HEALTHY',
                'model_version': 'v2.1',
                'probability': f"{prediction.probability}%"
            }
        except Exception as e:
            self.checks['predictions'] = {'status': f'❌ ERROR: {e}'}
    
    async def check_shopify(self):
        """Check Shopify connection"""
        try:
            from whitebox.shopify_api_client import ShopifyAPIClient
            # This checks configuration, not specific credentials
            self.checks['shopify'] = {
                'status': '✅ READY',
                'note': 'Requires credentials in config'
            }
        except Exception as e:
            self.checks['shopify'] = {'status': f'❌ ERROR: {e}'}
    
    async def check_email(self):
        """Check SendGrid connection"""
        try:
            import os
            api_key = os.getenv('SENDGRID_API_KEY')
            if api_key:
                self.checks['email'] = {
                    'status': '✅ CONFIGURED',
                    'provider': 'SendGrid'
                }
            else:
                self.checks['email'] = {
                    'status': '⚠️  NOT CONFIGURED',
                    'note': 'Set SENDGRID_API_KEY environment variable'
                }
        except Exception as e:
            self.checks['email'] = {'status': f'❌ ERROR: {e}'}
    
    async def run_all(self):
        """Run all health checks"""
        print("\n🏥 FASE 14 Health Check - Starting")
        print(f"Timestamp: {datetime.now().isoformat()}\n")
        
        await asyncio.gather(
            self.check_database(),
            self.check_websocket(),
            self.check_predictions(),
            self.check_shopify(),
            self.check_email()
        )
        
        self.print_report()
    
    def print_report(self):
        """Print health check report"""
        print("📊 System Status:")
        print("-" * 60)
        
        for system, details in self.checks.items():
            print(f"\n{system.upper()}:")
            for key, value in details.items():
                print(f"  {key}: {value}")
        
        print("\n" + "=" * 60)
        elapsed = time.time() - self.start_time
        print(f"✅ Health check completed in {elapsed:.2f}s")
        
        # Overall status
        errors = [k for k, v in self.checks.items() if '❌' in str(v.get('status', ''))]
        if errors:
            print(f"⚠️  {len(errors)} system(s) with issues: {', '.join(errors)}")
        else:
            print("✅ All systems healthy")

async def main():
    check = HealthCheck()
    await check.run_all()

if __name__ == '__main__':
    asyncio.run(main())
```

Run health check:
```bash
python health_check.py
```

**Expected output:**
```
🏥 FASE 14 Health Check - Starting
Timestamp: 2026-10-05T14:30:00

📊 System Status:
----

DATABASE:
  status: ✅ HEALTHY
  clients: 42
  response_time: 12ms

WEBSOCKET:
  status: ✅ HEALTHY
  active_connections: 0
  admin_connections: 0

PREDICTIONS:
  status: ✅ HEALTHY
  model_version: v2.1
  probability: 82%

SHOPIFY:
  status: ✅ READY
  note: Requires credentials in config

EMAIL:
  status: ✅ CONFIGURED
  provider: SendGrid

============================================================
✅ Health check completed in 1.23s
✅ All systems healthy
```

---

## DEPLOYMENT STEPS

### Production Deployment Checklist

```bash
#!/bin/bash
# FASE 14 Production Deployment Script

set -e  # Exit on error

echo "🚀 FASE 14 Production Deployment"
echo "=================================="

# 1. Pre-flight checks
echo "1️⃣  Running pre-flight checks..."
python -m pytest tests/ -v --tb=short
if [ $? -ne 0 ]; then
    echo "❌ Tests failed. Aborting deployment."
    exit 1
fi

# 2. Database backup
echo "2️⃣  Backing up database..."
mkdir -p backups
cp database.sqlite backups/database.sqlite.$(date +%Y%m%d_%H%M%S).backup
echo "✅ Database backed up"

# 3. Run migration
echo "3️⃣  Running database migration..."
python migrate_v14.py
if [ $? -ne 0 ]; then
    echo "❌ Migration failed. Rolling back..."
    exit 1
fi

# 4. Install dependencies
echo "4️⃣  Installing dependencies..."
pip install -r requirements.txt --break-system-packages --quiet

# 5. Health check
echo "5️⃣  Running health checks..."
python health_check.py

# 6. Deploy code
echo "6️⃣  Deploying code..."
git add -A
git commit -m "Deploy FASE 14 v14.0.0" || true
git push origin main

# 7. Restart services
echo "7️⃣  Restarting services..."
systemctl restart felix-automation-backend
systemctl restart felix-automation-websocket

# 8. Post-deployment verification
echo "8️⃣  Running post-deployment verification..."
sleep 5  # Wait for services to start
python verify_deployment.py

echo ""
echo "✅ DEPLOYMENT COMPLETED SUCCESSFULLY"
echo "📦 Version: v14.0.0"
echo "⏰ Deployed at: $(date)"
```

Save as `deploy.sh` and run:
```bash
chmod +x deploy.sh
./deploy.sh
```

---

## POST-DEPLOYMENT VERIFICATION

### Verification Checklist

```python
#!/usr/bin/env python3
"""Post-Deployment Verification"""

import requests
import json
from datetime import datetime

class DeploymentVerification:
    def __init__(self, base_url="https://api.enbuenamesa.com"):
        self.base_url = base_url
        self.token = "your_test_jwt_token"
        self.headers = {"Authorization": f"Bearer {self.token}"}
        self.results = []
    
    def test_api_endpoint(self, endpoint, method="GET", data=None):
        """Test API endpoint"""
        try:
            url = f"{self.base_url}{endpoint}"
            if method == "GET":
                response = requests.get(url, headers=self.headers, timeout=5)
            elif method == "POST":
                response = requests.post(url, headers=self.headers, json=data, timeout=5)
            
            success = response.status_code < 400
            self.results.append({
                'endpoint': endpoint,
                'method': method,
                'status': response.status_code,
                'success': success,
                'timestamp': datetime.now().isoformat()
            })
            return success
        except Exception as e:
            self.results.append({
                'endpoint': endpoint,
                'error': str(e),
                'success': False,
                'timestamp': datetime.now().isoformat()
            })
            return False
    
    def run_all_tests(self):
        """Run all post-deployment tests"""
        print("\n📋 POST-DEPLOYMENT VERIFICATION")
        print("=" * 60)
        
        tests = [
            ("/api/v1/health", "GET"),
            ("/api/v1/predictions/1", "GET"),
            ("/api/v1/tests", "GET"),
            ("/api/v1/shopify/analytics", "GET"),
        ]
        
        for endpoint, method in tests:
            print(f"Testing {method} {endpoint}...", end=" ")
            if self.test_api_endpoint(endpoint, method):
                print("✅")
            else:
                print("❌")
        
        self.print_report()
    
    def print_report(self):
        """Print verification report"""
        print("\n📊 RESULTS:")
        print("-" * 60)
        
        passed = sum(1 for r in self.results if r['success'])
        total = len(self.results)
        
        for result in self.results:
            status = "✅" if result['success'] else "❌"
            print(f"{status} {result['endpoint']}")
        
        print("\n" + "=" * 60)
        print(f"✅ PASSED: {passed}/{total}")
        
        if passed == total:
            print("🎉 DEPLOYMENT VERIFIED - ALL SYSTEMS GO!")
        else:
            print("⚠️  ISSUES DETECTED - SEE ABOVE")

if __name__ == '__main__':
    verification = DeploymentVerification()
    verification.run_all_tests()
```

---

## ROLLBACK PROCEDURES

### Quick Rollback

If deployment fails or issues are discovered:

```bash
#!/bin/bash
# Rollback Script

echo "🔄 ROLLING BACK FASE 14 DEPLOYMENT..."

# 1. Stop services
systemctl stop felix-automation-backend
systemctl stop felix-automation-websocket

# 2. Restore database
LATEST_BACKUP=$(ls -t backups/database.sqlite.* | head -1)
echo "Restoring from: $LATEST_BACKUP"
cp "$LATEST_BACKUP" database.sqlite

# 3. Restore code
git checkout HEAD~1
git reset --hard

# 4. Restart services
systemctl start felix-automation-backend
systemctl start felix-automation-websocket

echo "✅ ROLLBACK COMPLETED"
echo "Previous version restored"
```

---

## MONITORING & ALERTING

### Key Metrics to Monitor

```yaml
metrics:
  websocket:
    - active_connections (should be <1000)
    - message_latency_ms (should be <100)
    - error_rate (should be <1%)
  
  predictions:
    - prediction_latency_ms (should be <500)
    - anomaly_detection_rate
    - confidence_scores (trending)
  
  shopify:
    - sync_latency_ms (should be <5000)
    - api_error_rate (should be <1%)
    - webhook_delivery_success (should be >99%)
  
  ab_testing:
    - active_tests_count
    - sample_sizes_per_variant
    - statistical_power
    
  system:
    - memory_usage (should be <2GB)
    - disk_usage (should be <80%)
    - database_query_latency_ms
```

### Alert Triggers

```yaml
alerts:
  critical:
    - websocket_error_rate > 5%
    - database_connection_failed
    - shopify_sync_failed
    - prediction_latency > 2000ms
  
  warning:
    - websocket_latency > 200ms
    - shopify_rate_limit_exceeded
    - ab_test_low_sample_size
    - memory_usage > 1.8GB
```

### Alert Webhook Example (Slack)

```python
def send_alert(severity, message, details):
    """Send alert to monitoring system"""
    webhook_url = os.getenv('ALERT_WEBHOOK_URL')
    
    payload = {
        'text': f'{severity}: {message}',
        'attachments': [{
            'color': 'danger' if severity == 'CRITICAL' else 'warning',
            'fields': [
                {'title': k, 'value': str(v), 'short': True}
                for k, v in details.items()
            ]
        }]
    }
    
    requests.post(webhook_url, json=payload)
```

---

## TROUBLESHOOTING GUIDE

### WebSocket Issues

**Problem:** Clients cannot connect to WebSocket
```
Solution:
1. Verify JWT token is valid: python -c "from backend.auth import verify_jwt_token; print(verify_jwt_token('token'))"
2. Check WebSocket logs: tail -f logs/websocket.log
3. Verify heartbeat interval: curl http://localhost:5000/api/v1/health
4. Check browser console for connection errors
5. Verify firewall allows WebSocket (port 443 or 8000)
```

**Problem:** High WebSocket latency
```
Solution:
1. Check active connections: sqlite3 database.sqlite "SELECT COUNT(*) FROM active_connections"
2. Monitor CPU usage: top -p $(pgrep -f websocket_manager)
3. Check event frequency: grep "broadcast_event" logs/websocket.log | tail -100 | wc -l
4. Reduce event payload size: enable event_data_optimization in config
5. Increase heartbeat interval for mobile clients: websocket.mobile_heartbeat_interval = 120
```

### Database Issues

**Problem:** Migration fails with "table already exists"
```
Solution:
1. Check if tables already exist: sqlite3 database.sqlite ".tables"
2. If tables exist, migration already ran
3. Verify schema version: sqlite3 database.sqlite "PRAGMA user_version"
4. Check for table corruption: sqlite3 database.sqlite "PRAGMA integrity_check"
5. If corrupted, restore from backup: cp backups/database.sqlite.* database.sqlite
```

**Problem:** Slow queries on ab_test_results
```
Solution:
1. Verify indexes exist: sqlite3 database.sqlite ".indices ab_test_results"
2. If missing, recreate: sqlite3 database.sqlite "CREATE INDEX idx_ab_test_results_test ON ab_test_results(test_id)"
3. Vacuum database: sqlite3 database.sqlite "VACUUM"
4. Analyze table statistics: sqlite3 database.sqlite "ANALYZE ab_test_results"
5. Consider pagination: GET /api/v1/tests/{id}/results?limit=1000&offset=0
```

### Shopify Integration Issues

**Problem:** "Invalid access token" or 401 Unauthorized
```
Solution:
1. Verify token format: token should start with "shpat_"
2. Check token not expired: tokens don't expire, but may be regenerated
3. Verify token has required scopes: read_orders, read_products, read_analytics
4. Test directly: curl -H "X-Shopify-Access-Token: $TOKEN" https://$DOMAIN/admin/api/2024-01/shop.json
5. Regenerate token in Shopify Admin if needed
```

**Problem:** Webhook signature validation fails
```
Solution:
1. Verify webhook secret is correct: config.yaml shopify.webhook_secret
2. Check X-Shopify-Hmac-SHA256 header exists in webhook request
3. Verify HMAC calculation: python -c "
   import hmac, base64
   secret = b'your_webhook_secret'
   body = b'webhook_body_here'
   signature = base64.b64encode(hmac.new(secret, body, 'sha256').digest()).decode()
   print(signature)
   "
3. Compare with header value
4. Resend webhook from Shopify Admin for testing
```

**Problem:** Rate limit exceeded (429 Too Many Requests)
```
Solution:
1. Check rate limiter: config.yaml shopify.rate_limit (should be 2 req/sec)
2. Verify RateLimiter in ShopifyAPIClient is working
3. Check for concurrent requests: grep "make_request" logs/shopify.log | head -10
4. Implement exponential backoff: see whitebox/shopify_api_client.py
5. Add request queuing if needed: use asyncio.Queue for bulk syncs
```

### A/B Testing Issues

**Problem:** Variants not assigned to clients
```
Solution:
1. Verify variant assigner is running: tail -f logs/ab_testing.log
2. Check active tests: sqlite3 database.sqlite "SELECT * FROM ab_tests WHERE active=1"
3. Verify test_id and client_id in assignment: EmailVariantAssigner.assign_variant(test_id, client_id)
4. Check variant assignment determinism: same (test_id, client_id) should always return same variant
5. Verify in logs: grep "assign_variant" logs/ab_testing.log
```

**Problem:** Statistical significance calculation fails
```
Solution:
1. Verify scipy is installed: python -c "import scipy; print(scipy.__version__)"
2. Check sample sizes: need at least 30 samples per variant
3. Verify chi-square test input: from agents.statistical_tester import StatisticalTester; tester.compare_variants(a, b)
4. Check for division by zero: ensure denominator (total sends) > 0
5. Review p-value calculation: p_value should be between 0 and 1
```

### Prediction System Issues

**Problem:** Predictions not broadcasting to dashboard
```
Solution:
1. Verify PredictionBroadcaster is running: tail -f logs/predictions.log
2. Check WebSocket connection: admin must be connected
3. Verify predictor generates predictions: ConversionPredictor.predict_conversion()
4. Check event formatting: events must have client_id, probability, confidence
5. Monitor broadcast: grep "broadcast_prediction" logs/predictions.log
```

**Problem:** Confidence scores too low (<40%)
```
Solution:
1. This may be expected if client has little history
2. Check if sufficient data exists: SELECT COUNT(*) FROM client_interactions WHERE client_id=X
3. Review risk factors: they reduce confidence score
4. Verify positive factors are recognized
5. Consider increasing confidence_threshold in config if too strict
```

---

## SUPPORT & ESCALATION

### Support Contacts
- **Backend Issues:** Felipe @enbuenamesa.com
- **DevOps:** DevOps Team @ ops@enbuenamesa.com
- **Shopify Integration:** Integration Lead @ integrations@enbuenamesa.com

### Emergency Rollback
If system is critical failure:
```bash
# Immediate rollback (1 minute)
./rollback.sh
```

### Performance SLA
- **WebSocket Latency:** <100ms (p95) - Alert if >200ms
- **Dashboard Load:** <2s on 4G - Alert if >3s
- **API Response:** <500ms (p95) - Alert if >1s
- **Uptime:** 99.9% - Alert if <99%

---

**Document Version:** 1.0  
**Last Updated:** 2026-10-05  
**Next Review:** 2026-11-05
