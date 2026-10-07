# Phase 3 API Endpoints Documentation

## Overview

This document describes all new and modified API endpoints for FASE 15 Phase 3 execution. All endpoints require appropriate authentication and are protected by role-based access control.

**Base URL:** `http://localhost:8000/api`  
**Authentication:** Bearer token in `Authorization` header  
**Content-Type:** `application/json` for all requests/responses

---

## Admin Endpoints (Requires `admin` role)

### Activate Phase 3

```
POST /api/admin/phase3/activate
```

**Description:** Activates Phase 3 after pre-flight checks

**Request:**
```json
{
  "reason": "Manual activation after Phase 2 completion",
  "scheduled_time": "2026-10-06T22:00:00Z"
}
```

**Response (Success: 200):**
```json
{
  "status": "success",
  "message": "Phase 3 activated successfully",
  "timestamp": "2026-10-06T22:00:00Z",
  "checks_passed": {
    "database_connection": true,
    "phase_2_health": true,
    "database_integrity": true,
    "backups_recent": true,
    "circuit_breakers": true,
    "websocket_ready": true
  },
  "backup_location": "/data/backups/phase3_start_20261006_220000.sqlite",
  "first_checkpoint": {
    "hora": 48,
    "scheduled_at": "2026-10-06T22:02:00Z"
  },
  "monitoring_daemon": {
    "status": "started",
    "pid": 12345
  }
}
```

**Response (Failure: 400):**
```json
{
  "status": "error",
  "message": "Pre-flight check failed",
  "failed_check": "phase_2_health",
  "reason": "Phase 2 error rate too high (0.15% > 0.08%)",
  "can_retry": true
}
```

**Curl Example:**
```bash
curl -X POST http://localhost:8000/api/admin/phase3/activate \
  -H "Authorization: Bearer $ADMIN_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"reason": "Scheduled activation"}'
```

---

### Deactivate Phase 3 (Kill-Switch)

```
POST /api/admin/phase3/deactivate
```

**Description:** Immediately deactivates Phase 3 and reverts to Phase 2

**Request:**
```json
{
  "reason": "Critical alert - latency spike detected",
  "requested_by": "Felipe"
}
```

**Response (Success: 200):**
```json
{
  "status": "success",
  "message": "Phase 3 deactivated successfully",
  "timestamp": "2026-10-06T22:15:30Z",
  "actions_completed": {
    "feature_flag_disabled": true,
    "monitoring_daemon_stopped": true,
    "traffic_reverted_to_phase_2": true,
    "database_restored": true,
    "event_broadcast": true,
    "alerts_sent": true
  },
  "time_to_stable": "0.85 seconds",
  "last_checkpoint": {
    "hora": 52,
    "decision": "NO-GO",
    "reason": "latency_spike"
  },
  "backup_restored": "/data/backups/phase3_start_20261006_220000.sqlite"
}
```

**Response (Failure: 401):**
```json
{
  "status": "error",
  "message": "Unauthorized",
  "required_role": "admin",
  "your_role": "viewer"
}
```

**Curl Example:**
```bash
curl -X POST http://localhost:8000/api/admin/phase3/deactivate \
  -H "Authorization: Bearer $ADMIN_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"reason": "Emergency rollback"}'
```

---

### Get Phase 3 Status

```
GET /api/admin/phase3/status
```

**Description:** Returns current Phase 3 execution status and latest checkpoint

**Response (Success: 200):**
```json
{
  "status": "executing",
  "timestamp": "2026-10-06T22:15:00Z",
  "phase_3_active": true,
  "current_phase": 2,
  "rollout_percentage": 50,
  "checkpoints_completed": 7,
  "total_checkpoints": 13,
  "last_checkpoint": {
    "hora": 54,
    "timestamp": "2026-10-06T22:12:00Z",
    "status": "6/6 GREEN",
    "decision": "CONTINUE",
    "metrics": {
      "ml_accuracy": 0.837,
      "error_rate": 0.00016,
      "websocket_latency": 8,
      "predictions_hour": 49,
      "personalization_active": 152,
      "active_tests": 10
    }
  },
  "next_checkpoint": {
    "hora": 56,
    "scheduled_at": "2026-10-06T22:14:00Z",
    "status": "pending"
  },
  "circuit_breakers": {
    "database": "CLOSED",
    "websocket": "CLOSED",
    "prediction": "CLOSED"
  },
  "active_alerts": []
}
```

