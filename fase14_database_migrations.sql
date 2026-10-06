-- FASE 14 Database Schema Migrations
-- Production-ready schema for Shopify integration, ML predictions, A/B testing
-- Generado: 2026-10-06

-- ========================================
-- TRACK B: SHOPIFY INTEGRATION (3 tablas)
-- ========================================

-- Store credentials and sync status
CREATE TABLE IF NOT EXISTS shopify_stores (
    store_id INTEGER PRIMARY KEY AUTOINCREMENT,
    client_id INTEGER NOT NULL UNIQUE,
    shop_name TEXT NOT NULL,
    shop_domain TEXT NOT NULL UNIQUE,
    access_token_encrypted TEXT NOT NULL,
    webhook_secret_encrypted TEXT,
    last_sync TIMESTAMP,
    sync_status TEXT DEFAULT 'pending',  -- pending, syncing, active, error
    error_message TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY(client_id) REFERENCES clients(id) ON DELETE CASCADE,
    CHECK(sync_status IN ('pending', 'syncing', 'active', 'error'))
);
CREATE INDEX idx_shopify_stores_client_id ON shopify_stores(client_id);
CREATE INDEX idx_shopify_stores_sync_status ON shopify_stores(sync_status);

-- Order analytics and revenue tracking
CREATE TABLE IF NOT EXISTS shopify_orders (
    order_id INTEGER PRIMARY KEY AUTOINCREMENT,
    store_id INTEGER NOT NULL,
    shopify_order_id TEXT NOT NULL UNIQUE,
    customer_id TEXT,
    total_price DECIMAL(10, 2),
    currency TEXT DEFAULT 'USD',
    order_status TEXT,
    created_at_shopify TIMESTAMP,
    updated_at_shopify TIMESTAMP,
    synced_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY(store_id) REFERENCES shopify_stores(store_id) ON DELETE CASCADE,
    CHECK(total_price >= 0)
);
CREATE INDEX idx_shopify_orders_store_id ON shopify_orders(store_id);
CREATE INDEX idx_shopify_orders_created_at ON shopify_orders(created_at_shopify);
CREATE INDEX idx_shopify_orders_status ON shopify_orders(order_status);

-- Webhook configuration and event logging
CREATE TABLE IF NOT EXISTS shopify_webhooks (
    webhook_id INTEGER PRIMARY KEY AUTOINCREMENT,
    store_id INTEGER NOT NULL,
    shopify_webhook_id TEXT UNIQUE,
    topic TEXT NOT NULL,  -- orders/created, orders/updated, products/updated, etc.
    webhook_url TEXT NOT NULL,
    active INTEGER DEFAULT 1,
    registered_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_event_at TIMESTAMP,
    event_count INTEGER DEFAULT 0,
    FOREIGN KEY(store_id) REFERENCES shopify_stores(store_id) ON DELETE CASCADE,
    CHECK(topic IN ('orders/created', 'orders/updated', 'orders/deleted', 'products/created', 'products/updated', 'products/deleted'))
);
CREATE INDEX idx_shopify_webhooks_store_id ON shopify_webhooks(store_id);
CREATE INDEX idx_shopify_webhooks_topic ON shopify_webhooks(topic);


-- ========================================
-- TRACK C: ML PREDICTIONS (1 tabla)
-- ========================================

-- Prediction history for accuracy tracking and analysis
CREATE TABLE IF NOT EXISTS prediction_history (
    prediction_id INTEGER PRIMARY KEY AUTOINCREMENT,
    client_id INTEGER NOT NULL,
    probability DECIMAL(5, 2) NOT NULL,  -- 0-100, e.g., 78.50
    confidence DECIMAL(5, 2) NOT NULL,   -- 0-100, e.g., 92.00
    risk_factors TEXT,  -- JSON array of risk factors
    positive_factors TEXT,  -- JSON array of positive factors
    predicted_timeline_days INTEGER,
    anomaly_flags TEXT,  -- JSON array of anomalies
    recommendation TEXT,
    actual_outcome TEXT,  -- 'converted', 'churned', 'pending', null
    outcome_date TIMESTAMP,
    predicted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY(client_id) REFERENCES clients(id) ON DELETE CASCADE,
    CHECK(probability >= 0 AND probability <= 100),
    CHECK(confidence >= 0 AND confidence <= 100),
    CHECK(actual_outcome IS NULL OR actual_outcome IN ('converted', 'churned', 'pending'))
);
CREATE INDEX idx_prediction_history_client_id ON prediction_history(client_id);
CREATE INDEX idx_prediction_history_predicted_at ON prediction_history(predicted_at);
CREATE INDEX idx_prediction_history_probability ON prediction_history(probability);


-- ========================================
-- TRACK D: EMAIL A/B TESTING (3 tablas)
-- ========================================

