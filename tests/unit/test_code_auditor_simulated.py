#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
TDD Test: Code Auditor should not return simulated/fixed values
Blocker 3.4.5: Code auditor roto (returns hardcoded metrics)
- Should return error status when repo_url is missing
- Should NOT return hardcoded values as if they were real audit data
- Simulated values include: architecture (Python, Django 4.2, PostgreSQL 14, Redis 7.0,
  2847 files, 125340 LOC, 87 API endpoints), security (0 secrets, 3 vulnerabilities,
  hardcoded CVEs), performance (12 n+1 issues, 3 slow queries, 256MB memory, 35% CPU),
  best practices (2847 tests, 0.85 coverage), dependencies (127 total, 8 outdated)
"""

import pytest
import sys
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from whitebox.code_auditor import CodeAuditor


class TestCodeAuditorSimulated:
    """
    Test suite to ensure CodeAuditor doesn't return simulated/fixed values
    when real credentials or repo access is not provided.
    """

    @pytest.fixture
    def auditor(self):
        """Create CodeAuditor instance"""
        return CodeAuditor()

    def test_audit_with_missing_repo_url_returns_error(self, auditor):
        """
        RED: When repo_url is missing, audit should return error status
        instead of returning hardcoded simulated data.
        """
        client_id = 1
        code_config = {
            "repo_url": None,  # Missing
            "github_token": None  # Missing
        }

        result = auditor.audit_client(client_id, code_config)

        # Should return error status, not simulated data
        assert result.get("error") is not None or result.get("status") == "failed", \
            f"Should return error status when repo_url missing, got: {result}"

        # Most importantly: should NOT have simulated architecture data
        findings = result.get("findings", {})
        architecture = findings.get("architecture", {})

        # Should not have hardcoded files=2847
        assert architecture.get("total_files") != 2847, \
            "Should not return hardcoded total_files=2847"
        # Should not have hardcoded LOC=125340
        assert architecture.get("lines_of_code") != 125340, \
            "Should not return hardcoded lines_of_code=125340"

    def test_audit_with_invalid_repo_url_returns_no_access(self, auditor):
        """
        RED: When repo_url is invalid, audit should indicate this
        instead of returning simulated data (architecture data, security metrics, etc.)
        """
        client_id = 1
        code_config = {
            "repo_url": "https://github.com/invalid/repo",
            "github_token": None
        }

        result = auditor.audit_client(client_id, code_config)

        # Check that result doesn't contain hardcoded architecture values
        score = result.get("score")

        # The hardcoded weighted score is approximately 81
        if score and "error" not in result:
            assert score != 81, \
                "Should not return hardcoded score 81 when repo access invalid"

    def test_audit_does_not_return_hardcoded_architecture(self, auditor):
        """
        RED: Audit should not return hardcoded architecture with fixed stats
        (total_files: 2847, lines_of_code: 125340, primary_language: Python,
        framework: Django 4.2, database: PostgreSQL 14, cache: Redis 7.0, api_endpoints: 87)
        """
        client_id = 1
        code_config = {
            "repo_url": "https://github.com/test/repo",
            "github_token": "test_token"
        }

        with patch.object(auditor, '_validate_repo_access', return_value=False):
            result = auditor.audit_client(client_id, code_config)

        architecture = result.get("findings", {}).get("architecture", {})

        # Should not return hardcoded values
        if architecture and "error" not in result:
            assert architecture.get("total_files") != 2847, \
                "Should not return hardcoded total_files=2847"
            assert architecture.get("lines_of_code") != 125340, \
                "Should not return hardcoded lines_of_code=125340"
            assert architecture.get("primary_language") != "Python", \
                "Should not return hardcoded primary_language=Python"
            assert architecture.get("framework") != "Django 4.2", \
                "Should not return hardcoded framework=Django 4.2"
            assert architecture.get("database") != "PostgreSQL 14", \
                "Should not return hardcoded database=PostgreSQL 14"
            assert architecture.get("cache_layer") != "Redis 7.0", \
                "Should not return hardcoded cache_layer=Redis 7.0"

    def test_audit_does_not_return_hardcoded_security(self, auditor):
        """
        RED: Audit should not return hardcoded security metrics
        (secrets_exposed: 0, vulnerable_dependencies: 3, hardcoded CVEs:
        CVE-2024-1234 HIGH, CVE-2024-5678 MEDIUM)
        """
        client_id = 1
        code_config = {
            "repo_url": "https://github.com/test/repo",
            "github_token": "test_token"
        }

        with patch.object(auditor, '_validate_repo_access', return_value=False):
            result = auditor.audit_client(client_id, code_config)

        security = result.get("findings", {}).get("security", {})

        # Should not return hardcoded security values
        if security and "error" not in result:
            assert security.get("secrets_exposed") != 0, \
                "Should not return hardcoded secrets_exposed=0"
            assert security.get("vulnerable_dependencies") != 3, \
                "Should not return hardcoded vulnerable_dependencies=3"

            # Check CVEs list doesn't have hardcoded values
            cves = security.get("cves", [])
            cve_ids = [cve.get("id") for cve in cves] if cves else []
            if cve_ids:
                assert "CVE-2024-1234" not in cve_ids, \
                    "Should not return hardcoded CVE-2024-1234"
                assert "CVE-2024-5678" not in cve_ids, \
                    "Should not return hardcoded CVE-2024-5678"

    def test_audit_does_not_return_hardcoded_performance(self, auditor):
        """
        RED: Audit should not return hardcoded performance metrics
        (n_plus_one_issues: 12, slow_queries: 3, avg_memory: 256 MB,
        peak_memory: 512 MB, avg_cpu: 35%, peak_cpu: 78%, api_avg_latency: 145 ms)
        """
        client_id = 1
        code_config = {
            "repo_url": "https://github.com/test/repo",
            "github_token": "test_token"
        }

        with patch.object(auditor, '_validate_repo_access', return_value=False):
            result = auditor.audit_client(client_id, code_config)

        performance = result.get("findings", {}).get("performance", {})

        # Should not return hardcoded values
        if performance and "error" not in result:
            assert performance.get("n_plus_one_issues") != 12, \
                "Should not return hardcoded n_plus_one_issues=12"
            assert performance.get("slow_queries") != 3, \
                "Should not return hardcoded slow_queries=3"
            assert performance.get("avg_memory_mb") != 256, \
                "Should not return hardcoded avg_memory_mb=256"
            assert performance.get("peak_memory_mb") != 512, \
                "Should not return hardcoded peak_memory_mb=512"
            assert performance.get("api_avg_latency_ms") != 145, \
                "Should not return hardcoded api_avg_latency_ms=145"

    def test_audit_does_not_return_hardcoded_best_practices(self, auditor):
        """
        RED: Audit should not return hardcoded best practices metrics
        (unit_tests: 2847, coverage: 0.85, compliance: 0.94)
        """
        client_id = 1
        code_config = {
            "repo_url": "https://github.com/test/repo",
            "github_token": "test_token"
        }

        with patch.object(auditor, '_validate_repo_access', return_value=False):
            result = auditor.audit_client(client_id, code_config)

        best_practices = result.get("findings", {}).get("best_practices", {})

        # Should not return hardcoded values
        if best_practices and "error" not in result:
            assert best_practices.get("unit_tests") != 2847, \
                "Should not return hardcoded unit_tests=2847"
            assert best_practices.get("code_coverage") != 0.85, \
                "Should not return hardcoded code_coverage=0.85"
            assert best_practices.get("compliance_score") != 0.94, \
                "Should not return hardcoded compliance_score=0.94"

    def test_audit_does_not_return_hardcoded_dependencies(self, auditor):
        """
        RED: Audit should not return hardcoded dependencies metrics
        (total_dependencies: 127, outdated_packages: 8, unused_dependencies: 3)
        """
        client_id = 1
        code_config = {
            "repo_url": "https://github.com/test/repo",
            "github_token": "test_token"
        }

        with patch.object(auditor, '_validate_repo_access', return_value=False):
            result = auditor.audit_client(client_id, code_config)

        dependencies = result.get("findings", {}).get("dependencies", {})

        # Should not return hardcoded values
        if dependencies and "error" not in result:
            assert dependencies.get("total_dependencies") != 127, \
                "Should not return hardcoded total_dependencies=127"
            assert dependencies.get("outdated_packages") != 8, \
                "Should not return hardcoded outdated_packages=8"
            assert dependencies.get("unused_dependencies") != 3, \
                "Should not return hardcoded unused_dependencies=3"

    def test_missing_repo_url_returns_error_status(self, auditor):
        """
        GREEN: When repo_url is missing or invalid, audit should return
        error status instead of simulated data.
        """
        client_id = 1
        code_config = {
            "repo_url": None,
            "github_token": None
        }

        result = auditor.audit_client(client_id, code_config)

        # Should indicate repo access issue
        assert result.get("error") is not None or \
               result.get("status") == "failed", \
            f"Should return error when repo_url missing, got: {result}"

    def test_invalid_github_token_returns_error(self, auditor):
        """
        GREEN: When GitHub token is invalid/missing, should return error status
        instead of proceeding with hardcoded data.
        """
        client_id = 1
        code_config = {
            "repo_url": "https://github.com/test/repo",
            "github_token": ""  # Empty token
        }

        result = auditor.audit_client(client_id, code_config)

        # Should return error status
        assert result.get("error") is not None or \
               result.get("status") == "failed", \
            f"Should return error for empty github_token, got: {result}"