**Curl Example:**
```bash
curl -X GET http://localhost:8000/api/admin/phase3/status \
  -H "Authorization: Bearer $ADMIN_TOKEN"
```

---

### Get Phase 3 Checkpoints

```
GET /api/admin/phase3/checkpoints
```

**Description:** Returns all checkpoints from current Phase 3 execution

**Query Parameters:**
- `hora_from` (optional): Start HORA (default: 48)
- `hora_to` (optional): End HORA (default: 72)
- `limit` (optional): Max results (default: 100)

**Response (Success: 200):**
```json
{
  "status": "success",
  "total_checkpoints": 7,
  "checkpoints": [
    {
      "hora": 48,
      "timestamp": "2026-10-06T22:00:00Z",
      "status": "6/6 GREEN",
      "decision": "CONTINUE",
      "metrics": {
        "ml_accuracy": 0.835,
        "error_rate": 0.00017,
        "websocket_latency": 8,
        "predictions_hour": 48,
        "personalization_active": 150,
        "active_tests": 9
      },
      "metrics_met": 6
    },
    {
      "hora": 50,
      "timestamp": "2026-10-06T22:02:00Z",
      "status": "6/6 GREEN",
      "decision": "CONTINUE",
      "metrics_met": 6
    }
    // ... more checkpoints
  ]
}
```

**Curl Example:**
```bash
curl -X GET "http://localhost:8000/api/admin/phase3/checkpoints?hora_from=48&hora_to=60" \
  -H "Authorization: Bearer $ADMIN_TOKEN"
```

---

### Get Phase 3 Report

```
GET /api/admin/phase3/report
```

**Description:** Returns final Phase 3 report (available after HORA 72)

**Query Parameters:**
- `format` (optional): `json`, `markdown`, `html` (default: `json`)

**Response (Success: 200):**
```json
{
  "status": "success",
  "report_format": "json",
  "execution_summary": {
    "start_time": "2026-10-06T22:00:00Z",
    "end_time": "2026-10-07T22:00:00Z",
    "total_duration_hours": 24,
    "final_decision": "SUCCESS",
    "checkpoints_completed": 13,
    "checkpoints_continue": 13,
    "checkpoints_caution": 0,
    "checkpoints_no_go": 0
  },
  "metrics_summary": {
    "ml_accuracy_avg": 0.8356,
    "error_rate_avg": 0.000168,
    "websocket_latency_avg": 8.2,
    "predictions_hour_avg": 48.5,
    "personalization_active_avg": 151.2,
    "active_tests_avg": 9.3
  },
  "phase_progression": {
    "phase_1": {
      "start_time": "2026-10-06T22:00:00Z",
      "end_time": "2026-10-06T22:04:00Z",
      "rollout_percentage": 10,
      "checkpoints": 2,
      "status": "COMPLETE"
    },
    "phase_2": {
      "start_time": "2026-10-06T22:04:00Z",
      "end_time": "2026-10-06T22:10:00Z",
      "rollout_percentage": 50,
      "checkpoints": 4,
      "status": "COMPLETE"
    },
    "phase_3": {
      "start_time": "2026-10-06T22:10:00Z",
      "end_time": "2026-10-07T22:00:00Z",
      "rollout_percentage": 100,
      "checkpoints": 7,
      "status": "COMPLETE"
    }
  },
  "business_impact": {
    "estimated_conversion_lift": "35%",
    "estimated_incremental_orders": 770000,
    "estimated_annual_revenue_impact": "$1,925,000",
    "roi": "Positive"
  }
}
```

**Curl Example:**
```bash
curl -X GET "http://localhost:8000/api/admin/phase3/report?format=markdown" \
  -H "Authorization: Bearer $ADMIN_TOKEN"
```

---

## Dashboard Endpoints (Requires `viewer` role or higher)

### Get Real-Time Metrics

```
GET /api/phase3/metrics/current
```

**Description:** Returns current Phase 3 metrics for dashboard

