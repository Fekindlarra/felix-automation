# 🚀 SEO API Quick Reference

**FASE 14 - SEO Analysis Integration**  
**Complete endpoint reference for quick lookup**

---

## 📡 Endpoints at a Glance

### 1️⃣ Get Latest Audit
```bash
GET /api/seo/audit/{client_id}?token=TOKEN

# Response
{
  "status": "success",
  "score": 95,
  "findings_count": 3,
  "findings": [...]
}
```

### 2️⃣ Run Audit (Start Background Job)
```bash
POST /api/seo/audit/{client_id}?token=TOKEN

# Response
{
  "status": "success",
  "audit_id": 123,
  "audit_status": "running"
}
```

### 3️⃣ Get Audit History (Paginated)
```bash
GET /api/seo/history/{client_id}?token=TOKEN&limit=10&offset=0

# Response
{
  "status": "success",
  "total": 25,
  "audits": [
    {"id": 124, "score": 95, "created_at": "..."},
    {"id": 123, "score": 92, "created_at": "..."}
  ]
}
```

### 4️⃣ Get Detailed Report
```bash
GET /api/seo/report/{client_id}?token=TOKEN&audit_id=123

# Response
{
  "status": "success",
  "overall_score": 95,
  "findings_by_severity": {
    "critical": [...],
    "warning": [...],
    "info": [...]
  },
  "recommendations": [...]
}
```

### 5️⃣ Compare Trend (Days)
```bash
GET /api/seo/compare/{client_id}?token=TOKEN&days=30

# Response
{
  "status": "success",
  "trend": "improving",
  "improvement": 20.0,
  "improvement_percentage": 26.67,
  "scores_over_time": [
    {"date": "...", "score": 75},
    {"date": "...", "score": 95}
  ]
}
```

### 6️⃣ Get Dimensions Breakdown
```bash
GET /api/seo/dimensions/{client_id}?token=TOKEN

# Response
{
  "status": "success",
  "overall_score": 95,
  "dimensions": {
    "tecnica": {"score": 100, "findings": 1, "weight": "25%"},
    "contenido": {"score": 95, "findings": 3, "weight": "30%"},
    "rendimiento": {"score": 90, "findings": 4, "weight": "25%"},
    "seguridad": {"score": 85, "findings": 2, "weight": "20%"}
  },
  "keywords_detected": ["automatización", "ventas"]
}
```

---

## 🔐 Authentication

All endpoints require `token` query parameter:

```bash
# Get token
token=$(python3 -c "from backend.auth import create_admin_token; print(create_admin_token('admin@example.com'))")

# Use in any request
curl "http://localhost:8000/api/seo/audit/1?token=$token"
```

---

## 📊 Quick Workflows

### Workflow 1: Get Latest Score
```bash
# 1. Get latest audit
curl "http://localhost:8000/api/seo/audit/1?token=$TOKEN"

# 2. Extract score from response
# {
#   "score": 95,
#   "findings_count": 3
# }
```

### Workflow 2: Run Audit & Poll
```bash
# 1. Start audit
curl -X POST "http://localhost:8000/api/seo/audit/1?token=$TOKEN"
# Returns: {"audit_id": 123, "audit_status": "running"}

# 2. Poll every 5 seconds until complete
sleep 5
curl "http://localhost:8000/api/seo/audit/1?token=$TOKEN"

# 3. When status changes to "completed", show results
```

### Workflow 3: View Progress Report
```bash
# Get detailed report with recommendations
curl "http://localhost:8000/api/seo/report/1?token=$TOKEN"

# Shows:
# - overall_score
# - findings grouped by severity
# - specific recommendations
# - keywords detected
```

### Workflow 4: Track Improvement
```bash
# Compare last 30 days
curl "http://localhost:8000/api/seo/compare/1?token=$TOKEN&days=30"

# Shows:
# - trend (improving/declining/stable)
# - improvement percentage
# - scores over time for charting
```

---

## 🎯 Common Queries

### Get All Critical Issues
```bash
curl "http://localhost:8000/api/seo/report/1?token=$TOKEN" \
  | jq '.findings_by_severity.critical'
```

### Get Only Warnings
```bash
curl "http://localhost:8000/api/seo/report/1?token=$TOKEN" \
  | jq '.findings_by_severity.warning'
```

### Get Score Trend
```bash
curl "http://localhost:8000/api/seo/compare/1?token=$TOKEN" \
  | jq '.scores_over_time'
```

### Get All Keywords
```bash
curl "http://localhost:8000/api/seo/dimensions/1?token=$TOKEN" \
  | jq '.keywords_detected'
```

