# FASE 15 Kickoff Guide
**WhatsApp Integration - Week 1 Action Plan**

---

## 🎯 This Week's Goals

By end of Week 1, achieve:
1. ✅ Twilio account created and configured
2. ✅ Database schema extended (3 new tables)
3. ✅ Initial WhatsApp Message Agent skeleton
4. ✅ Team trained on architecture
5. ✅ Feature branches created

---

## 📋 Day 1-2: Twilio Setup

### Step 1: Create Twilio Account
```bash
# Go to https://www.twilio.com/console
# Sign up for Business account (required for WhatsApp)
# Verify phone number
# Save credentials:
# - Account SID
# - Auth Token
# - WhatsApp Sandbox Number (+1 234-567-XXXX)
```

### Step 2: WhatsApp Sandbox Configuration
```bash
# In Twilio console:
# 1. Go to Messaging → WhatsApp → Learn
# 2. Link your phone number
# 3. Send test message "join <code>" to confirm connection
# 4. Save sandbox number to config

# Copy to environment:
export TWILIO_ACCOUNT_SID="your_account_sid"
export TWILIO_AUTH_TOKEN="your_auth_token"
export TWILIO_WHATSAPP_FROM="+1 234-567-XXXX"
```

### Step 3: Configure Webhook
```bash
# In Twilio console:
# 1. Go to Messaging → WhatsApp → Sandbox Settings
# 2. Set Status Callback URL: https://yourdomain.com/webhooks/whatsapp/status
# 3. Set Incoming Message URL: https://yourdomain.com/webhooks/whatsapp/messages
# 4. Save

# For development (local):
# Use ngrok to create tunnel: ngrok http 8000
# Use ngrok URL for webhook (e.g., https://abc123.ngrok.io/webhooks/...)
```

### Verification
```bash
# Test API connection
python -c "
from twilio.rest import Client
account_sid = os.getenv('TWILIO_ACCOUNT_SID')
auth_token = os.getenv('TWILIO_AUTH_TOKEN')
client = Client(account_sid, auth_token)
message = client.messages.create(
    body='Test message',
    from_='whatsapp:+1234567XXXX',
    to='whatsapp:+your_number'
)
print(f'Message sent: {message.sid}')
"
```

---

## 📊 Day 3-4: Database Schema

### Step 1: Backup Production
```bash
# CRITICAL: Backup existing database first
cp data/pipeline.sqlite data/pipeline.sqlite.backup
cp data/pipeline.sqlite data/pipeline.sqlite.dev
```

### Step 2: Create New Tables
```sql
-- File: init_database.py (add to end)

CREATE TABLE IF NOT EXISTS whatsapp_messages (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    client_id INTEGER NOT NULL,
    message_id TEXT UNIQUE,
    body TEXT,
    variant TEXT CHECK(variant IN ('A', 'B')),
    phone_number TEXT,
    status TEXT DEFAULT 'pending',
    sent_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    error_message TEXT,
    retry_count INTEGER DEFAULT 0,
    
    FOREIGN KEY (client_id) REFERENCES clients(id)
);

CREATE TABLE IF NOT EXISTS whatsapp_conversion_tracking (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    client_id INTEGER NOT NULL,
    message_id TEXT,
    variant TEXT,
    
    -- Delivery
    sent_at TIMESTAMP,
    delivered_at TIMESTAMP,
    delivery_time_seconds INTEGER,
    
    -- Read
    read_at TIMESTAMP,
    time_to_read_seconds INTEGER,
    
    -- Click
    clicked_at TIMESTAMP,
    clicked_url TEXT,
    
    -- Conversion
    converted_at TIMESTAMP,
    conversion_type TEXT,
    conversion_value REAL,
    
    funnel_stage TEXT,
    device_type TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    FOREIGN KEY (client_id) REFERENCES clients(id)
);

CREATE TABLE IF NOT EXISTS whatsapp_ab_tests (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT UNIQUE,
    variant_a TEXT,
    variant_b TEXT,
    active BOOLEAN DEFAULT 1,
    start_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    end_date TIMESTAMP,
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Indices for performance
CREATE INDEX IF NOT EXISTS idx_whatsapp_messages_client 
    ON whatsapp_messages(client_id);
CREATE INDEX IF NOT EXISTS idx_conversion_tracking_client 
    ON whatsapp_conversion_tracking(client_id);
CREATE INDEX IF NOT EXISTS idx_conversion_tracking_funnel 
    ON whatsapp_conversion_tracking(funnel_stage);
CREATE INDEX IF NOT EXISTS idx_conversion_tracking_time 
    ON whatsapp_conversion_tracking(created_at);
```

