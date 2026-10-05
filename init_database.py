#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Base de Datos SQLite - Schema para Felix Automation (Opción C)
Gestiona: Pipeline, Funnel, Auditorías y Logs
"""

import sqlite3
import json
from datetime import datetime
from pathlib import Path

class DatabaseManager:
    """Gestor de base de datos SQLite para Felix Automation"""

    def __init__(self, db_path="./felix_automation.db"):
        self.db_path = Path(db_path)
        self.connection = None

    def connect(self):
        """Conectar a la base de datos"""
        self.connection = sqlite3.connect(str(self.db_path))
        self.connection.row_factory = sqlite3.Row
        self.connection.execute("PRAGMA foreign_keys = ON")
        print(f"✅ Conectado a: {self.db_path}")
        return self.connection

    def init_schema(self):
        """Inicializar schema completo"""
        cursor = self.connection.cursor()

        # ====== TABLA: CLIENTES ======
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS clients (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL UNIQUE,
            domain TEXT,
            email TEXT UNIQUE,
            business_type TEXT DEFAULT 'ecommerce',
            company_size TEXT DEFAULT 'pyme',
            sector TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            notes TEXT
        )
        """)

        # ====== TABLA: AUDITORÍAS ======
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS audits (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            client_id INTEGER NOT NULL,
            audit_type TEXT NOT NULL,
            platform TEXT NOT NULL,
            status TEXT DEFAULT 'pending',
            overall_score INTEGER,
            metrics_json TEXT,
            raw_data_json TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            completed_at TIMESTAMP,
            FOREIGN KEY (client_id) REFERENCES clients(id)
        )
        """)

        # ====== TABLA: PROPUESTAS ======
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS proposals (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            client_id INTEGER NOT NULL,
            audit_ids TEXT,
            estimated_cost INTEGER,
            estimated_duration TEXT,
            html_file TEXT,
            pdf_file TEXT,
            status TEXT DEFAULT 'draft',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            sent_at TIMESTAMP,
            FOREIGN KEY (client_id) REFERENCES clients(id)
        )
        """)

        # ====== TABLA: PIPELINE DE VENTAS ======
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS sales_pipeline (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            client_id INTEGER NOT NULL,
            stage TEXT NOT NULL,
            proposal_id INTEGER,
            notes TEXT,
            entered_stage_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            expected_transition_date TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (client_id) REFERENCES clients(id),
            FOREIGN KEY (proposal_id) REFERENCES proposals(id)
        )
        """)

        # ====== TABLA: LEAD SCORES ======
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS lead_scores (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            client_id INTEGER NOT NULL,
            web_score INTEGER,
            facebook_score INTEGER,
            google_score INTEGER,
            overall_score INTEGER,
            potential_ranking TEXT,
            calculated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (client_id) REFERENCES clients(id)
        )
        """)

        # ====== TABLA: EMAILS ENVIADOS ======
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS email_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            client_id INTEGER NOT NULL,
            proposal_id INTEGER,
            email_type TEXT,
            recipient TEXT,
            subject TEXT,
            sent_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            status TEXT DEFAULT 'sent',
            sendgrid_message_id TEXT,
            open_count INTEGER DEFAULT 0,
            click_count INTEGER DEFAULT 0,
            FOREIGN KEY (client_id) REFERENCES clients(id),
            FOREIGN KEY (proposal_id) REFERENCES proposals(id)
        )
        """)

        # ====== TABLA: SEGUIMIENTOS ======
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS followups (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            client_id INTEGER NOT NULL,
            email_log_id INTEGER,
            scheduled_for TIMESTAMP,
            sequence_day INTEGER,
            status TEXT DEFAULT 'pending',
            sent_at TIMESTAMP,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (client_id) REFERENCES clients(id),
            FOREIGN KEY (email_log_id) REFERENCES email_logs(id)
        )
        """)

        # ====== TABLA: EMBUDO (FUNNEL) ======
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS funnel_state (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            client_id INTEGER NOT NULL,
            stage TEXT NOT NULL,
            entered_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            days_in_stage INTEGER DEFAULT 0,
            status TEXT DEFAULT 'active',
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (client_id) REFERENCES clients(id),
            UNIQUE(client_id, stage)
        )
        """)

        # ====== TABLA: LOGS DE AGENTES ======
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS agent_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            agent_name TEXT NOT NULL,
            action TEXT NOT NULL,
            client_id INTEGER,
            status TEXT DEFAULT 'success',
            details TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (client_id) REFERENCES clients(id)
        )
        """)

        # ====== TABLA: MÉTRICAS DE DASHBOARD ======
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS dashboard_metrics (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            metric_name TEXT NOT NULL,
            metric_value TEXT,
            calculated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(metric_name)
        )
        """)

        # ====== ÍNDICES ======
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_clients_email ON clients(email)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_audits_client ON audits(client_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_pipeline_stage ON sales_pipeline(stage)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_email_logs_client ON email_logs(client_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_funnel_state_client ON funnel_state(client_id)")

        self.connection.commit()
        print("✅ Schema de base de datos inicializado")

    def seed_sample_data(self):
        """Cargar datos de ejemplo para pruebas"""
        cursor = self.connection.cursor()

        sample_clients = [
            ("Raíces de Cauquenes", "raicesdecauquenes.cl", "info@raices.cl", "plants", "pyme", "jardinería"),
            ("TechShop Premium", "techshop.cl", "admin@techshop.cl", "ecommerce", "pyme", "tecnología"),
            ("ConsultorLabs", "consultorlabs.cl", "hello@consultorlabs.cl", "services", "startup", "consultoría"),
        ]

        for name, domain, email, btype, size, sector in sample_clients:
            try:
                cursor.execute("""
                INSERT INTO clients (name, domain, email, business_type, company_size, sector)
                VALUES (?, ?, ?, ?, ?, ?)
                """, (name, domain, email, btype, size, sector))
            except sqlite3.IntegrityError:
                pass

        self.connection.commit()
        print("✅ Datos de ejemplo cargados")

    def close(self):
        """Cerrar conexión"""
        if self.connection:
            self.connection.close()
            print("✅ Conexión cerrada")


def main():
    """Inicializar base de datos"""
    db = DatabaseManager("./felix_automation.db")
    db.connect()
    db.init_schema()
    db.seed_sample_data()
    db.close()
    print("\n" + "="*60)
    print("✅ BASE DE DATOS INICIALIZADA CORRECTAMENTE")
    print("="*60)


if __name__ == "__main__":
    main()