**Response (Success: 200):**
```json
{
  "status": "success",
  "timestamp": "2026-10-06T22:15:30Z",
  "phase": 2,
  "rollout_percentage": 50,
  "metrics": {
    "ml_accuracy": {
      "value": 0.837,
      "target": 0.78,
      "status": "HEALTHY",
      "trend": "stable"
    },
    "error_rate": {
      "value": 0.00016,
      "target": 0.0008,
      "status": "HEALTHY",
      "trend": "stable"
    },
    "websocket_latency": {
      "value": 8,
      "target": 95,
      "status": "HEALTHY",
      "trend": "stable"
    },
    "predictions_hour": {
      "value": 49,
      "target": 42,
      "status": "HEALTHY",
      "trend": "stable"
    },
    "personalization_active": {
      "value": 152,
      "target": 140,
      "status": "HEALTHY",
      "trend": "stable"
    },
    "active_tests": {
      "value": 10,
      "target": 8,
      "status": "HEALTHY",
      "trend": "stable"
    }
  },
  "overall_status": "6/6 GREEN",
  "alerts": []
}
```

**Polling Frequency:** Recommended 5 seconds (WebSocket preferred)

**Curl Example:**
```bash
curl -X GET http://localhost:8000/api/phase3/metrics/current \
  -H "Authorization: Bearer $VIEWER_TOKEN"
```

---

### WebSocket Connection

```
WS /ws/phase3
```

**Description:** WebSocket for real-time Phase 3 events

**Connection:**
```javascript
const ws = new WebSocket('ws://localhost:8000/ws/phase3');

ws.onopen = () => {
  console.log('Connected to Phase 3 stream');
};

ws.onmessage = (event) => {
  const data = JSON.parse(event.data);
  console.log('Event:', data.event_type, data.data);
};
```

**Event Types:**
- `phase3:activated` - Phase 3 started
- `phase3:checkpoint_started` - Checkpoint collection began
- `phase3:metrics_collected` - Metrics gathered (every 2h)
- `phase3:decision_made` - Decision made (CONTINUE/CAUTION/NO-GO)
- `phase3:phase_advanced` - Rollout percentage escalated
- `phase3:checkpoint_completed` - Checkpoint complete
- `phase3:alert` - Alert triggered
- `phase3:rollback_triggered` - Rollback executed

**Event Payload Example:**
```json
{
  "event_type": "phase3:checkpoint_completed",
  "timestamp": "2026-10-06T22:12:00Z",
  "data": {
    "hora": 54,
    "status": "6/6 GREEN",
    "decision": "CONTINUE",
    "metrics_met": 6
  }
}
```

---

## Public Endpoints (No authentication)

### Health Check

```
GET /health
```

**Response:**
```json
{
  "status": "healthy",
  "timestamp": "2026-10-06T22:15:30Z",
  "services": {
    "database": "up",
    "websocket": "up",
    "prediction": "up",
    "metrics_collector": "up"
  }
}
```

---

## Error Handling

All error responses follow this format:

```json
{
  "status": "error",
  "error_code": "INVALID_REQUEST",
  "message": "Human-readable error message",
  "details": {
    "field": "reason",
    "suggestion": "how_to_fix"
  }
}
```

**Common Error Codes:**
- `401_UNAUTHORIZED` - Missing or invalid auth token
- `403_FORBIDDEN` - Insufficient permissions
- `400_INVALID_REQUEST` - Malformed request
- `409_CONFLICT` - Phase 3 already active or not active
- `503_SERVICE_UNAVAILABLE` - Backend service down
- `500_INTERNAL_ERROR` - Server error

---

## Rate Limiting

- Admin endpoints: 60 requests per minute per token
- Viewer endpoints: 300 requests per minute per token
- WebSocket: 100 messages per second per connection

**Rate Limit Headers:**
```
X-RateLimit-Limit: 60
X-RateLimit-Remaining: 45
X-RateLimit-Reset: 1633542900
```

---

## Authentication

### Getting Admin Token

```bash
# Request token
curl -X POST http://localhost:8000/auth/token \
  -H "Content-Type: application/json" \
  -d '{
    "username": "admin",
    "password": "admin_password",
    "scope": "admin"
  }'

# Response
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "Bearer",
  "expires_in": 3600
}

# Use token
export ADMIN_TOKEN="eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
```

### Token Scope Requirements

| Endpoint | Required Scope | Role |
|----------|----------------|------|
| `POST /phase3/activate` | `admin` | Administrator |
| `POST /phase3/deactivate` | `admin` | Administrator |
| `GET /phase3/status` | `admin` | Administrator |
| `GET /phase3/checkpoints` | `admin` | Administrator |
| `GET /phase3/report` | `admin` | Administrator |
| `GET /phase3/metrics/current` | `viewer` | Viewer/Admin |
| `WS /ws/phase3` | `viewer` | Viewer/Admin |

---

**Document Version:** 1.0  
**Last Updated:** October 6, 2026  
**Status:** Production Ready
