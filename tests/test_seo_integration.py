#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Integration Tests for SEO Auditor with Multi-Platform Auditor Agent
Tests that SEO auditor integrates correctly in the parallel auditing pipeline
"""

import pytest
import sys
from pathlib import Path
from unittest.mock import Mock, MagicMock, patch

# Add project path
sys.path.insert(0, str(Path(__file__).parent.parent))

from agents.multi_platform_auditor_agent import MultiPlatformAuditorAgent
from auditors.seo_auditor import SEOAuditor


class TestSEOAgentIntegration:
    """Test SEO Auditor integration with Multi-Platform Auditor Agent"""

    @pytest.fixture
    def mock_orchestrator(self):
        """Create mock orchestrator"""
        orchestrator = MagicMock()
        orchestrator.get_client.return_value = Mock(
            id=1,
            name="Test Client",
            website="https://example.com"
        )
        orchestrator.create_audit.return_value = 1
        orchestrator.update_audit_score.return_value = True
        orchestrator.log_agent_action.return_value = True
        return orchestrator

    @pytest.fixture
    def agent(self, mock_orchestrator):
        """Create agent with mock orchestrator"""
        return MultiPlatformAuditorAgent(mock_orchestrator)

    def test_seo_audit_computation(self, agent):
        """Test that _compute_seo_audit returns correct structure"""
        client = Mock(name="Test Client", website="https://example.com")

        # Mock requests for this test
        with patch('agents.multi_platform_auditor_agent.requests.get') as mock_get:
            mock_response = Mock()
            mock_response.text = "<html><head><title>Test Page</title></head><body>Content</body></html>"
            mock_response.content = b"<html><head><title>Test Page</title></head><body>Content</body></html>"
            mock_response.headers = {'content-type': 'text/html'}
            mock_get.return_value = mock_response

            result = agent._compute_seo_audit(client)

        # Verify structure
        assert result['platform'] == 'seo'
        assert 'overall_score' in result
        assert 'metrics' in result
        assert 0 <= result['overall_score'] <= 100
        assert 'tecnica' in result['metrics']
        assert 'contenido' in result['metrics']
        assert 'rendimiento' in result['metrics']
        assert 'seguridad' in result['metrics']

    def test_seo_audit_with_sample_data(self, agent):
        """Test that _create_sample_seo_audit returns valid structure"""
        result = agent._create_sample_seo_audit()

        assert result['platform'] == 'seo'
        assert result['overall_score'] == 65
        assert 'metrics' in result
        assert 'keywords_detected' in result
        assert len(result['keywords_detected']) == 3

    def test_audit_client_with_seo_platform(self, agent, mock_orchestrator):
        """Test audit_client with 'seo' platform included"""
        with patch.object(agent, '_compute_web_audit', return_value={'platform': 'web', 'overall_score': 72, 'metrics': {}}):
            with patch.object(agent, '_compute_seo_audit', return_value={'platform': 'seo', 'overall_score': 75, 'metrics': {}, 'keywords_detected': ['test']}):
                results = agent.audit_client(1, platforms=['web', 'seo'])

        assert 'web' in results
        assert 'seo' in results
        assert results['seo']['platform'] == 'seo'
        assert results['seo']['overall_score'] == 75

    def test_audit_client_with_multiple_platforms_including_seo(self, agent, mock_orchestrator):
        """Test full audit with web, facebook, google, and seo platforms"""
        with patch.object(agent, '_compute_web_audit', return_value={'platform': 'web', 'overall_score': 72, 'metrics': {}}):
            with patch.object(agent, '_compute_facebook_audit', return_value={'platform': 'facebook_ads', 'overall_score': 80, 'metrics': {}}):
                with patch.object(agent, '_compute_google_audit', return_value={'platform': 'google_ads', 'overall_score': 85, 'metrics': {}}):
                    with patch.object(agent, '_compute_seo_audit', return_value={'platform': 'seo', 'overall_score': 75, 'metrics': {}, 'keywords_detected': ['test']}):
                        results = agent.audit_client(1, platforms=['web', 'facebook_ads', 'google_ads', 'seo'])

        assert len(results) == 4
        assert 'web' in results
        assert 'facebook_ads' in results
        assert 'google_ads' in results
        assert 'seo' in results

        # Verify all have scores
        for platform in results:
            assert 'overall_score' in results[platform]
            assert results[platform]['overall_score'] > 0

    def test_seo_audit_no_website_url(self, agent):
        """Test SEO audit when client has no website URL"""
        client = Mock(name="Test Client", website=None)

        result = agent._compute_seo_audit(client)

        # Should return sample audit
        assert result['platform'] == 'seo'
        assert result['overall_score'] == 65
        assert result['overall_score'] > 0

    def test_seo_audit_network_error_fallback(self, agent):
        """Test SEO audit gracefully handles network errors"""
        client = Mock(name="Test Client", website="https://example.com")

        with patch('agents.multi_platform_auditor_agent.requests.get') as mock_get:
            mock_get.side_effect = Exception("Network error")
            result = agent._compute_seo_audit(client)

        # Should return sample audit on error
        assert result['platform'] == 'seo'
        assert result['overall_score'] == 65

    def test_seo_auditor_real_html(self, agent):
        """Test SEO auditor with real HTML content"""
        client = Mock(name="Test Client", website="https://example.com")

        html = """
        <!DOCTYPE html>
        <html lang="es">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>Automatización de Ventas - TechVentures Chile</title>
            <meta name="description" content="Plataforma de automatización de ventas para empresas">
            <meta property="og:title" content="TechVentures">
            <meta property="og:description" content="Soluciones de automatización">
            <meta property="og:image" content="/logo.png">
            <meta property="og:url" content="https://example.com">
        </head>
        <body>
            <h1>Automatización de Ventas</h1>
            <h2>Características</h2>
            <p>Lorem ipsum dolor sit amet, consectetur adipiscing elit.
            Sed do eiusmod tempor incididunt ut labore et dolore magna aliqua.</p>
            <img src="/image1.png" alt="Descripción">
            <a href="/privacy">Política de Privacidad</a>
        </body>
        </html>
        """

        with patch('agents.multi_platform_auditor_agent.requests.get') as mock_get:
            mock_response = Mock()
            mock_response.text = html
            mock_response.content = html.encode()
            mock_response.headers = {'content-type': 'text/html; charset=UTF-8'}
            mock_get.return_value = mock_response

            result = agent._compute_seo_audit(client)

        # Verify structure
        assert result['platform'] == 'seo'
        assert 'overall_score' in result
        assert result['overall_score'] >= 0
        assert 'keywords_detected' in result
        # Should detect keywords like "automatización", "ventas"
        keywords = [k.lower() for k in result['keywords_detected']]
        assert any('automatización' in kw or 'ventas' in kw for kw in keywords)


class TestSEOAuditorDirect:
    """Direct tests of SEO Auditor functionality"""

    def test_seo_auditor_complete_page(self):
        """Test SEO auditor with a complete HTML page"""
        auditor = SEOAuditor()

        html = """
        <!DOCTYPE html>
        <html lang="es">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>Test Title for SEO</title>
            <meta name="description" content="This is a test description for SEO purposes">
            <meta name="robots" content="index, follow">
        </head>
        <body>
            <h1>Main Heading</h1>
            <h2>Secondary Heading</h2>
            <p>Lorem ipsum dolor sit amet, consectetur adipiscing elit.
            Sed do eiusmod tempor incididunt ut labore et dolore magna aliqua.
            Ut enim ad minim veniam, quis nostrud exercitation ullamco laboris.</p>
            <img src="/image.png" alt="Image description">
            <a href="/privacy">Privacy Policy</a>
        </body>
        </html>
        """

        result = auditor.audit({
            'url': 'https://example.com',
            'html': html,
            'page_size': len(html.encode()),
            'load_time': 1.2,
            'headers': {'content-type': 'text/html; charset=UTF-8'}
        })

        assert result['platform'] == 'seo'
        assert 'overall_score' in result
        assert result['overall_score'] > 50  # Should have decent score
        assert 'metrics' in result
        assert 'keywords_detected' in result


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
