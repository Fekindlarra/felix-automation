#!/usr/bin/env python3
"""
FASE 14 PASO 11: A/B Testing API Routes
Complete CRUD API for A/B test management and results
Factory pattern for dependency injection - compatible with app.py initialization
"""

import logging
import json
from datetime import datetime, timedelta
from typing import Optional, Dict, List
from fastapi import APIRouter, HTTPException, status, Query
from pydantic import BaseModel, Field
from sqlite3 import Connection

logger = logging.getLogger(__name__)

# Global database connection (will be injected by main app)
database = None

# Global WebSocket manager (will be injected by main app)
websocket_manager = None

# Module-level router
router = APIRouter(prefix="/api/tests", tags=["A/B Testing"])


# ==================== PHASE 3 FEATURE FLAG ====================

def is_phase3_active() -> bool:
    """
    Check if Phase 3 is currently active
    Returns False if database not initialized or flag not set
    """
    if database is None:
        return False

    try:
        cursor = database.cursor()
        cursor.execute("""
            SELECT value FROM system_config WHERE key = 'PHASE_3_ACTIVE'
        """)
        result = cursor.fetchone()
        return result[0] == 'true' if result else False
    except Exception as e:
        logger.warning(f"⚠️ Could not check Phase 3 status: {e}")
        return False


def require_phase3_active():
    """
    Guard function for routes that require Phase 3 to be active
    Raises HTTPException with 423 (Locked) status if Phase 3 disabled
    """
    if not is_phase3_active():
        raise HTTPException(
            status_code=status.HTTP_423_LOCKED,
            detail="Phase 3 is currently disabled. Cannot perform this operation."
        )

# ==================== REQUEST/RESPONSE MODELS ====================

class VariantContent(BaseModel):
    """Content for a single test variant"""
    subject: str = Field(..., description="Email subject line")
    body: str = Field(..., description="Email body content (HTML)")


class CreateABTestRequest(BaseModel):
    """Request to create new A/B test"""
    test_name: str = Field(..., description="Name of the test")
    email_type: str = Field(..., description="Email type: audit_report, proposal, followup_1, etc")
    variant_a: VariantContent = Field(..., description="Variant A content")
    variant_b: VariantContent = Field(..., description="Variant B content")
    duration_days: int = Field(default=14, description="Test duration in days")
    notes: Optional[str] = Field(None, description="Optional test notes")


class ABTestResponse(BaseModel):
    """Response with A/B test data"""
    id: int
    test_name: str
    email_type: str
    active: bool
    variant_a: Dict
    variant_b: Dict
    start_date: str
    end_date: Optional[str] = None
    created_at: str
    distribution: Dict = Field(default_factory=dict)


class TestResultsResponse(BaseModel):
    """Response with test results and statistics"""
    test_id: int
    test_name: str
    email_type: str
    variant_a: Dict
    variant_b: Dict
    statistics: Dict
    winner: Optional[str] = None
    winner_margin: float = 0
    recommendation: str
    calculated_at: str


class WinnerResponse(BaseModel):
    """Response when marking winner"""
    test_id: int
    winner: str
    marked_at: str
    recommendation: str


# ==================== INITIALIZATION ====================

def init_ab_testing(db_connection: Connection, ws_manager=None):
    """Initialize A/B testing routes with database connection and optional WebSocket manager"""
    global database, websocket_manager
    database = db_connection
    websocket_manager = ws_manager
    logger.info("✅ A/B Testing routes initialized with database connection")
    if websocket_manager:
        logger.info("✅ A/B Testing routes connected to WebSocket manager")


def create_ab_testing_router(db_connection: Connection):
    """
    DEPRECATED: Use init_ab_testing() instead.
    Factory function kept for backwards compatibility.
    Returns the module-level router after initializing it.
    """
    init_ab_testing(db_connection)
    return router


# ==================== ROUTE HANDLERS ====================

