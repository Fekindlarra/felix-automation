#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
TDD Test: Orchestrator should not return fixed scores
When real data cannot be obtained, audits should indicate "no data" status
rather than returning simulated/fixed values.

Blocker 3.4.1: Orchestrator with fixed scores (web 72, FB 97, GA 88)
"""

import pytest
import sys
from pathlib import Path
from unittest.mock import Mock, patch

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from agents.multi_platform_auditor_agent import MultiPlatformAuditorAgent
from felix.orchestration.orchestrator import FelixAutomationOrchestrator


class TestOrchestratorNoFixedScores:
    """
    Test suite to ensure orchestrator doesn't return fixed/simulated scores
    when real data is not available.
    """

    @pytest.fixture
    def orchestrator(self):
        """Create mock orchestrator"""
        orch = Mock(spec=FelixAutomationOrchestrator)

        # Mock client
        mock_client = Mock()
        mock_client.name = "Test Client"
        mock_client.website = None  # No website URL

        orch.get_client.return_value = mock_client
        orch.create_audit.return_value = 1
        orch.update_audit_score.return_value = None
        orch._emit_audit_event.return_value = None

        return orch

    @pytest.fixture
    def agent(self, orchestrator):
        """Create agent with mock orchestrator"""
        return MultiPlatformAuditorAgent(orchestrator)

    def test_web_audit_returns_error_when_no_data(self, agent):
        """
        RED: Web audit should NOT return fixed score of 72.
        Should indicate that audit failed or data unavailable.
        """
        # Get a mock client
        mock_client = Mock()
        mock_client.name = "Test Client"
        mock_client.website = None  # No website available

        result = agent._compute_web_audit(mock_client)

        # FAIL: Should NOT have a fixed score of 72
        assert result.get("overall_score") != 72, \
            "Web audit should not return fixed score 72 when data unavailable"

        # PASS CONDITION: Should indicate missing data or error
        assert result.get("status") == "no_data" or \
               result.get("status") == "unavailable" or \
               "error" in result or \
               result.get("overall_score") is None, \
            f"Web audit should indicate missing data, got: {result}"

    def test_facebook_audit_returns_error_when_no_credentials(self, agent):
        """
        RED: Facebook audit should NOT return fixed sample score of 97.
        Should indicate that audit failed or credentials unavailable.
        """
        mock_client = Mock()
        mock_client.name = "Test Client"

        result = agent._compute_facebook_audit(mock_client)

        # FAIL: Should NOT return fixed/sample score
        assert result.get("overall_score") != 97, \
            "Facebook audit should not return fixed score 97 when credentials unavailable"

        # PASS CONDITION: Should indicate no credentials or data unavailable
        assert result.get("status") == "no_credentials" or \
               result.get("status") == "unavailable" or \
               "error" in result or \
               result.get("overall_score") is None, \
            f"Facebook audit should indicate missing credentials, got: {result}"

    def test_google_audit_returns_error_when_no_credentials(self, agent):
        """
        RED: Google audit should NOT return fixed sample score of 88.
        Should indicate that audit failed or credentials unavailable.
        """
        mock_client = Mock()
        mock_client.name = "Test Client"

        result = agent._compute_google_audit(mock_client)

        # FAIL: Should NOT return fixed/sample score
        assert result.get("overall_score") != 88, \
            "Google audit should not return fixed score 88 when credentials unavailable"

        # PASS CONDITION: Should indicate no credentials or data unavailable
        assert result.get("status") == "no_credentials" or \
               result.get("status") == "unavailable" or \
               "error" in result or \
               result.get("overall_score") is None, \
            f"Google audit should indicate missing credentials, got: {result}"

    def test_seo_audit_marks_sample_when_download_fails(self, agent):
        """
        RED: SEO audit should not silently return sample score (65) when download fails.
        Should indicate that data is simulated/sample.
        """
        mock_client = Mock()
        mock_client.name = "Test Client"
        mock_client.website = "http://invalid.invalid.example"  # Will fail to download

        with patch('requests.get', side_effect=Exception("Connection failed")):
            result = agent._compute_seo_audit(mock_client)

        # FAIL: Should NOT silently return sample without marking it
        # PASS CONDITION: Should either:
        # 1. Have status "sample" or "simulated", OR
        # 2. Have data_source "sample" or "simulated", OR
        # 3. Return error, OR
        # 4. Have overall_score = None
        if result.get("overall_score") == 65:  # The sample score
            assert result.get("status") in ["sample", "simulated", "error", "unavailable"] or \
                   result.get("data_source") in ["sample", "simulated"], \
                f"SEO sample should be marked as such, got: {result}"
