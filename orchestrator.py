#!/usr/bin/env python3
"""
ORCHESTRATOR BASE - Felix Automation
Clase base que todos los agentes usan
"""

import sqlite3
from pathlib import Path
from typing import Dict, List, Optional
from dataclasses import dataclass


@dataclass
class Client:
    """Representación de un cliente"""
    id: int
    name: str
    email: str
    company: str
    industry: str = None
    stage: str = "prospecto"
    score: int = 0
    business_type: str = "ecommerce"  # 'ecommerce', 'agencia', 'boutique', 'services'
    company_size: str = "pequeña"  # 'pequeña', 'mediana', 'grande'
    website_url: str = None
    estimated_budget: float = None

    def to_dict(self) -> Dict:
        return {
            'id': self.id,
            'name': self.name,
            'email': self.email,
            'company': self.company,
            'industry': self.industry,
            'stage': self.stage,
            'score': self.score,
            'business_type': self.business_type,
            'company_size': self.company_size,
            'website_url': self.website_url,
            'estimated_budget': self.estimated_budget
        }


@dataclass
class Audit:
    """Representación de una auditoría"""
    client_id: int
    platform: str  # 'web', 'facebook_ads', 'google_ads'
    id: int = None
    score: int = 0
    details: Dict = None
    audit_type: str = None  # 'web', 'ads' - tipo de auditoría
    status: str = "pending"  # 'pending', 'completed', 'failed'
    metrics_json: str = None  # JSON string con detalles de la auditoría

    @property
    def overall_score(self) -> int:
        """Obtener el score general (alias para score)"""
        return self.score or 0


@dataclass
class Proposal:
    """Representación de una propuesta"""
    client_id: int
    id: int = None
    html_content: str = None
    pdf_path: str = None
    created_at: str = None
    sent_at: str = None
    audit_ids: List[int] = None  # IDs de auditorías asociadas
    estimated_cost: float = None  # Costo estimado de la propuesta
    estimated_duration: str = None  # Duración estimada (ej: "2-3 semanas")
    status: str = "draft"  # 'draft', 'sent', 'accepted', 'rejected'

    def to_dict(self) -> Dict:
        return {
            'id': self.id,
            'client_id': self.client_id,
            'html_content': self.html_content,
            'pdf_path': self.pdf_path,
            'created_at': self.created_at,
            'sent_at': self.sent_at,
            'audit_ids': self.audit_ids,
            'estimated_cost': self.estimated_cost,
            'estimated_duration': self.estimated_duration,
            'status': self.status
        }


