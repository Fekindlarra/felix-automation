#!/usr/bin/env python3
"""
FELIX AUTOMATION - OPCIÓN C ORCHESTRATOR
Sistema de Automatización de Ventas End-to-End
Version 8.0 - Production Ready
"""

import os
import sys
import yaml
import json
import sqlite3
import logging
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Any
import traceback

# Importar agentes (existentes desde FASE 8)
try:
    from agents.multi_platform_auditor_agent import MultiPlatformAuditorAgent
    from agents.lead_scorer_agent import LeadScorerAgent
    from agents.proposal_generator_agent import ProposalGeneratorAgent
    from agents.email_sender_agent import EmailSenderAgent
    from agents.followup_agent import FollowUpAgent
    from agents.sales_pipeline_agent import SalesPipelineAgent
    from agents.funnel_management_agent import FunnelManagementAgent
except ImportError as e:
    print(f"Error importando agentes: {e}")
    sys.exit(1)


class ConfigManager:
    """Gestor centralizado de configuración"""
    
    def __init__(self, config_path: str = "config.yaml"):
        self.config_path = config_path
        self.config = self._load_config()
    
    def _load_config(self) -> Dict:
        """Carga configuración desde YAML y variables de entorno"""
        try:
            with open(self.config_path, 'r', encoding='utf-8') as f:
                config = yaml.safe_load(f)
        except FileNotFoundError:
            print(f"❌ Archivo de configuración no encontrado: {self.config_path}")
            sys.exit(1)
        
        # Sobrescribir con variables de entorno si existen
        # Formato: FELIX_<SECTION>_<KEY>
        for key, value in os.environ.items():
            if key.startswith('FELIX_'):
                parts = key[6:].lower().split('_')
                if len(parts) >= 2:
                    section = parts[0]
                    subkey = '_'.join(parts[1:])
                    if section in config:
                        config[section][subkey] = value
        
        return config
    
    def get(self, section: str, key: str = None, default=None):
        """Obtener valor de configuración"""
        if section not in self.config:
            return default
        
        if key is None:
            return self.config[section]
        
        return self.config[section].get(key, default)


class DatabaseManager:
    """Gestor de base de datos SQLite"""
    
    def __init__(self, db_path: str):
        self.db_path = db_path
        self.conn = None
        self._initialize()
    
    def _initialize(self):
        """Inicializar base de datos y crear tablas si no existen"""
        self.conn = sqlite3.connect(self.db_path)
        self.conn.row_factory = sqlite3.Row
        
        cursor = self.conn.cursor()
        
        # Tabla de clientes
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS clients (
                id INTEGER PRIMARY KEY,
                name TEXT NOT NULL,
                email TEXT,
                company TEXT,
                industry TEXT,
                stage TEXT DEFAULT 'prospecto',
                score INTEGER,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Tabla de auditorías
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS audits (
                id INTEGER PRIMARY KEY,
                client_id INTEGER NOT NULL,
                platform TEXT,  -- 'web', 'facebook_ads', 'google_ads'
                score INTEGER,
                details JSON,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (client_id) REFERENCES clients(id)
            )
        """)
        
        # Tabla de propuestas
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS proposals (
                id INTEGER PRIMARY KEY,
                client_id INTEGER NOT NULL,
                html_content TEXT,
                pdf_path TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                sent_at TIMESTAMP,
                FOREIGN KEY (client_id) REFERENCES clients(id)
            )
        """)
        
        # Tabla de emails
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS emails (
                id INTEGER PRIMARY KEY,
                client_id INTEGER NOT NULL,
                type TEXT,  -- 'proposal', 'followup'
                subject TEXT,
                status TEXT DEFAULT 'pending',  -- pending, sent, failed, opened
                sent_at TIMESTAMP,
                opened_at TIMESTAMP,
                FOREIGN KEY (client_id) REFERENCES clients(id)
            )
        """)
        
        # Tabla de pipeline
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS pipeline_history (
                id INTEGER PRIMARY KEY,
                client_id INTEGER NOT NULL,
                from_stage TEXT,
                to_stage TEXT,
                reason TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (client_id) REFERENCES clients(id)
            )
        """)
        
        self.conn.commit()
    
    def get_client(self, client_id: int) -> Optional[Dict]:
        """Obtener cliente por ID"""
        cursor = self.conn.cursor()
        cursor.execute("SELECT * FROM clients WHERE id = ?", (client_id,))
        row = cursor.fetchone()
        return dict(row) if row else None
    
    def get_all_clients(self) -> List[Dict]:
        """Obtener todos los clientes"""
        cursor = self.conn.cursor()
        cursor.execute("SELECT * FROM clients ORDER BY id")
        return [dict(row) for row in cursor.fetchall()]
    
    def update_client_stage(self, client_id: int, new_stage: str, reason: str = ""):
        """Actualizar etapa del cliente en el pipeline"""
        cursor = self.conn.cursor()
        
        # Obtener etapa actual
        cursor.execute("SELECT stage FROM clients WHERE id = ?", (client_id,))
        row = cursor.fetchone()
        old_stage = row['stage'] if row else 'prospecto'
        
        # Actualizar cliente
        cursor.execute(
            "UPDATE clients SET stage = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?",
            (new_stage, client_id)
        )
        
        # Registrar en historial
        cursor.execute(
            """INSERT INTO pipeline_history (client_id, from_stage, to_stage, reason)
               VALUES (?, ?, ?, ?)""",
            (client_id, old_stage, new_stage, reason)
        )
        
        self.conn.commit()
    
    def close(self):
        """Cerrar conexión"""
        if self.conn:
            self.conn.close()


