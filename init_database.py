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

    def __init__(self, db_path="data/pipeline.sqlite"):
        # Production deployment uses data/pipeline.sqlite
        self.db_path = Path(db_path)
        # Ensure parent directory exists
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
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

        # ========== FASE 14: NEW TABLES ==========

        # ====== TABLA: SHOPIFY STORES (Real API Integration) ======
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS shopify_stores (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            client_id INTEGER NOT NULL UNIQUE,
            shop_domain TEXT NOT NULL UNIQUE,
            access_token_encrypted TEXT NOT NULL,
            access_token_iv TEXT,
            shop_name TEXT,
            currency TEXT DEFAULT 'USD',
            timezone TEXT,
            plan TEXT,
            email TEXT,
            phone TEXT,
            last_sync TIMESTAMP,
            sync_status TEXT DEFAULT 'pending',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (client_id) REFERENCES clients(id)
        )
        """)

        # ====== TABLA: SHOPIFY ORDERS ======
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS shopify_orders (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            store_id INTEGER NOT NULL,
            shopify_order_id TEXT NOT NULL,
            order_number INTEGER,
            customer_email TEXT,
            total_price REAL,
            subtotal_price REAL,
            total_tax REAL,
            total_shipping REAL,
            currency TEXT DEFAULT 'USD',
            status TEXT,
            fulfillment_status TEXT,
            payment_status TEXT,
            created_at_shopify TIMESTAMP,
            updated_at_shopify TIMESTAMP,
            synced_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (store_id) REFERENCES shopify_stores(id),
            UNIQUE(store_id, shopify_order_id)
        )
        """)

        # ====== TABLA: SHOPIFY WEBHOOKS ======
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS shopify_webhooks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            store_id INTEGER NOT NULL,
            webhook_id TEXT NOT NULL,
            topic TEXT NOT NULL,
            url TEXT,
            active BOOLEAN DEFAULT 1,
            last_triggered TIMESTAMP,
            trigger_count INTEGER DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (store_id) REFERENCES shopify_stores(id),
            UNIQUE(store_id, webhook_id)
        )
        """)

        # ====== TABLA: PREDICTION HISTORY (ML Accuracy Tracking) ======
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS prediction_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            client_id INTEGER NOT NULL,
            probability REAL NOT NULL,
            confidence REAL NOT NULL,
            risk_factors_json TEXT,
            positive_factors_json TEXT,
            predicted_timeline_days INTEGER,
            actual_outcome TEXT,
            prediction_correct BOOLEAN,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            outcome_recorded_at TIMESTAMP,
            FOREIGN KEY (client_id) REFERENCES clients(id)
        )
        """)

        # ====== TABLA: A/B TESTS ======
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS ab_tests (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            test_name TEXT NOT NULL,
            email_type TEXT NOT NULL,
            variant_a_subject TEXT,
            variant_a_body TEXT,
            variant_b_subject TEXT,
            variant_b_body TEXT,
            active BOOLEAN DEFAULT 1,
            start_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            end_date TIMESTAMP,
            planned_duration_days INTEGER DEFAULT 14,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """)

        # ====== TABLA: A/B TEST RESULTS ======
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS ab_test_results (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            test_id INTEGER NOT NULL,
            client_id INTEGER NOT NULL,
            variant TEXT NOT NULL,
            sent_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            opened BOOLEAN DEFAULT 0,
            opened_at TIMESTAMP,
            clicked BOOLEAN DEFAULT 0,
            clicked_at TIMESTAMP,
            converted BOOLEAN DEFAULT 0,
            converted_at TIMESTAMP,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (test_id) REFERENCES ab_tests(id),
            FOREIGN KEY (client_id) REFERENCES clients(id)
        )
        """)

        # ========== FASE 15 PHASE 3: A/B Testing + ML Comparison Tables ==========

        # ====== TABLA: AB_TEST_ML_PREDICTIONS (ML vs Rules Comparison Tracking) ======
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS ab_test_ml_predictions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            test_id INTEGER NOT NULL,
            client_id INTEGER NOT NULL,
            ml_probability REAL NOT NULL,
            rules_probability REAL NOT NULL,
            actual_outcome INTEGER,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            outcome_date TIMESTAMP,
            FOREIGN KEY (test_id) REFERENCES ab_tests(id),
            FOREIGN KEY (client_id) REFERENCES clients(id),
            UNIQUE(test_id, client_id)
        )
        """)

        # ====== TABLA: PERSONALIZATION_VARIANTS (Winner Application & Gradual Rollout) ======
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS personalization_variants (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            client_id INTEGER NOT NULL,
            test_id INTEGER NOT NULL,
            winning_variant TEXT NOT NULL,
            rollout_phase INTEGER DEFAULT 1,
            applied_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            effective_until TIMESTAMP,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (test_id) REFERENCES ab_tests(id),
            FOREIGN KEY (client_id) REFERENCES clients(id),
            UNIQUE(test_id, client_id)
        )
        """)

        # ====== TABLA: COMPARISON_REPORTS (ML vs Rules Summary Reports) ======
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS comparison_reports (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            test_id INTEGER NOT NULL,
            ml_accuracy REAL,
            rules_accuracy REAL,
            ml_avg_confidence REAL,
            winner TEXT,
            confidence_interval TEXT,
            sample_size INTEGER,
            generated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (test_id) REFERENCES ab_tests(id),
            UNIQUE(test_id)
        )
        """)

        # ====== TABLA: ANOMALIES (Detection & Tracking) ======
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS anomalies (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            client_id INTEGER NOT NULL,
            anomaly_type TEXT NOT NULL,
            severity TEXT DEFAULT 'medium',
            description TEXT,
            metrics_json TEXT,
            detected_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            resolved BOOLEAN DEFAULT 0,
            resolved_at TIMESTAMP,
            notes TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (client_id) REFERENCES clients(id)
        )
        """)

        # ====== ÍNDICES ======
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_clients_email ON clients(email)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_audits_client ON audits(client_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_pipeline_stage ON sales_pipeline(stage)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_email_logs_client ON email_logs(client_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_funnel_state_client ON funnel_state(client_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_shopify_stores_client ON shopify_stores(client_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_shopify_orders_store ON shopify_orders(store_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_prediction_history_client ON prediction_history(client_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_ab_test_results_test ON ab_test_results(test_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_ab_test_results_client ON ab_test_results(client_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_anomalies_client ON anomalies(client_id)")
        # FASE 15 Phase 3 indices
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_ab_test_ml_predictions_test ON ab_test_ml_predictions(test_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_ab_test_ml_predictions_client ON ab_test_ml_predictions(client_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_personalization_variants_test ON personalization_variants(test_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_personalization_variants_client ON personalization_variants(client_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_comparison_reports_test ON comparison_reports(test_id)")

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
    """Inicializar base de datos - usa ruta de producción"""
    db = DatabaseManager("data/pipeline.sqlite")  # Production path
    db.connect()
    db.init_schema()
    db.seed_sample_data()
    db.close()
    print("\n" + "="*60)
    print("✅ BASE DE DATOS INICIALIZADA CORRECTAMENTE EN: data/pipeline.sqlite")
    print("="*60)


if __name__ == "__main__":
    main()