### Step 2: Apply Migration
```bash
# Development environment
sqlite3 data/pipeline.sqlite < schema.sql

# Verify
sqlite3 data/pipeline.sqlite ".tables"
# Should show: whatsapp_messages whatsapp_conversion_tracking whatsapp_ab_tests
```

### Verification
```bash
sqlite3 data/pipeline.sqlite "
SELECT name FROM sqlite_master 
WHERE type='table' AND name LIKE 'whatsapp%';
"
# Should return 3 tables
```

---

## 🤖 Day 5: WhatsApp Message Agent Skeleton

### Step 1: Create Module Structure
```bash
mkdir -p agents/tests
touch agents/whatsapp_message_agent.py
touch agents/tests/test_whatsapp_message_agent.py
```

### Step 2: Agent Skeleton
```python
# File: agents/whatsapp_message_agent.py

import os
from typing import Optional, Dict
from twilio.rest import Client
import logging

logger = logging.getLogger(__name__)

class WhatsAppMessageAgent:
    """Send and manage WhatsApp messages via Twilio"""
    
    def __init__(self):
        self.account_sid = os.getenv('TWILIO_ACCOUNT_SID')
        self.auth_token = os.getenv('TWILIO_AUTH_TOKEN')
        self.from_number = os.getenv('TWILIO_WHATSAPP_FROM')
        self.client = Client(self.account_sid, self.auth_token)
        
    def send_message(self, 
                    phone_number: str, 
                    body: str, 
                    variant: str = 'A') -> Dict:
        """
        Send WhatsApp message
        
        Args:
            phone_number: Recipient phone (E.164 format: +1234567890)
            body: Message text
            variant: A/B test variant
            
        Returns:
            Message metadata including message_id, status, timestamp
        """
        try:
            # Validate phone
            assert phone_number.startswith('+'), "Phone must be E.164 format"
            
            # Send via Twilio
            message = self.client.messages.create(
                from_=f'whatsapp:{self.from_number}',
                to=f'whatsapp:{phone_number}',
                body=body
            )
            
            # Log event
            logger.info(f"Message sent: {message.sid} to {phone_number}")
            
            return {
                'message_id': message.sid,
                'status': 'sent',
                'phone': phone_number,
                'variant': variant
            }
            
        except Exception as e:
            logger.error(f"Failed to send message: {e}")
            return {
                'message_id': None,
                'status': 'failed',
                'error': str(e)
            }
    
    def format_message(self, template: str, **variables) -> str:
        """Format message with variables"""
        return template.format(**variables)
    
    def schedule_message(self, phone: str, body: str, send_at):
        """Schedule message for later (TODO: implement)"""
        pass

# Test it
if __name__ == '__main__':
    agent = WhatsAppMessageAgent()
    result = agent.send_message(
        '+your_test_number',
        'Test message from FASE 15'
    )
    print(result)
```

### Step 3: Basic Unit Test
```python
# File: agents/tests/test_whatsapp_message_agent.py

import pytest
from agents.whatsapp_message_agent import WhatsAppMessageAgent

class TestWhatsAppMessageAgent:
    
    def test_format_message(self):
        agent = WhatsAppMessageAgent()
        template = "Hola {name}, tu propuesta de ${amount} está lista"
        result = agent.format_message(template, name="Juan", amount="5000")
        assert "Juan" in result
        assert "5000" in result
    
    def test_message_format_validation(self):
        agent = WhatsAppMessageAgent()
        # Phone must be E.164 format
        with pytest.raises(AssertionError):
            agent.send_message('1234567890', 'Test')  # Missing +
    
    def test_send_message_structure(self):
        agent = WhatsAppMessageAgent()
        # Mock test - structure validation only
        result = agent.format_message("Test {var}", var="value")
        assert result == "Test value"

# Run tests
# pytest agents/tests/test_whatsapp_message_agent.py -v
```