-- A/B test configuration
CREATE TABLE IF NOT EXISTS ab_tests (
    test_id INTEGER PRIMARY KEY AUTOINCREMENT,
    test_name TEXT NOT NULL,
    email_type TEXT NOT NULL,  -- welcome, followup, promotional, etc.
    variant_a_name TEXT DEFAULT 'Variant A',
    variant_b_name TEXT DEFAULT 'Variant B',
    variant_a_template TEXT,  -- HTML template for variant A
    variant_b_template TEXT,  -- HTML template for variant B
    active INTEGER DEFAULT 1,
    start_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    end_date TIMESTAMP,
    winner TEXT,  -- 'A', 'B', or NULL if no clear winner
    p_value DECIMAL(5, 4),  -- e.g., 0.0420
    confidence_level DECIMAL(5, 2),  -- e.g., 95.80
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CHECK(active IN (0, 1)),
    CHECK(winner IS NULL OR winner IN ('A', 'B')),
    CHECK(p_value IS NULL OR (p_value >= 0 AND p_value <= 1)),
    CHECK(confidence_level IS NULL OR (confidence_level >= 0 AND confidence_level <= 100))
);
CREATE INDEX idx_ab_tests_active ON ab_tests(active);
CREATE INDEX idx_ab_tests_email_type ON ab_tests(email_type);
CREATE INDEX idx_ab_tests_start_date ON ab_tests(start_date);

-- Per-client A/B test tracking (opens, clicks, conversions)
CREATE TABLE IF NOT EXISTS ab_test_results (
    result_id INTEGER PRIMARY KEY AUTOINCREMENT,
    test_id INTEGER NOT NULL,
    variant TEXT NOT NULL,  -- 'A' or 'B'
    sent_count INTEGER DEFAULT 0,
    open_count INTEGER DEFAULT 0,
    click_count INTEGER DEFAULT 0,
    conversion_count INTEGER DEFAULT 0,
    revenue DECIMAL(10, 2) DEFAULT 0,
    tracked_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY(test_id) REFERENCES ab_tests(test_id) ON DELETE CASCADE,
    CHECK(variant IN ('A', 'B')),
    CHECK(sent_count >= 0),
    CHECK(open_count >= 0),
    CHECK(click_count >= 0),
    CHECK(conversion_count >= 0),
    CHECK(revenue >= 0)
);
CREATE INDEX idx_ab_test_results_test_id ON ab_test_results(test_id);
CREATE INDEX idx_ab_test_results_variant ON ab_test_results(variant);

-- Variant assignment audit trail (which client got which variant)
CREATE TABLE IF NOT EXISTS ab_test_assignments (
    assignment_id INTEGER PRIMARY KEY AUTOINCREMENT,
    test_id INTEGER NOT NULL,
    client_id INTEGER NOT NULL,
    variant TEXT NOT NULL,  -- 'A' or 'B'
    template_name TEXT,
    assigned_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    email_sent_at TIMESTAMP,
    FOREIGN KEY(test_id) REFERENCES ab_tests(test_id) ON DELETE CASCADE,
    FOREIGN KEY(client_id) REFERENCES clients(id) ON DELETE CASCADE,
    CHECK(variant IN ('A', 'B')),
    UNIQUE(test_id, client_id)  -- One assignment per client per test
);
CREATE INDEX idx_ab_test_assignments_test_id ON ab_test_assignments(test_id);
CREATE INDEX idx_ab_test_assignments_client_id ON ab_test_assignments(client_id);
CREATE INDEX idx_ab_test_assignments_variant ON ab_test_assignments(variant);
CREATE INDEX idx_ab_test_assignments_assigned_at ON ab_test_assignments(assigned_at);


-- ========================================
-- TRACK C: ANOMALY DETECTION (1 tabla)
-- ========================================

-- Anomaly detection and alerts
CREATE TABLE IF NOT EXISTS anomalies (
    anomaly_id INTEGER PRIMARY KEY AUTOINCREMENT,
    client_id INTEGER NOT NULL,
    anomaly_type TEXT NOT NULL,  -- conversion_drop, engagement_drop, unusual_pattern, etc.
    severity TEXT NOT NULL DEFAULT 'medium',  -- low, medium, high, critical
    description TEXT,
    detection_data TEXT,  -- JSON with anomaly details
    detected_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    resolved_at TIMESTAMP,
    resolution_notes TEXT,
    FOREIGN KEY(client_id) REFERENCES clients(id) ON DELETE CASCADE,
    CHECK(anomaly_type IN ('conversion_drop', 'engagement_drop', 'unusual_pattern', 'revenue_anomaly', 'activity_spike')),
    CHECK(severity IN ('low', 'medium', 'high', 'critical'))
);
CREATE INDEX idx_anomalies_client_id ON anomalies(client_id);
CREATE INDEX idx_anomalies_detected_at ON anomalies(detected_at);
CREATE INDEX idx_anomalies_severity ON anomalies(severity);
CREATE INDEX idx_anomalies_resolved_at ON anomalies(resolved_at);