class OrchestratorOpcionC:
    """Orquestador principal de OPCIÓN C"""
    
    def __init__(self, config_path: str = "config.yaml"):
        self.config = ConfigManager(config_path)
        self.db = DatabaseManager(self.config.get('database', 'path'))
        self.logger = self._setup_logging()
        
        # Inicializar agentes
        self.auditor = MultiPlatformAuditorAgent()
        self.scorer = LeadScorerAgent()
        self.generator = ProposalGeneratorAgent()
        self.sender = EmailSenderAgent()
        self.followup = FollowUpAgent()
        self.pipeline = SalesPipelineAgent()
        self.funnel = FunnelManagementAgent()
        
        self.start_time = None
        self.execution_summary = {
            "timestamp": None,
            "version": "8.0",
            "total_clients": 0,
            "processed": 0,
            "errors": 0,
            "steps": {},
            "duration_seconds": 0
        }
    
    def _setup_logging(self) -> logging.Logger:
        """Configurar logging"""
        log_level = self.config.get('logging', 'level', 'INFO')
        log_file = self.config.get('logging', 'file', 'data/logs/sistema.log')
        
        # Crear directorio de logs si no existe
        Path(log_file).parent.mkdir(parents=True, exist_ok=True)
        
        logger = logging.getLogger('OrchestratorOpcionC')
        logger.setLevel(getattr(logging, log_level))
        
        # Handler a archivo
        handler = logging.FileHandler(log_file)
        handler.setLevel(getattr(logging, log_level))
        
        # Formato
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        
        return logger
    
    def execute_9_step_pipeline(self, client_ids: Optional[List[int]] = None) -> Dict:
        """Ejecutar pipeline completo de 9 pasos"""
        self.start_time = datetime.now()
        self.execution_summary["timestamp"] = self.start_time.isoformat()
        
        # Obtener clientes a procesar
        if client_ids is None:
            clients = self.db.get_all_clients()
        else:
            clients = [self.db.get_client(cid) for cid in client_ids if self.db.get_client(cid)]
        
        self.execution_summary["total_clients"] = len(clients)
        self.logger.info(f"Iniciando pipeline para {len(clients)} clientes")
        
        # 9 Pasos del pipeline
        steps = [
            ("Auditoría Multi-Plataforma", self._step_1_audit),
            ("Cálculo de Lead Scores", self._step_2_scoring),
            ("Generación de Propuestas", self._step_3_proposals),
            ("Envío de Emails", self._step_4_emails),
            ("Secuencias de Follow-up", self._step_5_followup),
            ("Actualización del Pipeline", self._step_6_pipeline_update),
            ("Generación de Dashboards", self._step_7_dashboards),
            ("Generación de Reportes", self._step_8_reports),
            ("Resumen de Ejecución", self._step_9_summary)
        ]
        
        for step_num, (step_name, step_func) in enumerate(steps, 1):
            try:
                self.logger.info(f"PASO {step_num}: {step_name}")
                result = step_func(clients)
                self.execution_summary["steps"][f"paso_{step_num}"] = {
                    "name": step_name,
                    "status": "completed",
                    "details": result
                }
                self.execution_summary["processed"] += result.get("processed", 0)
            except Exception as e:
                self.logger.error(f"Error en PASO {step_num} ({step_name}): {str(e)}")
                self.logger.error(traceback.format_exc())
                self.execution_summary["steps"][f"paso_{step_num}"] = {
                    "name": step_name,
                    "status": "error",
                    "error": str(e)
                }
                self.execution_summary["errors"] += 1
        
        # Calcular duración
        duration = datetime.now() - self.start_time
        self.execution_summary["duration_seconds"] = duration.total_seconds()
        
        self.logger.info(f"Pipeline completado en {duration.total_seconds():.2f} segundos")
        return self.execution_summary
    
    def _step_1_audit(self, clients: List[Dict]) -> Dict:
        """PASO 1: Auditoría Multi-Plataforma"""
        result = {"processed": 0, "audits": []}
        for client in clients:
            try:
                audit = self.auditor.audit_client(
                    client['id'],
                    platforms=['web', 'facebook_ads', 'google_ads']
                )
                result["audits"].append(audit)
                result["processed"] += 1
            except Exception as e:
                self.logger.error(f"Error auditando cliente {client['id']}: {e}")
        return result
    
    def _step_2_scoring(self, clients: List[Dict]) -> Dict:
        """PASO 2: Cálculo de Lead Scores"""
        result = {"processed": 0, "scores": []}
        for client in clients:
            try:
                score = self.scorer.score_lead(client['id'])
                result["scores"].append({"client_id": client['id'], "score": score})
                result["processed"] += 1
            except Exception as e:
                self.logger.error(f"Error calculando score para cliente {client['id']}: {e}")
        return result
    
    def _step_3_proposals(self, clients: List[Dict]) -> Dict:
        """PASO 3: Generación de Propuestas"""
        result = {"processed": 0, "proposals": []}
        for client in clients:
            try:
                proposal_id = self.generator.generate_proposal(client['id'], [])
                result["proposals"].append({"client_id": client['id'], "proposal_id": proposal_id})
                result["processed"] += 1
            except Exception as e:
                self.logger.error(f"Error generando propuesta para cliente {client['id']}: {e}")
        return result
    
    def _step_4_emails(self, clients: List[Dict]) -> Dict:
        """PASO 4: Envío de Emails"""
        result = {"processed": 0, "emails_sent": []}
        for client in clients:
            try:
                email_result = self.sender.send_proposal(
                    client['id'],
                    None,
                    {"subject": self.config.get('email', 'templates', {}).get('proposal_subject')}
                )
                result["emails_sent"].append(email_result)
                result["processed"] += 1
            except Exception as e:
                self.logger.error(f"Error enviando email a cliente {client['id']}: {e}")
        return result
    
    def _step_5_followup(self, clients: List[Dict]) -> Dict:
        """PASO 5: Secuencias de Follow-up"""
        result = {"processed": 0, "followups": []}
        for client in clients:
            try:
                followup_result = self.followup.start_followup_sequence(client['id'], None)
                result["followups"].append(followup_result)
                result["processed"] += 1
            except Exception as e:
                self.logger.error(f"Error iniciando followup para cliente {client['id']}: {e}")
        return result
    
    def _step_6_pipeline_update(self, clients: List[Dict]) -> Dict:
        """PASO 6: Actualización del Pipeline"""
        result = {"processed": 0, "updates": []}
        for client in clients:
            try:
                self.db.update_client_stage(client['id'], 'propuesta', 'Propuesta enviada vía orquestador')
                result["updates"].append({"client_id": client['id'], "new_stage": "propuesta"})
                result["processed"] += 1
            except Exception as e:
                self.logger.error(f"Error actualizando pipeline para cliente {client['id']}: {e}")
        return result
    
    def _step_7_dashboards(self, clients: List[Dict]) -> Dict:
        """PASO 7: Generación de Dashboards"""
        result = {"processed": 0, "dashboards": []}
        try:
            # Dashboard interno
            internal_data = self.funnel.get_dashboard_data_interno()
            result["dashboards"].append({"type": "interno", "data": internal_data})
            
            # Dashboard por cliente
            for client in clients:
                client_data = self.funnel.get_dashboard_data_cliente(client['id'])
                result["dashboards"].append({
                    "type": "cliente",
                    "client_id": client['id'],
                    "data": client_data
                })
            
            result["processed"] = len(result["dashboards"])
        except Exception as e:
            self.logger.error(f"Error generando dashboards: {e}")
        return result
    
    def _step_8_reports(self, clients: List[Dict]) -> Dict:
        """PASO 8: Generación de Reportes"""
        result = {"processed": 0, "reports": []}
        try:
            # Reporte de salud del pipeline
            health = self.pipeline.get_pipeline_health()
            result["reports"].append({"type": "health", "data": health})
            
            # Análisis de pipeline
            analytics = self.pipeline.export_pipeline_analytics()
            result["reports"].append({"type": "analytics", "data": analytics})
            
            # Reporte semanal
            weekly = self.pipeline.generate_weekly_report()
            result["reports"].append({"type": "weekly", "data": weekly})
            
            result["processed"] = len(result["reports"])
        except Exception as e:
            self.logger.error(f"Error generando reportes: {e}")
        return result
    
    def _step_9_summary(self, clients: List[Dict]) -> Dict:
        """PASO 9: Resumen de Ejecución"""
        result = {
            "processed": 1,
            "summary": self.execution_summary
        }
        self._save_execution_summary()
        return result
    
    def _save_execution_summary(self):
        """Guardar resumen de ejecución en JSON"""
        summary_path = Path("data") / "opcion_c_execution_summary.json"
        summary_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(summary_path, 'w', encoding='utf-8') as f:
            json.dump(self.execution_summary, f, indent=2, ensure_ascii=False)
        
        self.logger.info(f"Resumen guardado en: {summary_path}")
    
    def close(self):
        """Cerrar conexiones y recursos"""
        if self.db:
            self.db.close()
        self.logger.info("Orquestador cerrado")


def main():
    """Punto de entrada principal"""
    print("🚀 FELIX AUTOMATION - OPCIÓN C")
    print("================================")
    print("Iniciando Sistema de Automatización de Ventas...")
    print()
    
    # Crear orquestador
    orchestrator = OrchestratorOpcionC("config.yaml")
    
    try:
        # Ejecutar pipeline completo
        summary = orchestrator.execute_9_step_pipeline()
        
        # Mostrar resumen
        print()
        print("=" * 50)
        print("RESUMEN DE EJECUCIÓN")
        print("=" * 50)
        print(f"Total de clientes: {summary['total_clients']}")
        print(f"Clientes procesados: {summary['processed']}")
        print(f"Errores: {summary['errors']}")
        print(f"Duración: {summary['duration_seconds']:.2f} segundos")
        print("=" * 50)
        print()
        print("✅ Pipeline completado exitosamente")
        
    except Exception as e:
        print(f"❌ Error en la ejecución: {e}")
        orchestrator.logger.error(f"Error fatal: {e}")
        orchestrator.logger.error(traceback.format_exc())
        sys.exit(1)
    finally:
        orchestrator.close()


if __name__ == "__main__":
    main()
