#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
FASE 15 Phase 3 - Feature Flag Middleware
Guards Phase 3 routes and enforces kill-switch behavior
"""

import sqlite3
import logging
from functools import wraps
from fastapi import HTTPException

logger = logging.getLogger(__name__)

# =============================================================================
# Feature Flag System
# =============================================================================

class Phase3FeatureFlags:
    """Manage Phase 3 feature flags"""
    
    _flag_cache = {}
    _cache_ttl = 30  # Cache for 30 seconds to avoid DB hits on every request
    
    @classmethod
    def is_phase3_active(cls, db_path: str = "fase15.db") -> bool:
        """Check if Phase 3 is currently active"""
        try:
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT value FROM system_config 
                WHERE key = 'PHASE_3_ACTIVE'
            """)
            
            result = cursor.fetchone()
            conn.close()
            
            if result:
                is_active = result[0].lower() == 'true'
                logger.debug(f"Phase 3 flag check: {is_active}")
                return is_active
            
            logger.debug("Phase 3 flag not found, defaulting to False")
            return False
            
        except Exception as e:
            logger.error(f"Error reading Phase 3 flag: {str(e)}")
            return False
    
    @classmethod
    def is_personalization_enabled(cls, db_path: str = "fase15.db") -> bool:
        """Check if personalization is enabled"""
        try:
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT value FROM system_config 
                WHERE key = 'PERSONALIZATION_ENABLED'
            """)
            
            result = cursor.fetchone()
            conn.close()
            
            if result:
                return result[0].lower() == 'true'
            
            return False
            
        except Exception as e:
            logger.error(f"Error reading personalization flag: {str(e)}")
            return False
    
    @classmethod
    def is_ml_comparison_enabled(cls, db_path: str = "fase15.db") -> bool:
        """Check if ML vs rules comparison is enabled"""
        try:
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT value FROM system_config 
                WHERE key = 'ML_COMPARISON_ENABLED'
            """)
            
            result = cursor.fetchone()
            conn.close()
            
            if result:
                return result[0].lower() == 'true'
            
            return False
            
        except Exception as e:
            logger.error(f"Error reading ML comparison flag: {str(e)}")
            return False

# =============================================================================
# Route Guards (Decorators)
# =============================================================================

def require_phase3_active(func):
    """
    Decorator: Only allow if Phase 3 is active
    Used on routes that create new tests or apply winners
    """
    @wraps(func)
    async def wrapper(*args, **kwargs):
        if not Phase3FeatureFlags.is_phase3_active():
            logger.warning(f"Phase 3 inactive: blocking {func.__name__}")
            raise HTTPException(
                status_code=423,  # Locked
                detail="Phase 3 is currently disabled. Cannot create new A/B tests or apply winners."
            )
        return await func(*args, **kwargs)
    return wrapper

def allow_phase3_read_only(func):
    """
    Decorator: Allow reads even when Phase 3 is inactive
    Used on GET endpoints
    """
    @wraps(func)
    async def wrapper(*args, **kwargs):
        # Always allow reads
        return await func(*args, **kwargs)
    return wrapper

def require_personalization_enabled(func):
    """
    Decorator: Only allow if personalization is enabled
    """
    @wraps(func)
    async def wrapper(*args, **kwargs):
        if not Phase3FeatureFlags.is_personalization_enabled():
            logger.warning(f"Personalization disabled: blocking {func.__name__}")
            raise HTTPException(
                status_code=423,
                detail="Personalization is currently disabled."
            )
        return await func(*args, **kwargs)
    return wrapper

def require_ml_comparison_enabled(func):
    """
    Decorator: Only allow if ML comparison is enabled
    """
    @wraps(func)
    async def wrapper(*args, **kwargs):
        if not Phase3FeatureFlags.is_ml_comparison_enabled():
            logger.warning(f"ML comparison disabled: blocking {func.__name__}")
            raise HTTPException(
                status_code=423,
                detail="ML vs rules comparison is currently disabled."
            )
        return await func(*args, **kwargs)
    return wrapper

# =============================================================================
# Phase 3 Status Info
# =============================================================================

def get_phase3_info(db_path: str = "fase15.db") -> dict:
    """Get comprehensive Phase 3 status info"""
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Get all Phase 3 related flags
        cursor.execute("""
            SELECT key, value, updated_at 
            FROM system_config 
            WHERE key LIKE 'PHASE_3_%' OR key LIKE '%_ENABLED'
        """)
        
        configs = {row[0]: row[1] for row in cursor.fetchall()}
        conn.close()
        
        return {
            "phase3_active": configs.get('PHASE_3_ACTIVE', 'false').lower() == 'true',
            "personalization_enabled": configs.get('PERSONALIZATION_ENABLED', 'true').lower() == 'true',
            "ml_comparison_enabled": configs.get('ML_COMPARISON_ENABLED', 'true').lower() == 'true',
            "activation_time": configs.get('PHASE_3_ACTIVATION_TIME'),
            "deactivation_time": configs.get('PHASE_3_DEACTIVATION_TIME'),
            "all_configs": configs
        }
        
    except Exception as e:
        logger.error(f"Error getting Phase 3 info: {str(e)}")
        return {
            "phase3_active": False,
            "personalization_enabled": True,
            "ml_comparison_enabled": True,
            "error": str(e)
        }