-- ========================================
-- VIEWS FOR COMMON QUERIES
-- ========================================

-- A/B Test summary: Conversion rates by variant
CREATE VIEW IF NOT EXISTS v_ab_test_summary AS
SELECT
    t.test_id,
    t.test_name,
    t.email_type,
    r.variant,
    r.sent_count,
    r.open_count,
    ROUND(CAST(r.open_count AS FLOAT) / NULLIF(r.sent_count, 0) * 100, 2) AS open_rate,
    r.click_count,
    ROUND(CAST(r.click_count AS FLOAT) / NULLIF(r.sent_count, 0) * 100, 2) AS click_rate,
    r.conversion_count,
    ROUND(CAST(r.conversion_count AS FLOAT) / NULLIF(r.sent_count, 0) * 100, 2) AS conversion_rate,
    ROUND(r.revenue / NULLIF(r.conversion_count, 0), 2) AS avg_order_value,
    t.winner,
    t.p_value,
    t.confidence_level,
    t.start_date,
    t.end_date
FROM ab_tests t
LEFT JOIN ab_test_results r ON t.test_id = r.test_id
ORDER BY t.test_id DESC, r.variant;

-- Shopify store analytics summary
CREATE VIEW IF NOT EXISTS v_shopify_analytics AS
SELECT
    s.store_id,
    s.shop_name,
    s.client_id,
    s.sync_status,
    COUNT(DISTINCT o.order_id) AS total_orders,
    ROUND(SUM(o.total_price), 2) AS total_revenue,
    ROUND(AVG(o.total_price), 2) AS avg_order_value,
    ROUND(COUNT(DISTINCT o.customer_id) / NULLIF(COUNT(DISTINCT o.order_id), 0) * 100, 2) AS repeat_customer_rate,
    s.last_sync
FROM shopify_stores s
LEFT JOIN shopify_orders o ON s.store_id = o.store_id
GROUP BY s.store_id, s.shop_name, s.client_id, s.sync_status, s.last_sync
ORDER BY total_revenue DESC NULLS LAST;

-- Recent anomalies by severity
CREATE VIEW IF NOT EXISTS v_active_anomalies AS
SELECT
    a.anomaly_id,
    c.name AS client_name,
    a.client_id,
    a.anomaly_type,
    a.severity,
    a.description,
    a.detected_at,
    CASE
        WHEN a.resolved_at IS NULL THEN 'Active'
        ELSE 'Resolved'
    END AS status,
    a.resolution_notes
FROM anomalies a
JOIN clients c ON a.client_id = c.id
WHERE a.resolved_at IS NULL OR datetime(a.resolved_at) > datetime('now', '-7 days')
ORDER BY
    CASE a.severity
        WHEN 'critical' THEN 1
        WHEN 'high' THEN 2
        WHEN 'medium' THEN 3
        ELSE 4
    END,
    a.detected_at DESC;


-- ========================================
-- TRIGGERS FOR AUTOMATIC UPDATES
-- ========================================

-- Auto-update shopify_stores.updated_at
CREATE TRIGGER IF NOT EXISTS trg_shopify_stores_updated_at
AFTER UPDATE ON shopify_stores
BEGIN
    UPDATE shopify_stores SET updated_at = CURRENT_TIMESTAMP
    WHERE store_id = NEW.store_id;
END;

-- Auto-update prediction_history.updated_at
CREATE TRIGGER IF NOT EXISTS trg_prediction_history_updated_at
AFTER UPDATE ON prediction_history
BEGIN
    UPDATE prediction_history SET updated_at = CURRENT_TIMESTAMP
    WHERE prediction_id = NEW.prediction_id;
END;

-- Auto-update ab_tests.updated_at
CREATE TRIGGER IF NOT EXISTS trg_ab_tests_updated_at
AFTER UPDATE ON ab_tests
BEGIN
    UPDATE ab_tests SET updated_at = CURRENT_TIMESTAMP
    WHERE test_id = NEW.test_id;
END;

-- Auto-update ab_test_results.updated_at
CREATE TRIGGER IF NOT EXISTS trg_ab_test_results_updated_at
AFTER UPDATE ON ab_test_results
BEGIN
    UPDATE ab_test_results SET updated_at = CURRENT_TIMESTAMP
    WHERE result_id = NEW.result_id;
END;


-- ========================================
-- VERIFICATION QUERIES
-- ========================================

-- Verify all tables created successfully
-- SELECT name FROM sqlite_master WHERE type='table' AND name LIKE 'shopify_%' OR name LIKE 'ab_test%' OR name LIKE 'prediction_%' OR name LIKE 'anomal%';

-- Verify all indexes created
-- SELECT name FROM sqlite_master WHERE type='index' AND name LIKE 'idx_%';

-- Verify all views created
-- SELECT name FROM sqlite_master WHERE type='view' AND name LIKE 'v_%';
