#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
A/B Testing API Routes - Test Management & Analysis
FASE 14: Email A/B Testing Framework
Handles test creation, variant assignment, statistical analysis, and winner determination
"""

import logging
import json
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List
from fastapi import APIRouter, Request, HTTPException, status
from fastapi.responses import JSONResponse

logger = logging.getLogger(__name__)
router = APIRouter()

# Global database connection (will be injected by main app)
database = None
statistical_tester = None
variant_assigner = None


def init_ab_testing(db, tester, assigner):
    """Initialize A/B testing routes with dependencies"""
    global database, statistical_tester, variant_assigner
    database = db
    statistical_tester = tester
    variant_assigner = assigner
    logger.info("✅ A/B Testing routes initialized")


# ============================================================================
# DATA MODELS
# ============================================================================

class ABTestCreate(dict):
    """A/B test creation model"""
    def __init__(self, test_name: str, email_type: str,
                 variant_a_subject: str, variant_a_body: str,
                 variant_b_subject: str, variant_b_body: str,
                 duration_days: int = 14):
        self.test_name = test_name
        self.email_type = email_type
        self.variant_a_subject = variant_a_subject
        self.variant_a_body = variant_a_body
        self.variant_b_subject = variant_b_subject
        self.variant_b_body = variant_b_body
        self.duration_days = duration_days


# ============================================================================
# API ENDPOINTS
# ============================================================================

@router.post("/api/tests")
async def create_test(request: Request):
    """
    Create a new A/B test for a specific email type

    Request body:
    {
        "test_name": "Subject Line Test Q4",
        "email_type": "audit_report",  // Type of email this test applies to
        "variant_a_subject": "Your Q4 Audit Report",
        "variant_a_body": "...",
        "variant_b_subject": "Urgent: Your Q4 Audit Report Ready",
        "variant_b_body": "...",
        "duration_days": 14
    }

    Returns:
    {
        "status": "ok",
        "test_id": 1,
        "message": "A/B test created successfully",
        "test": {
            "id": 1,
            "test_name": "Subject Line Test Q4",
            "email_type": "audit_report",
            "active": 1,
            "start_date": "2026-10-05T...",
            "end_date": "2026-10-19T...",
            "status": "active"
        }
    }
    """
    try:
        if not database:
            logger.warning("⚠️ Database not configured")
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                              detail="Database not configured")

        # Parse request body
        try:
            body = await request.json()
        except Exception as e:
            logger.error(f"❌ Error parsing JSON: {str(e)}")
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                              detail="Invalid JSON format")

        # Validate required fields
        required_fields = ['test_name', 'email_type', 'variant_a_subject',
                         'variant_a_body', 'variant_b_subject', 'variant_b_body']
        for field in required_fields:
            if field not in body:
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                                  detail=f"Missing required field: {field}")

        # Extract data
        test_name = body['test_name']
        email_type = body['email_type']
        variant_a_subject = body['variant_a_subject']
        variant_a_body = body['variant_a_body']
        variant_b_subject = body['variant_b_subject']
        variant_b_body = body['variant_b_body']
        duration_days = body.get('duration_days', 14)

        # Validate duration
        if duration_days < 1 or duration_days > 90:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                              detail="Duration must be between 1 and 90 days")

        # Create test in database
        cursor = database.cursor()
        start_date = datetime.now()
        end_date = start_date + timedelta(days=duration_days)

        cursor.execute("""
        INSERT INTO ab_tests
        (test_name, email_type, variant_a_subject, variant_a_body,
         variant_b_subject, variant_b_body, active, start_date, end_date, created_at)
        VALUES (?, ?, ?, ?, ?, ?, 1, ?, ?, ?)
        """, (
            test_name,
            email_type,
            variant_a_subject,
            variant_a_body,
            variant_b_subject,
            variant_b_body,
            start_date.isoformat(),
            end_date.isoformat(),
            datetime.now().isoformat()
        ))

        database.commit()
        test_id = cursor.lastrowid

        logger.info(f"✅ A/B test created: {test_name} (ID: {test_id}, Type: {email_type})")

        return JSONResponse({
            "status": "ok",
            "test_id": test_id,
            "message": "A/B test created successfully",
            "test": {
                "id": test_id,
                "test_name": test_name,
                "email_type": email_type,
                "active": 1,
                "start_date": start_date.isoformat(),
                "end_date": end_date.isoformat(),
                "status": "active"
            }
        }, status_code=201)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error creating A/B test: {str(e)}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                          detail="Error creating A/B test")


@router.get("/api/tests")
async def list_tests(active_only: Optional[bool] = True):
    """
    List all A/B tests (optionally filtered to active tests)

    Query parameters:
    - active_only: true (default) - Only show active tests

    Returns:
    {
        "status": "ok",
        "tests": [
            {
                "id": 1,
                "test_name": "Subject Line Test Q4",
                "email_type": "audit_report",
                "active": 1,
                "start_date": "2026-10-05T...",
                "end_date": "2026-10-19T...",
                "progress": 15
            }
        ]
    }
    """
    try:
        if not database:
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                              detail="Database not configured")

        cursor = database.cursor()

        # Build query based on filter
        if active_only:
            cursor.execute("""
            SELECT id, test_name, email_type, active, start_date, end_date
            FROM ab_tests
            WHERE active = 1
            ORDER BY start_date DESC
            """)
        else:
            cursor.execute("""
            SELECT id, test_name, email_type, active, start_date, end_date
            FROM ab_tests
            ORDER BY start_date DESC
            """)

        results = cursor.fetchall()

        tests = []
        for row in results:
            test_id, test_name, email_type, active, start_date, end_date = row

            # Calculate progress percentage
            start = datetime.fromisoformat(start_date)
            end = datetime.fromisoformat(end_date)
            now = datetime.now()
            duration = (end - start).total_seconds()
            elapsed = (now - start).total_seconds()
            progress = min(100, max(0, int((elapsed / duration) * 100))) if duration > 0 else 0

            tests.append({
                "id": test_id,
                "test_name": test_name,
                "email_type": email_type,
                "active": active,
                "start_date": start_date,
                "end_date": end_date,
                "progress": progress
            })

        logger.info(f"✅ Listed {len(tests)} A/B tests")
        return JSONResponse({
            "status": "ok",
            "tests": tests
        })

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error listing tests: {str(e)}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                          detail="Error listing tests")


@router.get("/api/tests/{test_id}/results")
async def get_test_results(test_id: int):
    """
    Get detailed results and statistical analysis for a test

    Returns:
    {
        "status": "ok",
        "test_id": 1,
        "test_name": "Subject Line Test Q4",
        "results": {
            "variant_a": {
                "sent": 500,
                "opened": 150,
                "clicked": 45,
                "converted": 12,
                "open_rate": 0.30,
                "click_rate": 0.09,
                "conversion_rate": 0.024
            },
            "variant_b": {...},
            "open_rate_p_value": 0.0234,
            "click_rate_p_value": 0.156,
            "conversion_rate_p_value": 0.012,
            "winner": "A",
            "confidence": 0.98,
            "open_rate_lift": 12.5,
            "click_rate_lift": 8.3,
            "conversion_rate_lift": 15.2,
            "recommendation": "Variant A is winner (+15.2% conversion lift). Deploy to all traffic."
        }
    }
    """
    try:
        if not database or not statistical_tester:
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                              detail="Database or statistical tester not configured")

        # Verify test exists
        cursor = database.cursor()
        cursor.execute("SELECT id, test_name FROM ab_tests WHERE id = ?", (test_id,))
        test_info = cursor.fetchone()

        if not test_info:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                              detail="Test not found")

        test_name = test_info[1]

        # Get statistical comparison
        comparison = statistical_tester.compare_variants(test_id)

        logger.info(f"✅ Retrieved results for test {test_id}")

        return JSONResponse({
            "status": "ok",
            "test_id": test_id,
            "test_name": test_name,
            "results": comparison
        })

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error getting test results: {str(e)}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                          detail="Error retrieving test results")


@router.post("/api/tests/{test_id}/winner")
async def mark_winner(test_id: int, request: Request):
    """
    Mark a test winner and optionally deploy to all traffic

    Request body:
    {
        "winner": "A",  // or "B"
        "deploy": true,
        "notes": "Deploying variant A due to 15% conversion lift"
    }

    Returns:
    {
        "status": "ok",
        "message": "Winner marked and deployment initiated",
        "winner": "A",
        "deployed": true
    }
    """
    try:
        if not database:
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                              detail="Database not configured")

        # Parse request
        try:
            body = await request.json()
        except Exception as e:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                              detail="Invalid JSON format")

        winner = body.get('winner', '').upper()
        deploy = body.get('deploy', False)
        notes = body.get('notes', '')

        if winner not in ['A', 'B']:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                              detail="Winner must be 'A' or 'B'")

        # Update test in database
        cursor = database.cursor()
        cursor.execute("""
        UPDATE ab_tests
        SET winner = ?, winner_determined_at = ?, active = ?
        WHERE id = ?
        """, (winner, datetime.now().isoformat(), 0 if deploy else 1, test_id))

        database.commit()

        logger.info(f"✅ Test {test_id} winner marked: {winner} (deployed: {deploy})")

        if deploy:
            logger.info(f"📊 Variant {winner} deployed to all traffic for test {test_id}")
            if notes:
                logger.info(f"   Notes: {notes}")

        return JSONResponse({
            "status": "ok",
            "message": "Winner marked" + (" and deployed" if deploy else ""),
            "winner": winner,
            "deployed": deploy
        })

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error marking winner: {str(e)}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                          detail="Error marking winner")


@router.post("/api/tests/{test_id}/pause")
async def pause_test(test_id: int):
    """
    Pause an active A/B test (stop sending new assignments)

    Returns:
    {
        "status": "ok",
        "message": "Test paused",
        "test_id": 1,
        "active": false
    }
    """
    try:
        if not database:
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                              detail="Database not configured")

        cursor = database.cursor()

        # Verify test exists and is active
        cursor.execute("SELECT active FROM ab_tests WHERE id = ?", (test_id,))
        result = cursor.fetchone()

        if not result:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                              detail="Test not found")

        if result[0] == 0:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                              detail="Test is already paused")

        # Pause test
        cursor.execute("""
        UPDATE ab_tests
        SET active = 0
        WHERE id = ?
        """, (test_id,))

        database.commit()

        logger.info(f"✅ Test {test_id} paused")

        return JSONResponse({
            "status": "ok",
            "message": "Test paused",
            "test_id": test_id,
            "active": False
        })

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error pausing test: {str(e)}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                          detail="Error pausing test")


@router.post("/api/tests/{test_id}/resume")
async def resume_test(test_id: int):
    """
    Resume a paused A/B test

    Returns:
    {
        "status": "ok",
        "message": "Test resumed",
        "test_id": 1,
        "active": true
    }
    """
    try:
        if not database:
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                              detail="Database not configured")

        cursor = database.cursor()

        # Verify test exists and is paused
        cursor.execute("SELECT active FROM ab_tests WHERE id = ?", (test_id,))
        result = cursor.fetchone()

        if not result:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                              detail="Test not found")

        if result[0] == 1:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                              detail="Test is already active")

        # Resume test
        cursor.execute("""
        UPDATE ab_tests
        SET active = 1
        WHERE id = ?
        """, (test_id,))

        database.commit()

        logger.info(f"✅ Test {test_id} resumed")

        return JSONResponse({
            "status": "ok",
            "message": "Test resumed",
            "test_id": test_id,
            "active": True
        })

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error resuming test: {str(e)}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                          detail="Error resuming test")


@router.delete("/api/tests/{test_id}")
async def delete_test(test_id: int):
    """
    Delete a test (soft delete - marks as inactive)

    Returns:
    {
        "status": "ok",
        "message": "Test deleted",
        "test_id": 1
    }
    """
    try:
        if not database:
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                              detail="Database not configured")

        cursor = database.cursor()

        # Verify test exists
        cursor.execute("SELECT id FROM ab_tests WHERE id = ?", (test_id,))
        if not cursor.fetchone():
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                              detail="Test not found")

        # Soft delete (mark as inactive and archived)
        cursor.execute("""
        UPDATE ab_tests
        SET active = 0, archived = 1
        WHERE id = ?
        """, (test_id,))

        database.commit()

        logger.info(f"✅ Test {test_id} deleted (archived)")

        return JSONResponse({
            "status": "ok",
            "message": "Test deleted",
            "test_id": test_id
        })

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error deleting test: {str(e)}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                          detail="Error deleting test")


@router.get("/api/tests/summary/{test_id}")
async def get_test_summary(test_id: int):
    """
    Get a summary of test status and current results

    Returns:
    {
        "status": "ok",
        "summary": {
            "test_id": 1,
            "test_name": "Subject Line Test Q4",
            "email_type": "audit_report",
            "active": 1,
            "start_date": "2026-10-05T...",
            "end_date": "2026-10-19T...",
            "progress": 15,
            "variant_a_sent": 500,
            "variant_b_sent": 500,
            "leader": "A",
            "confidence": 0.98,
            "recommendation": "Continue test - significant difference emerging"
        }
    }
    """
    try:
        if not database or not statistical_tester:
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                              detail="Database or statistical tester not configured")

        cursor = database.cursor()

        # Get test info
        cursor.execute("""
        SELECT id, test_name, email_type, active, start_date, end_date
        FROM ab_tests
        WHERE id = ?
        """, (test_id,))

        test_info = cursor.fetchone()
        if not test_info:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                              detail="Test not found")

        test_id, test_name, email_type, active, start_date, end_date = test_info

        # Calculate progress
        start = datetime.fromisoformat(start_date)
        end = datetime.fromisoformat(end_date)
        now = datetime.now()
        duration = (end - start).total_seconds()
        elapsed = (now - start).total_seconds()
        progress = min(100, max(0, int((elapsed / duration) * 100))) if duration > 0 else 0

        # Get variant results
        cursor.execute("""
        SELECT variant, COUNT(*) as count
        FROM ab_test_results
        WHERE test_id = ?
        GROUP BY variant
        """, (test_id,))

        results = cursor.fetchall()
        variant_a_sent = next((r[1] for r in results if r[0] == 'A'), 0)
        variant_b_sent = next((r[1] for r in results if r[0] == 'B'), 0)

        # Get statistical comparison
        comparison = statistical_tester.compare_variants(test_id)

        summary = {
            "test_id": test_id,
            "test_name": test_name,
            "email_type": email_type,
            "active": active,
            "start_date": start_date,
            "end_date": end_date,
            "progress": progress,
            "variant_a_sent": variant_a_sent,
            "variant_b_sent": variant_b_sent,
            "leader": comparison.get('winner'),
            "confidence": comparison.get('sample_adequate'),
            "recommendation": comparison.get('recommendation', 'Continue test')
        }

        logger.info(f"✅ Retrieved test summary for test {test_id}")

        return JSONResponse({
            "status": "ok",
            "summary": summary
        })

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error getting test summary: {str(e)}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                          detail="Error retrieving test summary")


@router.get("/api/tests/health")
async def health_check():
    """Health check endpoint for A/B testing service"""
    return JSONResponse({
        "status": "ok",
        "service": "ab-testing-api",
        "version": "1.0.0",
        "timestamp": datetime.now().isoformat()
    })