@router.post("", response_model=ABTestResponse, status_code=status.HTTP_201_CREATED)
async def create_test(request: CreateABTestRequest):
    """
    Create a new A/B test

    - **test_name**: Name of the test
    - **email_type**: Type of email (audit_report, proposal, etc)
    - **variant_a**: Content for variant A
    - **variant_b**: Content for variant B
    - **duration_days**: How many days to run the test (default: 14)

    ⚠️ Phase 3 Active: This endpoint requires Phase 3 to be active
    """
    # Check Phase 3 is active
    require_phase3_active()

    if database is None:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Database not initialized"
        )

    try:
        logger.info(f"🧪 Creating A/B test: {request.test_name} for {request.email_type}")

        cursor = database.cursor()
        now = datetime.utcnow().isoformat()

        # Calculate end date
        end_date = (datetime.utcnow() + timedelta(days=request.duration_days)).isoformat()

        # Serialize variant content to JSON
        variant_a_json = json.dumps({
            "subject": request.variant_a.subject,
            "body": request.variant_a.body
        })
        variant_b_json = json.dumps({
            "subject": request.variant_b.subject,
            "body": request.variant_b.body
        })

        # Insert test
        cursor.execute(
            """
            INSERT INTO ab_tests
            (test_name, email_type, active, variant_a, variant_b, start_date, end_date, notes, created_at)
            VALUES (?, ?, 1, ?, ?, ?, ?, ?, ?)
            """,
            (request.test_name, request.email_type, variant_a_json, variant_b_json,
             now, end_date, request.notes, now)
        )
        database.commit()
        test_id = cursor.lastrowid

        logger.info(f"✅ A/B test created: ID {test_id}")

        # Broadcast test creation event to WebSocket
        if websocket_manager:
            try:
                from backend.events import EventFactory
                event = EventFactory.test_created(
                    client_id=0,  # System-level test (not tied to specific client)
                    test_id=test_id,
                    test_name=request.test_name,
                    email_type=request.email_type,
                    duration_days=request.duration_days
                )
                websocket_manager.broadcast(event, role='admin')
                logger.info(f"📢 Broadcasted test:created for test {test_id}")
            except Exception as e:
                logger.error(f"⚠️ Failed to broadcast test:created: {e}")

        return ABTestResponse(
            id=test_id,
            test_name=request.test_name,
            email_type=request.email_type,
            active=True,
            variant_a={"subject": request.variant_a.subject, "body": request.variant_a.body},
            variant_b={"subject": request.variant_b.subject, "body": request.variant_b.body},
            start_date=now,
            created_at=now
        )

    except Exception as e:
        logger.error(f"❌ Error creating test: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Error creating test: {str(e)}"
        )


@router.get("", response_model=List[ABTestResponse])
async def list_tests(active_only: bool = Query(False, description="Only show active tests")):
    """
    List all A/B tests

    - **active_only**: If true, only return currently active tests
    """
    if database is None:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Database not initialized"
        )

    try:
        from agents.email_variant_assigner import EmailVariantAssigner

        cursor = database.cursor()

        query = "SELECT id, test_name, email_type, active, variant_a, variant_b, start_date, end_date, created_at FROM ab_tests"
        if active_only:
            query += " WHERE active = 1"
        query += " ORDER BY created_at DESC"

        cursor.execute(query)
        results = cursor.fetchall()

        assigner = EmailVariantAssigner(database)
        tests = []
        for row in results:
            test_id, name, email_type, active, var_a, var_b, start, end, created = row
            dist = assigner.get_test_distribution(test_id)

            tests.append(ABTestResponse(
                id=test_id,
                test_name=name,
                email_type=email_type,
                active=active,
                variant_a=json.loads(var_a) if var_a else {},
                variant_b=json.loads(var_b) if var_b else {},
                start_date=start,
                end_date=end,
                created_at=created,
                distribution=dist
            ))

        logger.info(f"📋 Listed {len(tests)} tests")
        return tests

    except Exception as e:
        logger.error(f"❌ Error listing tests: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error fetching tests"
        )


@router.get("/{test_id}", response_model=ABTestResponse)
async def get_test(test_id: int):
    """Get a specific A/B test by ID"""
    if database is None:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Database not initialized"
        )

    try:
        cursor = database.cursor()
        cursor.execute(
            "SELECT id, test_name, email_type, active, variant_a, variant_b, start_date, end_date, created_at FROM ab_tests WHERE id = ?",
            (test_id,)
        )
        row = cursor.fetchone()

        if not row:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Test {test_id} not found"
            )

        test_id, name, email_type, active, var_a, var_b, start, end, created = row

        from agents.email_variant_assigner import EmailVariantAssigner
        assigner = EmailVariantAssigner(database)
        dist = assigner.get_test_distribution(test_id)

        return ABTestResponse(
            id=test_id,
            test_name=name,
            email_type=email_type,
            active=active,
            variant_a=json.loads(var_a) if var_a else {},
            variant_b=json.loads(var_b) if var_b else {},
            start_date=start,
            end_date=end,
            created_at=created,
            distribution=dist
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error fetching test: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error fetching test"
        )


