#!/usr/bin/env python3
"""
Setup ML Monitoring and Performance Tracking
Creates views and logging tables for tracking prediction performance
"""

import sys
import os
import sqlite3
from datetime import datetime
from pathlib import Path

def setup_monitoring_tables(db_path):
    """Create monitoring tables for tracking prediction performance"""

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    print("📊 Setting up ML Monitoring Tables...")

    # Prediction log table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS prediction_log (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            client_id TEXT NOT NULL,
            web_score FLOAT,
            facebook_score FLOAT,
            google_score FLOAT,
            business_type TEXT,
            company_size TEXT,
            predicted_probability INTEGER,
            predicted_confidence FLOAT,
            risk_factors TEXT,
            positive_factors TEXT,
            actual_outcome INTEGER,
            outcome_date TIMESTAMP,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (client_id) REFERENCES clients(id)
        )
    """)

    # Model performance metrics table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS model_performance (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            date DATE,
            total_predictions INTEGER DEFAULT 0,
            correct_predictions INTEGER DEFAULT 0,
            accuracy FLOAT,
            average_confidence FLOAT,
            high_confidence_predictions INTEGER DEFAULT 0,
            medium_confidence_predictions INTEGER DEFAULT 0,
            low_confidence_predictions INTEGER DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # Prediction accuracy by score range
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS accuracy_by_range (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            score_range TEXT,
            total_predictions INTEGER,
            correct_predictions INTEGER,
            accuracy FLOAT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    conn.commit()

    # Create views for analysis
    print("📈 Creating analytics views...")

    # Recent predictions view
    cursor.execute("""
        CREATE VIEW IF NOT EXISTS recent_predictions AS
        SELECT
            client_id,
            predicted_probability,
            predicted_confidence,
            CASE
                WHEN actual_outcome IS NOT NULL THEN
                    CASE WHEN (predicted_probability > 50 AND actual_outcome = 1) OR
                              (predicted_probability <= 50 AND actual_outcome = 0)
                         THEN 1 ELSE 0 END
                ELSE NULL
            END as prediction_correct,
            created_at
        FROM prediction_log
        ORDER BY created_at DESC
        LIMIT 100
    """)

    # Daily accuracy view
    cursor.execute("""
        CREATE VIEW IF NOT EXISTS daily_accuracy AS
        SELECT
            DATE(created_at) as date,
            COUNT(*) as total,
            SUM(CASE
                WHEN (predicted_probability > 50 AND actual_outcome = 1) OR
                     (predicted_probability <= 50 AND actual_outcome = 0)
                THEN 1 ELSE 0
            END) as correct,
            ROUND(100.0 * SUM(CASE
                WHEN (predicted_probability > 50 AND actual_outcome = 1) OR
                     (predicted_probability <= 50 AND actual_outcome = 0)
                THEN 1 ELSE 0
            END) / COUNT(*), 2) as accuracy
        FROM prediction_log
        WHERE actual_outcome IS NOT NULL
        GROUP BY DATE(created_at)
        ORDER BY date DESC
    """)

    # Confidence distribution view
    cursor.execute("""
        CREATE VIEW IF NOT EXISTS confidence_distribution AS
        SELECT
            CASE
                WHEN predicted_confidence >= 0.9 THEN 'Very High (≥0.9)'
                WHEN predicted_confidence >= 0.7 THEN 'High (0.7-0.9)'
                WHEN predicted_confidence >= 0.5 THEN 'Medium (0.5-0.7)'
                ELSE 'Low (<0.5)'
            END as confidence_range,
            COUNT(*) as count,
            ROUND(100.0 * COUNT(*) / (SELECT COUNT(*) FROM prediction_log), 2) as percentage
        FROM prediction_log
        GROUP BY confidence_range
    """)

    # Client prediction history view
    cursor.execute("""
        CREATE VIEW IF NOT EXISTS client_prediction_history AS
        SELECT
            client_id,
            COUNT(*) as prediction_count,
            ROUND(AVG(predicted_probability), 2) as avg_probability,
            ROUND(AVG(predicted_confidence), 3) as avg_confidence,
            MIN(created_at) as first_prediction,
            MAX(created_at) as latest_prediction
        FROM prediction_log
        GROUP BY client_id
        ORDER BY prediction_count DESC
    """)

    conn.commit()
    print("✅ Monitoring tables and views created")

    # Print schema info
    print("\n📋 Created Tables:")
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name LIKE 'prediction_%' OR name LIKE 'model_%' OR name LIKE 'accuracy_%'")
    tables = cursor.fetchall()
    for table in tables:
        print(f"   - {table[0]}")

    print("\n📊 Created Views:")
    cursor.execute("SELECT name FROM sqlite_master WHERE type='view' AND name LIKE '%predictions%' OR name LIKE '%accuracy%' OR name LIKE '%confidence%'")
    views = cursor.fetchall()
    for view in views:
        print(f"   - {view[0]}")

    conn.close()
    return True


def create_monitoring_queries():
    """Generate useful monitoring SQL queries"""

    queries = {
        "today_predictions": """
            SELECT COUNT(*) as total,
                   ROUND(AVG(predicted_probability), 2) as avg_probability,
                   ROUND(AVG(predicted_confidence), 3) as avg_confidence
            FROM prediction_log
            WHERE DATE(created_at) = DATE('now')
        """,

        "accuracy_last_7_days": """
            SELECT DATE(created_at) as date,
                   COUNT(*) as total,
                   SUM(CASE
                       WHEN (predicted_probability > 50 AND actual_outcome = 1) OR
                            (predicted_probability <= 50 AND actual_outcome = 0)
                       THEN 1 ELSE 0
                   END) as correct,
                   ROUND(100.0 * SUM(CASE
                       WHEN (predicted_probability > 50 AND actual_outcome = 1) OR
                            (predicted_probability <= 50 AND actual_outcome = 0)
                       THEN 1 ELSE 0
                   END) / COUNT(*), 2) as accuracy
            FROM prediction_log
            WHERE actual_outcome IS NOT NULL AND created_at >= datetime('now', '-7 days')
            GROUP BY DATE(created_at)
        """,

        "model_performance_summary": """
            SELECT
                COUNT(*) as total_predictions,
                ROUND(AVG(predicted_probability), 2) as avg_probability,
                ROUND(AVG(predicted_confidence), 3) as avg_confidence,
                MIN(predicted_confidence) as min_confidence,
                MAX(predicted_confidence) as max_confidence
            FROM prediction_log
            WHERE created_at >= datetime('now', '-30 days')
        """,

        "high_confidence_predictions": """
            SELECT COUNT(*) as count,
                   ROUND(100.0 * COUNT(*) / (SELECT COUNT(*) FROM prediction_log), 2) as percentage
            FROM prediction_log
            WHERE predicted_confidence >= 0.9
        """,
    }

    return queries


def main():
    print("🚀 ML Monitoring Setup")
    print("=" * 60)

    db_path = Path(__file__).parent.parent / 'data' / 'pipeline.db'

    print(f"\n📂 Database: {db_path}")

    if not db_path.exists():
        print("❌ Database not found")
        return 1

    # Setup monitoring
    if setup_monitoring_tables(db_path):
        print("\n✅ Monitoring setup completed successfully")

        # Display monitoring queries
        print("\n" + "=" * 60)
        print("📊 Available Monitoring Queries")
        print("=" * 60)

        queries = create_monitoring_queries()
        for query_name, query_sql in queries.items():
            print(f"\n✓ {query_name}:")
            print(f"  {query_sql.strip()[:70]}...")

        print("\n💾 All queries are stored in SQLite views for easy analysis")
        print("✅ Ready for production monitoring!")

        return 0
    else:
        print("❌ Failed to setup monitoring")
        return 1


if __name__ == '__main__':
    sys.exit(main())