### Get Specific Dimension Score
```bash
curl "http://localhost:8000/api/seo/dimensions/1?token=$TOKEN" \
  | jq '.dimensions.rendimiento.score'
```

---

## 📈 Response Status Codes

| Code | Meaning | Solution |
|------|---------|----------|
| 200 | Success | Parse response |
| 404 | Not Found | Check client_id, audit_id |
| 500 | Server Error | Check server logs |
| Invalid token | Unauthorized | Regenerate token |

---

## 🔄 Audit Status Flow

```
POST /api/seo/audit
        ↓
audit_status = "running"
        ↓
[Wait 5-30 seconds]
        ↓
GET /api/seo/audit
        ↓
audit_status = "completed"
        ↓
Result available in response
```

---

## 🛠️ Testing Endpoints

### With curl
```bash
TOKEN=$(python3 -c "from backend.auth import create_admin_token; print(create_admin_token('admin@example.com'))")

# Test GET
curl "http://localhost:8000/api/seo/audit/1?token=$TOKEN"

# Test POST
curl -X POST "http://localhost:8000/api/seo/audit/1?token=$TOKEN"

# With jq formatting
curl "http://localhost:8000/api/seo/audit/1?token=$TOKEN" | jq '.'
```

### With Python
```python
import requests
from backend.auth import create_admin_token

token = create_admin_token("admin@example.com")

# GET request
r = requests.get("http://localhost:8000/api/seo/audit/1", 
                params={"token": token})
print(r.json())

# POST request
r = requests.post("http://localhost:8000/api/seo/audit/1",
                 params={"token": token})
print(r.json())
```

### With JavaScript
```javascript
const token = "your_admin_token";

// GET
fetch(`/api/seo/audit/1?token=${token}`)
  .then(r => r.json())
  .then(data => console.log(data));

// POST
fetch(`/api/seo/audit/1?token=${token}`, {method: 'POST'})
  .then(r => r.json())
  .then(data => console.log(data));
```

---

## 📋 Parameter Reference

| Param | Endpoint | Type | Default | Max | Required |
|-------|----------|------|---------|-----|----------|
| client_id | All | path | - | - | Yes |
| token | All | query | - | - | Yes |
| audit_id | GET /report | query | latest | - | No |
| audit_id | GET /dimensions | query | latest | - | No |
| limit | GET /history | query | 10 | 50 | No |
| offset | GET /history | query | 0 | - | No |
| days | GET /compare | query | 30 | 365 | No |

---

## 🔍 Score Interpretation

| Score | Status | Action |
|-------|--------|--------|
| 90-100 | 🌟 Excellent | Maintain |
| 80-89 | ✅ Good | Review warnings |
| 70-79 | ⚠️ Fair | Fix critical |
| 60-69 | 🔴 Low | Audit needed |
| 0-59 | ❌ Poor | Urgent action |

---

## 📚 Full Documentation

For complete details, see:
- `/backend/routes/SEO_API_DOCUMENTATION.md` - Full specs
- `/backend/routes/seo_routes.py` - Implementation
- `/tests/test_seo_routes.py` - Test examples

---

## ⚡ Performance Tips

- ✅ Use `audit_id` parameter to avoid re-fetching latest
- ✅ Cache results for 5-10 minutes
- ✅ Poll with 5 second intervals (not 1 second)
- ✅ Use WebSocket events when available (instead of polling)
- ✅ Batch requests when possible

---

## 🆘 Troubleshooting

**404 - Not Found**
```bash
# Verify client exists
curl "http://localhost:8000/api/seo/audit/999?token=$TOKEN"
# Make sure client_id is correct
```

**No audit found**
```bash
# Client hasn't been audited yet
# Run audit first:
curl -X POST "http://localhost:8000/api/seo/audit/1?token=$TOKEN"
```

**Status still "running"**
```bash
# Normal - audits take 1-30 seconds
# Keep polling every 5 seconds
```

**Invalid token**
```bash
# Regenerate token
TOKEN=$(python3 -c "from backend.auth import create_admin_token; print(create_admin_token('admin@example.com'))")
```

---

## 📞 Quick Links

| Resource | Path |
|----------|------|
| API Docs | `/backend/routes/SEO_API_DOCUMENTATION.md` |
| Implementation | `/backend/routes/seo_routes.py` |
| Tests | `/tests/test_seo_routes.py` |
| Core Auditor | `/auditors/seo_auditor.py` |
| Summary | `/SEO_API_ROUTES_IMPLEMENTATION.md` |

---

**Version:** 1.0.0  
**Last Updated:** 2026-10-05  
**Status:** ✅ Production Ready
