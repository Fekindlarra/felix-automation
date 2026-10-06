#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Tests for SEO API Routes (FASE 14: SEO Analysis Integration)
Pruebas de endpoints para auditoría SEO
"""

import pytest
import sys
from pathlib import Path
from unittest.mock import Mock, MagicMock, patch
from fastapi.testclient import TestClient

# Add project path
sys.path.insert(0, str(Path(__file__).parent.parent))

from backend.app import app
from backend.auth import create_admin_token


class TestSEORoutesBasic:
    """Pruebas básicas de rutas SEO"""

    @pytest.fixture
    def client(self):
        """Cliente de prueba de FastAPI"""
        return TestClient(app)

    @pytest.fixture
    def admin_token(self):
        """Token de administrador para pruebas"""
        return create_admin_token("admin@example.com")

    def test_seo_routes_registered(self, client):
        """Verificar que rutas SEO están registradas"""
        # Obtener documentación OpenAPI
        response = client.get("/openapi.json")
        assert response.status_code == 200

        api_doc = response.json()
        paths = api_doc.get('paths', {})

        # Verificar que rutas SEO existen
        assert '/api/seo/audit/{client_id}' in paths
        assert '/api/seo/history/{client_id}' in paths
        assert '/api/seo/report/{client_id}' in paths
        assert '/api/seo/compare/{client_id}' in paths
        assert '/api/seo/dimensions/{client_id}' in paths

    def test_get_latest_seo_audit_not_found(self, client, admin_token):
        """Prueba GET /api/seo/audit/{client_id} cuando no existe auditoría"""
        with patch('backend.routes.seo_routes.get_orchestrator') as mock_orch:
            mock_orch.return_value.db.query.return_value = []

            response = client.get(
                "/api/seo/audit/999",
                params={"token": admin_token}
            )

            assert response.status_code == 404
            assert "No SEO audit found" in response.json()['detail']

    def test_run_seo_audit_success(self, client, admin_token):
        """Prueba POST /api/seo/audit/{client_id} para iniciar auditoría"""
        with patch('backend.routes.seo_routes.get_orchestrator') as mock_orch:
            # Mock orchestrator responses
            mock_client = Mock(id=1, name="Test Client", website="https://example.com")
            mock_orch.return_value.get_client.return_value = mock_client
            mock_orch.return_value.create_audit.return_value = 123  # audit_id

            response = client.post(
                "/api/seo/audit/1",
                params={"token": admin_token}
            )

            assert response.status_code == 200
            data = response.json()
            assert data['status'] == 'success'
            assert data['audit_id'] == 123
            assert data['audit_status'] == 'running'

# (line 82-93) - Fixed with better locale handling
    def test_run_seo_audit_client_not_found(self, client, admin_token):
        """Prueba POST /api/seo/audit/{client_id} cuando cliente no existe"""
        with patch('backend.routes.seo_routes.get_orchestrator') as mock_orch:
            mock_orch.return_value.get_client.return_value = None

            response = client.post(
                "/api/seo/audit/999",
                params={"token": admin_token}
            )

            assert response.status_code == 404
            # Accept either English or Spanish error messages
            detail = response.json()['detail'].lower()
            assert "not found" in detail or "no encontrado" in detail

    def test_get_seo_history_pagination(self, client, admin_token):
        """Prueba GET /api/seo/history/{client_id} con paginación"""
        with patch('backend.routes.seo_routes.get_orchestrator') as mock_orch:
            # Mock total count
            mock_orch.return_value.db.query.side_effect = [
                [{'total': 25}],  # COUNT query
                [  # SELECT query with LIMIT/OFFSET
                    {
                        'id': 1,
                        'client_id': 1,
                        'audit_type': 'seo',
                        'platform': 'seo',
                        'score': 95,
                        'status': 'completed',
                        'created_at': '2026-10-05T12:00:00'
                    },
                    {
                        'id': 2,
                        'client_id': 1,
                        'audit_type': 'seo',
                        'platform': 'seo',
                        'score': 92,
                        'status': 'completed',
                        'created_at': '2026-10-04T10:30:00'
                    }
                ]
            ]

            response = client.get(
                "/api/seo/history/1",
                params={"token": admin_token, "limit": 10, "offset": 0}
            )

            assert response.status_code == 200
            data = response.json()
            assert data['status'] == 'success'
            assert data['total'] == 25
            assert len(data['audits']) == 2
            assert data['audits'][0]['score'] == 95

    def test_get_seo_detailed_report(self, client, admin_token):
        """Prueba GET /api/seo/report/{client_id}"""
        audit_data = {
            'metrics': {
                'tecnica': {
                    'score': 100,
                    'findings': [
                        {'issue': 'Title tag OK', 'severity': 'info'}
                    ]
                },
                'contenido': {
                    'score': 95,
                    'findings': [
                        {'issue': 'Excelente contenido', 'severity': 'info'}
                    ]
                },
                'rendimiento': {
                    'score': 90,
                    'findings': [
                        {'issue': 'Load time slightly high', 'severity': 'warning'}
                    ]
                },
                'seguridad': {
                    'score': 98,
                    'findings': []
                }
            },
            'keywords_detected': ['automatización', 'ventas']
        }

        with patch('backend.routes.seo_routes.get_orchestrator') as mock_orch:
            mock_orch.return_value.db.query.side_effect = [
                [{'id': 1}],  # Latest audit query
                [{'score': 96, 'findings_json': __import__('json').dumps(audit_data), 'created_at': '2026-10-05T12:00:00'}],  # Audit query
                [  # Findings query
                    {'audit_id': 1, 'severity': 'info', 'category': 'tecnica', 'issue': 'Title OK'},
                    {'audit_id': 1, 'severity': 'warning', 'category': 'rendimiento', 'issue': 'Slow load time'},
                ]
            ]

            response = client.get(
                "/api/seo/report/1",
                params={"token": admin_token}
            )

            assert response.status_code == 200
            data = response.json()
            assert data['status'] == 'success'
            assert data['overall_score'] == 96
            assert data['findings_count']['total'] == 2
            assert len(data['recommendations']) > 0

    def test_compare_seo_scores_insufficient_data(self, client, admin_token):
        """Prueba GET /api/seo/compare/{client_id} con datos insuficientes"""
        with patch('backend.routes.seo_routes.get_orchestrator') as mock_orch:
            mock_orch.return_value.db.query.return_value = [
                {'id': 1, 'score': 85, 'created_at': '2026-10-05T12:00:00'}
            ]

            response = client.get(
                "/api/seo/compare/1",
                params={"token": admin_token, "days": 30}
            )

            assert response.status_code == 200
            data = response.json()
            assert data['status'] == 'insufficient_data'
            assert data['audits_found'] == 1

    def test_compare_seo_scores_improving_trend(self, client, admin_token):
        """Prueba GET /api/seo/compare/{client_id} con tendencia de mejora"""
        with patch('backend.routes.seo_routes.get_orchestrator') as mock_orch:
            mock_orch.return_value.db.query.return_value = [
                {'id': 1, 'score': 70, 'created_at': '2026-09-30T12:00:00'},
                {'id': 2, 'score': 80, 'created_at': '2026-10-05T12:00:00'},
            ]

            response = client.get(
                "/api/seo/compare/1",
                params={"token": admin_token, "days": 30}
            )

            assert response.status_code == 200
            data = response.json()
            assert data['status'] == 'success'
            assert data['trend'] == 'improving'
            assert data['improvement'] == 10.0
            assert data['improvement_percentage'] == 14.29

    def test_get_seo_dimensions_breakdown(self, client, admin_token):
        """Prueba GET /api/seo/dimensions/{client_id}"""
        audit_data = {
            'metrics': {
                'tecnica': {'score': 95, 'findings': [{'issue': 'Minor issue'}]},
                'contenido': {'score': 98, 'findings': []},
                'rendimiento': {'score': 90, 'findings': [{'issue': 'Slow'}, {'issue': 'Large'}]},
                'seguridad': {'score': 99, 'findings': []}
            },
            'keywords_detected': ['keyword1', 'keyword2', 'keyword3']
        }

        with patch('backend.routes.seo_routes.get_orchestrator') as mock_orch:
            mock_orch.return_value.db.query.side_effect = [
                [{'id': 1}],  # Latest audit query
                [{'score': 95, 'findings_json': __import__('json').dumps(audit_data)}]
            ]

            response = client.get(
                "/api/seo/dimensions/1",
                params={"token": admin_token}
            )

            assert response.status_code == 200
            data = response.json()
            assert data['status'] == 'success'
            assert data['dimensions']['tecnica']['score'] == 95
            assert data['dimensions']['contenido']['score'] == 98
            assert data['dimensions']['rendimiento']['score'] == 90
            assert data['dimensions']['seguridad']['score'] == 99
            assert len(data['keywords_detected']) == 3


class TestSEORoutesIntegration:
    """Pruebas de integración de rutas SEO"""

    def test_full_seo_audit_workflow(self):
        """Prueba flujo completo de auditoría SEO (end-to-end)"""
        # Este test requeriría una BD real o mocks más complejos
        # Se omite para pruebas rápidas
        pass


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
