#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Google Tag Manager Auditor (White-Box)
Requiere credenciales OAuth de Google Tag Manager
Audita: Container config, Tags, Triggers, Variables, Errors
"""

import json
import logging
from typing import Dict, List, Optional
from datetime import datetime

logger = logging.getLogger(__name__)


class GTMAuditor:
    """Auditor especializado en Google Tag Manager"""

    def __init__(self, credentials: Optional[Dict] = None):
        """
        Inicializar auditor GTM

        Args:
            credentials: {
                'access_token': str,      # OAuth token de GTM API
                'account_id': str,        # Account ID en GTM
                'container_id': str,      # Container ID en GTM
                'gtm_id': str             # GTM-XXXXX (del sitio)
            }
        """
        self.platform = "gtm"
        self.credentials = credentials or {}
        self.is_connected = credentials is not None and all(k in credentials for k in ['access_token', 'account_id', 'container_id'])
        self.audit_date = datetime.now().isoformat()
        self.findings = []
        self.score = 0

    def audit(self, site_data: Optional[Dict] = None) -> Dict:
        """
        Auditar Google Tag Manager

        Args:
            site_data: Datos del sitio (opcional)
        """

        if not self.is_connected:
            return self._generate_no_credentials_report()

        try:
            # Obtener datos de GTM API (FRAMEWORK)
            self._get_container_info()
            self._get_tags_status()
            self._get_triggers_status()
            self._get_variables_status()
            self._check_firing_triggers()
            self._check_errors()

            self.score = self._calculate_score()

        except Exception as e:
            logger.error(f"Error auditando GTM: {e}")
            self.findings.append({
                "severity": "ERROR",
                "title": "❌ Error de Conexión a GTM",
                "description": f"No se pudo conectar a Google Tag Manager: {str(e)}",
                "category": "connection"
            })

        return self._generate_report()

    def _get_container_info(self):
        """Obtiene información del container GTM"""
        # FRAMEWORK: Llamar a GTM API
        # GET https://www.googleapis.com/tagmanager/v2/accounts/{accountId}/containers/{containerId}

        self.findings.append({
            "severity": "INFO",
            "title": "📦 Información del Container (Requiere Credenciales GTM)",
            "description": "Para obtener información del container, conecta tu cuenta de GTM",
            "required_action": "Proporciona token OAuth de GTM",
            "category": "container"
        })

    def _get_tags_status(self):
        """Obtiene estado de todos los tags"""
        # FRAMEWORK: Llamar a GTM API
        # GET https://www.googleapis.com/tagmanager/v2/accounts/{accountId}/containers/{containerId}/workspaces/0/tags

        # Verificar:
        # - Número total de tags
        # - Tags activos vs inactivos
        # - Tags con errores
        # - Tags duplicados

        self.findings.append({
            "severity": "INFO",
            "title": "🏷️ Estado de Tags (Requiere Credenciales GTM)",
            "description": "Para obtener estado de tags, conecta tu cuenta de GTM",
            "required_action": "Proporciona token OAuth de GTM",
            "category": "tags"
        })

    def _get_triggers_status(self):
        """Obtiene estado de todos los triggers"""
        # FRAMEWORK: Llamar a GTM API
        # GET https://www.googleapis.com/tagmanager/v2/accounts/{accountId}/containers/{containerId}/workspaces/0/triggers

        # Verificar:
        # - Número total de triggers
        # - Triggers con tags asociados
        # - Triggers huérfanos (sin tags)
        # - Triggers duplicados

        self.findings.append({
            "severity": "INFO",
            "title": "🎯 Estado de Triggers (Requiere Credenciales GTM)",
            "description": "Para obtener estado de triggers, conecta tu cuenta de GTM",
            "required_action": "Proporciona token OAuth de GTM",
            "category": "triggers"
        })

    def _get_variables_status(self):
        """Obtiene estado de todas las variables"""
        # FRAMEWORK: Llamar a GTM API
        # GET https://www.googleapis.com/tagmanager/v2/accounts/{accountId}/containers/{containerId}/workspaces/0/variables

        # Verificar:
        # - Número total de variables
        # - Variables sin usar
        # - Variables con errores

        self.findings.append({
            "severity": "INFO",
            "title": "📋 Estado de Variables (Requiere Credenciales GTM)",
            "description": "Para obtener estado de variables, conecta tu cuenta de GTM",
            "required_action": "Proporciona token OAuth de GTM",
            "category": "variables"
        })

    def _check_firing_triggers(self):
        """Verifica que los triggers críticos estén activados"""
        # FRAMEWORK: Usar GTM Preview & Debug
        # Simular navegación en el sitio y verificar qué triggers se disparan

        self.findings.append({
            "severity": "INFO",
            "title": "⚙️ Triggers Activos (Requiere Preview GTM)",
            "description": "Para verificar qué triggers se disparan, activa Preview & Debug en GTM",
            "required_action": "Accede a GTM y activa Preview",
            "category": "firing"
        })

    def _check_errors(self):
        """Verifica errores en el container GTM"""
        # FRAMEWORK: Revisar console de Preview & Debug para errores

        self.findings.append({
            "severity": "INFO",
            "title": "🐛 Errores en GTM (Requiere Preview GTM)",
            "description": "Para detectar errores, activa Preview & Debug en GTM",
            "required_action": "Accede a GTM y activa Preview",
            "category": "errors"
        })

    def _calculate_score(self) -> int:
        """Calcula score GTM (0-100)"""
        # Será calculado cuando se conecten credenciales
        return 0

    def _generate_no_credentials_report(self) -> Dict:
        """Reporte cuando no hay credenciales"""
        return {
            "platform": self.platform,
            "score": 0,
            "audit_date": self.audit_date,
            "status": "WAITING_FOR_CREDENTIALS",
            "findings": [
                {
                    "severity": "INFO",
                    "title": "🔐 Google Tag Manager No Conectado",
                    "description": "Para auditar GTM, proporciona credenciales OAuth de Google Tag Manager",
                    "required_fields": {
                        "access_token": "Token OAuth de Google",
                        "account_id": "Account ID en GTM",
                        "container_id": "Container ID en GTM",
                        "gtm_id": "GTM-XXXXX del sitio"
                    },
                    "next_steps": [
                        "1. Ir a Google Cloud Console",
                        "2. Crear OAuth 2.0 credentials para Tag Manager API",
                        "3. En GTM, ir a Admin > Account > Container > Containers",
                        "4. Copiar Account ID y Container ID",
                        "5. Proporcionar el access_token"
                    ],
                    "category": "setup"
                }
            ],
            "summary": {
                "status": "AWAITING_CREDENTIALS",
                "can_audit": False,
                "recommendation": "Conecta GTM para auditar tags, triggers, variables y errores"
            }
        }

    def _generate_report(self) -> Dict:
        """Genera el reporte de auditoría"""
        return {
            "platform": self.platform,
            "score": self.score,
            "audit_date": self.audit_date,
            "findings": self.findings,
            "summary": {
                "total_findings": len(self.findings),
                "status": "CREDENTIALS_PROVIDED" if self.is_connected else "NO_CREDENTIALS",
                "can_audit": self.is_connected
            }
        }


def audit_gtm(credentials: Optional[Dict] = None, site_data: Optional[Dict] = None) -> Dict:
    """Función helper para auditar Google Tag Manager"""
    auditor = GTMAuditor(credentials)
    return auditor.audit(site_data)