### Step 4: Update Config
```yaml
# File: config.yaml (add to end)

whatsapp:
  api_provider: "twilio"
  rate_limit: 80  # messages per second
  timeout: 10     # seconds
  retry_attempts: 3
  message_templates:
    proposal_sent: "Tu propuesta de ${amount} está lista ✅ Ver propuesta: ${link}"
    proposal_reminder: "¿Preguntas sobre tu propuesta? ${link}"
    proposal_accepted: "¡Excelente! 🎉 Comenzamos la implementación."
```

---

## 👥 Team Coordination

### Create Feature Branches
```bash
# Main feature branches for Week 1-2
git checkout -b feature/whatsapp-message-agent
git checkout -b feature/database-schema
git checkout -b feature/conversion-tracking
git checkout -b feature/webhook-handler

# Parallel work
# Dev 1: Message Agent + Database
# Dev 2: Conversion Tracking
# Dev 3: Webhook (starts Week 2)
```

### Communication Plan
```markdown
# Daily standup (10 min, 9:00 AM)
- What I built yesterday
- What I'm building today
- Blockers

# Weekly review (Friday, 4:00 PM)
- Demo working features
- Discuss blockers
- Plan next week
```

---

## ✅ Week 1 Verification Checklist

By Friday end of day, verify:

**Twilio Setup (100%)**
- [ ] Account created and funded
- [ ] Phone number verified
- [ ] Webhook configured
- [ ] Test message sent successfully
- [ ] Credentials secured in .env

**Database (100%)**
- [ ] Backup created
- [ ] 3 new tables created
- [ ] 4 indices created
- [ ] Schema verified in sqlite3
- [ ] Migrations tested on dev database

**Agent Skeleton (80%)**
- [ ] Module structure created
- [ ] Basic send_message() implemented
- [ ] Message formatting working
- [ ] 3 unit tests passing
- [ ] Code reviews completed

**Team (100%)**
- [ ] All developers have repo access
- [ ] Feature branches created
- [ ] Environment setup completed
- [ ] Daily standups scheduled
- [ ] Weekly reviews scheduled

---

## 🚀 Week 2 Preview

Week 2 focus: Complete Message Agent + Start Tracking

**Goals:**
1. ✅ Full WhatsApp Message Agent implementation
2. ✅ Conversion Tracking System started
3. ✅ Webhook endpoints skeleton
4. ✅ Integration tests created

**Deliverables:**
- agents/whatsapp_message_agent.py (100% complete)
- analytics/conversion_tracker.py (30% complete)
- backend/routes/whatsapp_webhooks.py (skeleton)
- 15+ unit tests passing

---

## 💡 Tips & Best Practices

### Twilio Development
```bash
# Use sandbox mode for testing (doesn't cost money)
# Test with your actual phone number first
# Log all API calls for debugging
# Use retry logic for failures
```

### Database
```bash
# Always backup before migrations
# Test schema on dev database first
# Use transactions for multi-step operations
# Create indices AFTER data loads
```

### Code
```bash
# Write tests first (TDD approach)
# Keep commits small and focused
# Use type hints (Python 3.11+)
# Document complex logic
```

### Team
```bash
# Use git feature branches (never commit to main)
# Code review every PR before merge
# Run full test suite before merge
# Keep PRs small (<300 lines)
```

---

## 📞 Support & Escalation

**Day 1-2 Issues:** Contact Twilio Support  
**Database Issues:** Check schema validation script  
**Agent Development:** Review existing agents pattern  
**Team Coordination:** Felipe Rodriguez (felipe@enbuenamesa.com)

---

## 📅 Next Milestones

- **Oct 13 (End Week 1):** Foundation complete
- **Oct 20 (End Week 2):** Message Agent + Tracking started
- **Oct 27 (End Week 3):** A/B Testing framework complete
- **Nov 3 (End Week 4):** Dashboard & Integration done
- **Nov 10 (End Week 5):** Testing & Optimization
- **Nov 17 (Week 6):** Production deployment

---

**Kickoff Date:** October 6, 2026  
**Prepared By:** Claude Haiku 4.5  
**Contact:** felipe@enbuenamesa.com

Let's build FASE 15! 🚀
