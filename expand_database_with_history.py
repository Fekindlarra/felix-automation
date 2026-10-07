#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Expandir BD con tablas históricas para tracking long-term
"""

import sqlite3
from datetime import datetime
from pathlib import Path

def create_historical_tables(connection):
    """Crear tablas históricas para análisis long-term"""
    cursor = connection.cursor()

    print("=" * 80)
    print("📊 CREANDO TABLAS HISTÓRICAS")
    print("=" * 80)

    # 1. Prediction Accuracy History
    print("\n[1/3] Creando prediction_accuracy_history...")
    try:
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS prediction_accuracy_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            test_id INTEGER NOT NULL,
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            ml_accuracy_percent REAL,
            rules_accuracy_percent REAL,
            accuracy_gap_percent REAL,
            sample_size INTEGER,
            predictions_hour INTEGER,  -- Predictions tracked in last hour
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (test_id) REFERENCES ab_tests(id)
        )
        """)
        connection.commit()
        print("   ✅ Tabla creada: prediction_accuracy_history")
    except Exception as e:
        print(f"   ❌ Error: {e}")

    # 2. Personalization Performance
    print("\n[2/3] Creando personalization_performance...")
    try:
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS personalization_performance (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            test_id INTEGER NOT NULL,
            rollout_phase INTEGER,
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            assignments_count INTEGER,
            conversion_rate_percent REAL,
            average_confidence REAL,
            performance_lift_percent REAL,  -- vs control group
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (test_id) REFERENCES ab_tests(id)
        )
        """)
        connection.commit()
        print("   ✅ Tabla creada: personalization_performance")
    except Exception as e:
        print(f"   ❌ Error: {e}")

    # 3. System Health History
    print("\n[3/3] Creando system_health_history...")
    try:
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS system_health_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            websocket_latency_ms REAL,
            ml_inference_ms REAL,
            comparison_recording_ms REAL,
            db_query_latency_ms REAL,
            error_rate_percent REAL,
            predictions_per_hour INTEGER,
            personalization_lookups_per_hour INTEGER,
            api_uptime_percent REAL,
            database_uptime_percent REAL,
            notes TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """)
        connection.commit()
        print("   ✅ Tabla creada: system_health_history")
    except Exception as e:
        print(f"   ❌ Error: {e}")

    # Crear índices
    print("\n[ÍNDICES] Creando índices para optimización...")
    try:
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_prediction_acc_test ON prediction_accuracy_history(test_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_prediction_acc_time ON prediction_accuracy_history(timestamp)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_pers_perf_test ON personalization_performance(test_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_pers_perf_phase ON personalization_performance(rollout_phase)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_sys_health_time ON system_health_history(timestamp)")
        connection.commit()
        print("   ✅ 5 índices creados para acceso rápido")
    except Exception as e:
        print(f"   ❌ Error: {e}")

    print("\n" + "=" * 80)
    print("✅ TABLAS HISTÓRICAS CREADAS")
    print("=" * 80)

    # Verificar tablas
    cursor.execute("""
        SELECT name FROM sqlite_master
        WHERE type='table' AND name IN ('prediction_accuracy_history', 'personalization_performance', 'system_health_history')
    """)
    tables = cursor.fetchall()
    print(f"\nTablas históricas activas: {len(tables)}/3")
    for table in tables:
        print(f"  ✅ {table[0]}")

def main():
    """Expandir BD"""
    db = sqlite3.connect('data/pipeline.sqlite')
    create_historical_tables(db)
    db.close()

    print("\n🎉 Base de datos expandida con tracking histórico")

if __name__ == "__main__":
    main()