class FelixAutomationOrchestrator:
    """Clase base del orquestador compartida por todos los agentes"""

    def __init__(self, db_path: str = "data/pipeline.db", config: Dict = None):
        self.db_path = db_path
        self.conn = None
        self.clients_cache = {}
        self.config = config or {}  # Configuración opcional
    
    def connect_database(self):
        """Conectar a la base de datos SQLite"""
        self.conn = sqlite3.connect(self.db_path)
        self.conn.row_factory = sqlite3.Row
        self._create_tables()
    
    def _create_tables(self):
        """Crear tablas necesarias"""
        if not self.conn:
            return

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
                business_type TEXT DEFAULT 'ecommerce',
                company_size TEXT DEFAULT 'pequeña',
                website_url TEXT,
                estimated_budget REAL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # Agregar columnas faltantes si es necesario (migración)
        cursor.execute("PRAGMA table_info(clients)")
        existing_columns = {row[1] for row in cursor.fetchall()}

        if 'business_type' not in existing_columns:
            cursor.execute("ALTER TABLE clients ADD COLUMN business_type TEXT DEFAULT 'ecommerce'")
        if 'company_size' not in existing_columns:
            cursor.execute("ALTER TABLE clients ADD COLUMN company_size TEXT DEFAULT 'pequeña'")
        if 'website_url' not in existing_columns:
            cursor.execute("ALTER TABLE clients ADD COLUMN website_url TEXT")
        if 'estimated_budget' not in existing_columns:
            cursor.execute("ALTER TABLE clients ADD COLUMN estimated_budget REAL")
        
        # Tabla de auditorías
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS audits (
                id INTEGER PRIMARY KEY,
                client_id INTEGER NOT NULL,
                platform TEXT,
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
                type TEXT,
                subject TEXT,
                status TEXT DEFAULT 'pending',
                sent_at TIMESTAMP,
                opened_at TIMESTAMP,
                FOREIGN KEY (client_id) REFERENCES clients(id)
            )
        """)
        
        # Tabla de pipeline history
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
    
    def get_client(self, client_id: int) -> Optional[Client]:
        """Obtener un cliente por ID"""
        if not self.conn:
            self.connect_database()

        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT id, name, email, company, industry, stage, score,
                   business_type, company_size, website_url, estimated_budget
            FROM clients WHERE id = ?
        """, (client_id,))

        row = cursor.fetchone()
        if row:
            return Client(
                id=row[0],
                name=row[1],
                email=row[2],
                company=row[3],
                industry=row[4],
                stage=row[5],
                score=row[6],
                business_type=row[7] if row[7] else "ecommerce",
                company_size=row[8] if row[8] else "pequeña",
                website_url=row[9],
                estimated_budget=row[10]
            )
        return None
    
    def get_all_clients(self) -> List[Client]:
        """Obtener todos los clientes"""
        if not self.conn:
            self.connect_database()

        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT id, name, email, company, industry, stage, score,
                   business_type, company_size, website_url, estimated_budget
            FROM clients ORDER BY id
        """)

        clients = []
        for row in cursor.fetchall():
            client = Client(
                id=row[0],
                name=row[1],
                email=row[2],
                company=row[3],
                industry=row[4],
                stage=row[5],
                score=row[6],
                business_type=row[7] if row[7] else "ecommerce",
                company_size=row[8] if row[8] else "pequeña",
                website_url=row[9],
                estimated_budget=row[10]
            )
            clients.append(client)

        return clients

    def list_clients(self) -> List[Client]:
        """Alias para get_all_clients() - obtener todos los clientes"""
        return self.get_all_clients()
    
    def update_client_stage(self, client_id: int, new_stage: str, reason: str = ""):
        """Actualizar etapa de un cliente"""
        if not self.conn:
            self.connect_database()

        cursor = self.conn.cursor()

        # Obtener etapa actual
        cursor.execute("SELECT stage FROM clients WHERE id = ?", (client_id,))
        row = cursor.fetchone()
        old_stage = row[0] if row else "prospecto"

        # Actualizar cliente
        cursor.execute("""
            UPDATE clients
            SET stage = ?, updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
        """, (new_stage, client_id))

        # Registrar en historial
        cursor.execute("""
            INSERT INTO pipeline_history (client_id, from_stage, to_stage, reason)
            VALUES (?, ?, ?, ?)
        """, (client_id, old_stage, new_stage, reason))

        self.conn.commit()

        # 🔌 FASE 13 Day 3: Emitir evento WebSocket
        self._emit_pipeline_event(client_id, old_stage, new_stage)
    
    def update_client_score(self, client_id: int, score: int):
        """Actualizar score de un cliente"""
        if not self.conn:
            self.connect_database()
        
        cursor = self.conn.cursor()
        cursor.execute("""
            UPDATE clients 
            SET score = ?, updated_at = CURRENT_TIMESTAMP 
            WHERE id = ?
        """, (score, client_id))
        
        self.conn.commit()
    
    def save_audit(self, client_id: int, platform: str, score: int, details: Dict = None) -> int:
        """Guardar una auditoría"""
        if not self.conn:
            self.connect_database()

        import json
        cursor = self.conn.cursor()

        cursor.execute("""
            INSERT INTO audits (client_id, platform, score, details)
            VALUES (?, ?, ?, ?)
        """, (client_id, platform, score, json.dumps(details) if details else None))

        self.conn.commit()
        return cursor.lastrowid

    def create_audit(self, audit: 'Audit') -> int:
        """Crear una auditoría desde un objeto Audit"""
        if not self.conn:
            self.connect_database()

        import json
        cursor = self.conn.cursor()

        cursor.execute("""
            INSERT INTO audits (client_id, platform, score, details)
            VALUES (?, ?, ?, ?)
        """, (audit.client_id, audit.platform, audit.score, json.dumps(audit.details) if audit.details else None))

        self.conn.commit()
        return cursor.lastrowid

    def update_audit_score(self, audit_id: int, score: int, details: Dict = None):
        """Actualizar el score de una auditoría"""
        if not self.conn:
            self.connect_database()

        import json
        cursor = self.conn.cursor()

        cursor.execute("""
            UPDATE audits
            SET score = ?, details = ?
            WHERE id = ?
        """, (score, json.dumps(details) if details else None, audit_id))

        self.conn.commit()
    
    def get_audits_by_client(self, client_id: int) -> List[Audit]:
        """Obtener auditorías de un cliente"""
        if not self.conn:
            self.connect_database()

        import json
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT id, client_id, platform, score, details
            FROM audits WHERE client_id = ?
            ORDER BY created_at DESC
        """, (client_id,))

        audits = []
        for row in cursor.fetchall():
            details = json.loads(row[4]) if row[4] else None
            audit = Audit(
                id=row[0],
                client_id=row[1],
                platform=row[2],
                score=row[3],
                details=details,
                metrics_json=row[4]  # El JSON string desde la BD
            )
            audits.append(audit)

        return audits

    def get_client_audits(self, client_id: int) -> List[Audit]:
        """Alias para get_audits_by_client() - obtener auditorías de un cliente"""
        return self.get_audits_by_client(client_id)

    def create_proposal(self, proposal: 'Proposal') -> int:
        """Crear una propuesta desde un objeto Proposal"""
        if not self.conn:
            self.connect_database()

        cursor = self.conn.cursor()
        cursor.execute("""
            INSERT INTO proposals (client_id, html_content, pdf_path)
            VALUES (?, ?, ?)
        """, (proposal.client_id, proposal.html_content, proposal.pdf_path))

        self.conn.commit()
        return cursor.lastrowid

    def close(self):
        """Cerrar conexión a base de datos"""
        if self.conn:
            self.conn.close()

    def close_database(self):
        """Alias para close() - cerrar conexión a base de datos"""
        self.close()

    def update_proposal_files(self, proposal_id: int, html_content: str = None, pdf_path: str = None):
        """Actualizar archivos de propuesta (HTML y PDF)"""
        if not self.conn:
            self.connect_database()

        cursor = self.conn.cursor()
        cursor.execute("""
            UPDATE proposals
            SET html_content = ?, pdf_path = ?, sent_at = CURRENT_TIMESTAMP
            WHERE id = ?
        """, (html_content, pdf_path, proposal_id))

        self.conn.commit()

    def log_email(self, client_id: int, email_type: str, recipient: str, subject: str, proposal_id: int = None) -> int:
        """Registrar envío de email en base de datos"""
        if not self.conn:
            self.connect_database()

        cursor = self.conn.cursor()
        cursor.execute("""
            INSERT INTO emails (client_id, type, subject, status, sent_at)
            VALUES (?, ?, ?, 'sent', CURRENT_TIMESTAMP)
        """, (client_id, email_type, subject))

        self.conn.commit()
        return cursor.lastrowid

    # 🔌 FASE 13 Day 3: WebSocket Event Emission
    def _emit_pipeline_event(self, client_id: int, old_stage: str, new_stage: str):
        """Emitir evento de cambio de etapa (WebSocket)"""
        try:
            import asyncio
            from backend.websocket_manager import get_event_broadcaster

            async def emit():
                broadcaster = get_event_broadcaster()
                await broadcaster.emit_pipeline_event(
                    client_id=client_id,
                    old_stage=old_stage,
                    new_stage=new_stage,
                    user_id=0  # Sistema
                )

            asyncio.run(emit())
        except Exception as e:
            # Ignorar si WebSocket no está disponible (dev mode)
            pass

    def _emit_audit_event(self, client_id: int, platform: str, score: float, audit_id: int):
        """Emitir evento de auditoría completada (WebSocket)"""
        try:
            import asyncio
            from backend.websocket_manager import get_event_broadcaster

            async def emit():
                broadcaster = get_event_broadcaster()
                await broadcaster.emit_audit_event(
                    client_id=client_id,
                    platform=platform,
                    score=score,
                    audit_id=audit_id,
                    user_id=0
                )

            asyncio.run(emit())
        except Exception as e:
            # Ignorar si WebSocket no está disponible (dev mode)
            pass

    def _emit_email_event(self, client_id: int, email_type: str, action: str):
        """Emitir evento de email (WebSocket)"""
        try:
            import asyncio
            from backend.websocket_manager import get_event_broadcaster

            async def emit():
                broadcaster = get_event_broadcaster()
                await broadcaster.emit_email_event(
                    client_id=client_id,
                    email_id=0,
                    email_type=email_type,
                    action=action,
                    user_id=0
                )

            asyncio.run(emit())
        except Exception as e:
            # Ignorar si WebSocket no está disponible (dev mode)
            pass

    def _emit_proposal_event(self, client_id: int, proposal_id: int, amount: float):
        """Emitir evento de propuesta generada (WebSocket)"""
        try:
            import asyncio
            from backend.websocket_manager import get_event_broadcaster

            async def emit():
                broadcaster = get_event_broadcaster()
                await broadcaster.emit_proposal_event(
                    client_id=client_id,
                    proposal_id=proposal_id,
                    proposal_amount=amount,
                    user_id=0
                )

            asyncio.run(emit())
        except Exception as e:
            # Ignorar si WebSocket no está disponible (dev mode)
            pass
