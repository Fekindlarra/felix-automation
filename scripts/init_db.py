#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Inicializar BD y crear tablas
"""

import sys
import sqlite3
from pathlib import Path

# Agregar path
sys.path.insert(0, str(Path(__file__).parent.parent))

def init_database():
    """Crear tablas iniciales"""
    db_path = "./data/felix.db"

    # Crear directorio si no existe
    Path("./data").mkdir(exist_ok=True)

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    print("🔧 Inicializando base de datos...")

    # Tabla: Clientes
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS clients (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        domain TEXT,
        email TEXT UNIQUE NOT NULL,
        business_type TEXT DEFAULT 'ecommerce',
        company_size TEXT DEFAULT 'pyme',
        sector TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        notes TEXT
    )
    """)
    print("  ✓ Tabla: clients")

    # Tabla: Auditorías
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS audits (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        client_id INTEGER NOT NULL,
        audit_type TEXT DEFAULT 'web',
        platform TEXT,
        status TEXT DEFAULT 'pending',
        overall_score INTEGER DEFAULT 0,
        metrics_json TEXT DEFAULT '{}',
        raw_data_json TEXT DEFAULT '{}',
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        completed_at TIMESTAMP,
        FOREIGN KEY (client_id) REFERENCES clients(id)
    )
    """)
    print("  ✓ Tabla: audits")

    # Tabla: Lead Scores
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS lead_scores (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        client_id INTEGER UNIQUE NOT NULL,
        web_score INTEGER DEFAULT 0,
        facebook_score INTEGER DEFAULT 0,
        google_score INTEGER DEFAULT 0,
        overall_score INTEGER DEFAULT 0,
        potential_ranking TEXT,
        recommendation TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (client_id) REFERENCES clients(id)
    )
    """)
    print("  ✓ Tabla: lead_scores")

    # Tabla: Propuestas
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS proposals (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        client_id INTEGER NOT NULL,
        audit_ids TEXT,
        estimated_cost INTEGER DEFAULT 0,
        estimated_duration TEXT,
        html_file TEXT,
        pdf_file TEXT,
        status TEXT DEFAULT 'draft',
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        sent_at TIMESTAMP,
        FOREIGN KEY (client_id) REFERENCES clients(id)
    )
    """)
    print("  ✓ Tabla: proposals")

    # Tabla: Sales Pipeline
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS sales_pipeline (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        client_id INTEGER NOT NULL,
        stage TEXT,
        proposal_id INTEGER,
        notes TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (client_id) REFERENCES clients(id),
        UNIQUE(client_id)
    )
    """)
    print("  ✓ Tabla: sales_pipeline")

    # Tabla: Email Logs
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS email_logs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        client_id INTEGER NOT NULL,
        proposal_id INTEGER,
        email_type TEXT,
        recipient TEXT NOT NULL,
        subject TEXT,
        open_count INTEGER DEFAULT 0,
        click_count INTEGER DEFAULT 0,
        sent_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (client_id) REFERENCES clients(id)
    )
    """)
    print("  ✓ Tabla: email_logs")

    # Tabla: Funnel State
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS funnel_state (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        client_id INTEGER UNIQUE NOT NULL,
        stage TEXT,
        entered_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        status TEXT DEFAULT 'active',
        FOREIGN KEY (client_id) REFERENCES clients(id)
    )
    """)
    print("  ✓ Tabla: funnel_state")

    # Tabla: Agent Logs
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS agent_logs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        agent_name TEXT,
        action TEXT,
        status TEXT,
        client_id INTEGER,
        details TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (client_id) REFERENCES clients(id)
    )
    """)
    print("  ✓ Tabla: agent_logs")

    # Tabla: Dashboard Metrics
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS dashboard_metrics (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        metric_name TEXT UNIQUE,
        metric_value TEXT,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """)
    print("  ✓ Tabla: dashboard_metrics")

    conn.commit()
    conn.close()

    print("\n✅ Base de datos inicializada exitosamente")
    print(f"   Ubicación: {db_path}")

if __name__ == "__main__":
    init_database()
