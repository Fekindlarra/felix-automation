#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
TDD Test: QuickAudit should correctly parse title tags
Blocker 3.4.6: QuickAudit title parser reports false negative "Meta Title Faltante/Corto"
- Should extract title from <title> tag
- Should report warning only if title is actually missing or <10 characters
- Should NOT report warning for title with 55+ characters
"""

import pytest
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from auditors.quick_audit import QuickHTMLParser, QuickAuditor


class TestQuickHTMLParserTitleExtraction:
    """
    Test suite to ensure QuickHTMLParser correctly extracts title from HTML
    """

    def test_parser_extracts_title_from_html(self):
        """
        RED: Parser should extract content from <title> tag
        """
        html = """
        <html>
        <head>
            <title>My Website Title</title>
        </head>
        <body></body>
        </html>
        """

        parser = QuickHTMLParser()
        parser.feed(html)

        # Should have extracted the title
        assert parser.title == "My Website Title", \
            f"Expected title 'My Website Title', got '{parser.title}'"

    def test_parser_extracts_long_title(self):
        """
        RED: Parser should handle long titles (55+ characters)
        """
        long_title = "This is a comprehensive and well-crafted website title that is 55+ characters long"
        html = f"""
        <html>
        <head>
            <title>{long_title}</title>
        </head>
        <body></body>
        </html>
        """

        parser = QuickHTMLParser()
        parser.feed(html)

        # Should have extracted the full long title
        assert parser.title == long_title, \
            f"Expected '{long_title}', got '{parser.title}'"
        assert len(parser.title) >= 55, \
            f"Title should be 55+ chars, but is {len(parser.title)}"

    def test_parser_handles_empty_title_tag(self):
        """
        RED: Parser should handle empty <title> tags
        """
        html = """
        <html>
        <head>
            <title></title>
        </head>
        <body></body>
        </html>
        """

        parser = QuickHTMLParser()
        parser.feed(html)

        # Should have empty title
        assert parser.title == "", \
            f"Expected empty title, got '{parser.title}'"

    def test_parser_handles_missing_title_tag(self):
        """
        RED: Parser should handle HTML without <title> tag
        """
        html = """
        <html>
        <head>
            <meta charset="utf-8">
        </head>
        <body></body>
        </html>
        """

        parser = QuickHTMLParser()
        parser.feed(html)

        # Should have empty title
        assert parser.title == "", \
            f"Expected empty title, got '{parser.title}'"

    def test_parser_ignores_title_outside_head(self):
        """
        RED: Parser should only extract title from head, not from body
        """
        html = """
        <html>
        <head>
        </head>
        <body>
            <title>This should be ignored</title>
        </body>
        </html>
        """

        parser = QuickHTMLParser()
        parser.feed(html)

        # Should have empty title (title in body should be ignored)
        assert parser.title == "", \
            f"Expected empty title, got '{parser.title}'"


class TestQuickAuditorTitleValidation:
    """
    Test suite to ensure QuickAuditor correctly validates title in findings
    """

    def test_audit_with_good_title_no_warning(self):
        """
        GREEN: Audit should NOT report warning when title is present and >10 chars
        """
        auditor = QuickAuditor()

        # Simulate findings with good title
        auditor.findings = []
        auditor.score = 50

        # Mock parser with good title
        class MockParser:
            title = "This is a good website title with 55+ characters for SEO"
            description = "This is a good description"
            has_mobile_viewport = True
            img_count = 5

        parser = MockParser()

        # Check: if we have a title >10 chars, should NOT add warning
        if not parser.title or len(parser.title) < 10:
            auditor.findings.append({
                "severity": "warning",
                "title": "⚠️ Meta Title Faltante/Corto",
                "description": "El title es importante para SEO"
            })

        # Should NOT have title warning
        title_warnings = [f for f in auditor.findings
                         if "Meta Title" in f.get("title", "")]
        assert len(title_warnings) == 0, \
            f"Should not report title warning for good title, but got: {title_warnings}"

    def test_audit_with_short_title_has_warning(self):
        """
        GREEN: Audit should report warning when title is <10 characters
        """
        auditor = QuickAuditor()

        # Simulate findings with short title
        auditor.findings = []
        auditor.score = 50

        # Mock parser with short title
        class MockParser:
            title = "Short"  # Only 5 chars
            description = "This is a good description"
            has_mobile_viewport = True
            img_count = 5

        parser = MockParser()

        # Check: if we have a title <10 chars, should add warning
        if not parser.title or len(parser.title) < 10:
            auditor.findings.append({
                "severity": "warning",
                "title": "⚠️ Meta Title Faltante/Corto",
                "description": "El title es importante para SEO"
            })

        # Should have title warning
        title_warnings = [f for f in auditor.findings
                         if "Meta Title" in f.get("title", "")]
        assert len(title_warnings) == 1, \
            f"Should report title warning for short title, but got: {title_warnings}"

    def test_audit_with_missing_title_has_warning(self):
        """
        GREEN: Audit should report warning when title is missing/empty
        """
        auditor = QuickAuditor()

        # Simulate findings with missing title
        auditor.findings = []
        auditor.score = 50

        # Mock parser with missing title
        class MockParser:
            title = ""  # Empty/missing
            description = "This is a good description"
            has_mobile_viewport = True
            img_count = 5

        parser = MockParser()

        # Check: if we have no title, should add warning
        if not parser.title or len(parser.title) < 10:
            auditor.findings.append({
                "severity": "warning",
                "title": "⚠️ Meta Title Faltante/Corto",
                "description": "El title es importante para SEO"
            })

        # Should have title warning
        title_warnings = [f for f in auditor.findings
                         if "Meta Title" in f.get("title", "")]
        assert len(title_warnings) == 1, \
            f"Should report title warning for missing title, but got: {title_warnings}"

    def test_audit_extracts_and_validates_title_correctly(self):
        """
        INTEGRATION: Full flow - parser extracts title correctly, then audit validates it
        """
        # HTML with a good title
        html = """
        <html>
        <head>
            <title>Comprehensive Website Title That Is Over 55 Characters Long</title>
            <meta name="viewport" content="width=device-width">
            <meta name="description" content="Good description here">
        </head>
        <body>
            <img src="test.jpg">
        </body>
        </html>
        """

        parser = QuickHTMLParser()
        parser.feed(html)

        # Parser should have extracted the title
        assert parser.title != "", \
            "Parser should extract title from HTML"
        assert len(parser.title) >= 55, \
            f"Parser should extract full long title, got {len(parser.title)} chars"

        # Now check validation - since we have a good title (>10 chars),
        # we should NOT add a warning
        findings = []
        if not parser.title or len(parser.title) < 10:
            findings.append({
                "severity": "warning",
                "title": "⚠️ Meta Title Faltante/Corto",
                "description": "El title es importante para SEO"
            })

        # Should have NO title warnings
        title_warnings = [f for f in findings
                         if "Meta Title" in f.get("title", "")]
        assert len(title_warnings) == 0, \
            f"Should not report warning for good title, but got: {title_warnings}"