@router.get("/{test_id}/results", response_model=TestResultsResponse)
async def get_test_results(test_id: int):
    """Get test results with statistical analysis"""
    if database is None:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Database not initialized"
        )

    try:
        from agents.statistical_tester import StatisticalTester

        cursor = database.cursor()
        cursor.execute("SELECT test_name, email_type, variant_a, variant_b FROM ab_tests WHERE id = ?", (test_id,))
        test = cursor.fetchone()

        if not test:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Test {test_id} not found"
            )

        test_name, email_type, variant_a, variant_b = test
        tester = StatisticalTester(database)
        results = tester.compare_variants(test_id)

        return TestResultsResponse(
            test_id=test_id,
            test_name=test_name,
            email_type=email_type,
            variant_a=json.loads(variant_a) if variant_a else {},
            variant_b=json.loads(variant_b) if variant_b else {},
            statistics=results.get('statistics', {}),
            winner=results.get('winner'),
            winner_margin=results.get('winner_margin', 0),
            recommendation=results.get('recommendation', ''),
            calculated_at=datetime.utcnow().isoformat()
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error getting test results: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error calculating test results"
        )


@router.post("/{test_id}/winner", response_model=WinnerResponse)
async def mark_winner(test_id: int, winner: str = Query(..., description="Winner variant: A or B")):
    """
    Mark the winner of a test and update test status

    ⚠️ Phase 3 Active: This endpoint requires Phase 3 to be active
    """
    # Check Phase 3 is active
    require_phase3_active()

    if database is None:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Database not initialized"
        )

    try:
        if winner not in ['A', 'B']:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Winner must be 'A' or 'B'"
            )

        logger.info(f"🏆 Marking variant {winner} as winner for test {test_id}")

        cursor = database.cursor()
        cursor.execute("SELECT test_name, email_type, planned_duration_days FROM ab_tests WHERE id = ?", (test_id,))
        test = cursor.fetchone()

        if not test:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Test {test_id} not found"
            )

        test_name, email_type, duration_days = test

        # Update test
        cursor.execute(
            "UPDATE ab_tests SET active = 0 WHERE id = ?",
            (test_id,)
        )
        database.commit()

        logger.info(f"✅ Winner marked: variant {winner} for test {test_id}")

        # Apply personalization and broadcast winner announcement
        try:
            from agents.personalization_engine import PersonalizationEngine
            engine = PersonalizationEngine(database)
            engine.apply_test_winner(test_id, winner, websocket_manager)
            logger.info(f"✅ Personalization applied for test {test_id}")
        except Exception as e:
            logger.error(f"⚠️ Error applying personalization: {e}")

        return WinnerResponse(
            test_id=test_id,
            winner=winner,
            marked_at=datetime.utcnow().isoformat(),
            recommendation=f"Deploy variant {winner}"
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error marking winner: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error marking winner"
        )


@router.post("/{test_id}/pause")
async def pause_test(test_id: int):
    """Pause an active A/B test

    ⚠️ Phase 3 Active: This endpoint requires Phase 3 to be active
    """
    # Check Phase 3 is active
    require_phase3_active()

    if database is None:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Database not initialized"
        )

    try:
        logger.info(f"⏸️  Pausing test {test_id}")

        cursor = database.cursor()
        cursor.execute(
            "SELECT test_name, email_type FROM ab_tests WHERE id = ?",
            (test_id,)
        )
        test_row = cursor.fetchone()

        cursor.execute(
            "UPDATE ab_tests SET active = 0 WHERE id = ?",
            (test_id,)
        )
        database.commit()

        logger.info(f"✅ Test {test_id} paused")

        # Broadcast test paused event
        if websocket_manager and test_row:
            try:
                from backend.events import EventFactory
                event = EventFactory.test_paused(
                    client_id=0,  # System-level test
                    test_id=test_id,
                    test_name=test_row[0]
                )
                websocket_manager.broadcast(event, role='admin')
                logger.info(f"📢 Broadcasted test:paused for test {test_id}")
            except Exception as e:
                logger.error(f"⚠️ Failed to broadcast test:paused: {e}")

        return {
            "status": "paused",
            "test_id": test_id,
            "paused_at": datetime.utcnow().isoformat()
        }

    except Exception as e:
        logger.error(f"❌ Error pausing test: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error pausing test"
        )


@router.post("/{test_id}/resume")
async def resume_test(test_id: int):
    """Resume a paused A/B test

    ⚠️ Phase 3 Active: This endpoint requires Phase 3 to be active
    """
    # Check Phase 3 is active
    require_phase3_active()

    if database is None:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Database not initialized"
        )

    try:
        logger.info(f"▶️  Resuming test {test_id}")

        cursor = database.cursor()
        cursor.execute(
            "UPDATE ab_tests SET active = 1 WHERE id = ?",
            (test_id,)
        )
        database.commit()

        logger.info(f"✅ Test {test_id} resumed")

        return {
            "status": "active",
            "test_id": test_id,
            "resumed_at": datetime.utcnow().isoformat()
        }

    except Exception as e:
        logger.error(f"❌ Error resuming test: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error resuming test"
        )


if __name__ == "__main__":
    logger.info("A/B Testing API Routes Module Loaded")
