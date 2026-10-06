"""
FASE 14: Configuración centralizada del sistema de predicciones
Ajusta estos valores para tuning sin tocar el código de predicción
"""

# ============================================================================
# ANOMALY DETECTION THRESHOLDS
# ============================================================================

ANOMALY_THRESHOLDS = {
    # Tipo 1: Alta probabilidad pero baja confianza (inconsistencia)
    "high_prob_low_confidence": {
        "probability_min": 70,      # Si probabilidad > esto
        "confidence_max": 40,       # Y confianza < esto
        "severity": "high",
        "message": "Alta probabilidad pero baja confianza - revisar modelo"
    },

    # Tipo 2: Perfil de alto riesgo (muchos factores negativos)
    "high_risk_profile": {
        "risk_factor_threshold": 4,  # Si risk_factors >= esto
        "severity": "medium",
        "message": "{count} factores de riesgo identificados - evaluación manual recomendada"
    },

    # Tipo 3: Mismatch etapa-probabilidad (cliente avanzado pero baja prob)
    "stage_probability_mismatch": {
        "probability_max": 30,                              # Si probabilidad < esto
        "advanced_stages": ["propuesta", "negociacion"],   # Y cliente está en estas etapas
        "severity": "high",
        "message": "Baja probabilidad ({prob}%) pero cliente en etapa avanzada ({stage})"
    },

    # Tipo 4: Inactividad prolongada
    "prolonged_inactivity": {
        "days_threshold": 30,       # Si días sin contacto > esto
        "probability_decrease": 15, # Reduce prob este %
        "severity": "low",
        "message": "Sin contacto hace {days} días - probabilidad reducida"
    }
}

# ============================================================================
# RECOMMENDATION ENGINE
# ============================================================================

RECOMMENDATIONS = {
    # Basadas en probabilidad y etapa
    "rules": [
        # Prospectos de alta probabilidad
        {
            "condition": lambda prob, stage, audit: prob > 80 and stage == "prospecto",
            "action": "Contacto inmediato",
            "timeline": 1,
            "reason": "Alta probabilidad - seguimiento prioritario"
        },

        # Prospectos de baja probabilidad
        {
            "condition": lambda prob, stage, audit: prob < 50 and stage == "prospecto",
            "action": "Revisar y re-segmentar",
            "timeline": 7,
            "reason": "Baja probabilidad - requiere mejor calificación"
        },

        # En propuesta hace poco
        {
            "condition": lambda prob, stage, audit: stage == "propuesta" and prob > 70,
            "action": "Seguimiento de propuesta",
            "timeline": 2,
            "reason": "Propuesta enviada - seguimiento en 48h"
        },

        # En negociación
        {
            "condition": lambda prob, stage, audit: stage == "negociacion",
            "action": "Acelerar cierre",
            "timeline": 1,
            "reason": "Fase avanzada - focus en cierre"
        },

        # Auditoría profunda de alto valor
        {
            "condition": lambda prob, stage, audit: audit == "deep" and prob > 65,
            "action": "Llamada ejecutiva",
            "timeline": 1,
            "reason": "Alto valor y buena probabilidad"
        },

        # Default
        {
            "condition": lambda prob, stage, audit: True,
            "action": "Seguimiento regular",
            "timeline": 3,
            "reason": "Seguimiento según el flujo"
        }
    ],

    # Días estimados a cierre por etapa
    "days_to_close": {
        "prospecto": 14,      # 2 semanas desde captura
        "propuesta": 10,      # 1.5 semanas desde propuesta
        "negociacion": 5,     # 5 días de negociación típica
        "cerrado": 0          # Ya cerrado
    }
}

# ============================================================================
# PREDICTION FACTORS
# ============================================================================

POSITIVE_FACTORS = {
    "high_intention": {
        "keywords": ["urgencia", "necesita", "importante", "ahora", "pronto"],
        "weight": 15,
        "label": "Alta intención de compra"
    },

    "budget_available": {
        "keywords": ["presupuesto", "aprobado", "fondos", "disponible"],
        "weight": 20,
        "label": "Presupuesto disponible"
    },

    "authority": {
        "keywords": ["decisión", "aprueba", "autoridad", "firma", "poder"],
        "weight": 15,
        "label": "Autoridad de decisión"
    },

    "timeline": {
        "keywords": ["deadline", "fecha", "vencimiento", "plazo", "límite"],
        "weight": 10,
        "label": "Timeline claro"
    },

    "advanced_stage": {
        "stages": ["propuesta", "negociacion"],
        "weight": 25,
        "label": "Etapa avanzada"
    },

    "deep_audit_interest": {
        "audit_types": ["deep"],
        "weight": 15,
        "label": "Auditoría profunda"
    }
}

RISK_FACTORS = {
    "limited_budget": {
        "keywords": ["limitado", "presupuesto pequeño", "restricción", "limitar", "bajo"],
        "weight": -15,
        "label": "Presupuesto limitado"
    },

    "slow_season": {
        "keywords": ["baja", "lento", "temporada", "tranquilo"],
        "weight": -10,
        "label": "Temporada lenta"
    },

    "competition": {
        "keywords": ["competencia", "rival", "alternativa", "otro", "comparar"],
        "weight": -12,
        "label": "Competencia activa"
    },

    "indecision": {
        "keywords": ["decidir", "duda", "incertidumbre", "evaluar", "pensar"],
        "weight": -10,
        "label": "Indecisión del equipo"
    },

    "procrastination": {
        "days_without_contact": 20,
        "weight": -15,
        "label": "Inactividad prolongada"
    },

    "low_engagement": {
        "keywords": ["no", "no interesa", "no urgente", "puede esperar"],
        "weight": -18,
        "label": "Bajo engagement"
    }
}

# ============================================================================
# CONFIDENCE SCORE ADJUSTMENT
# ============================================================================

CONFIDENCE_FACTORS = {
    "complete_profile": {
        "required_fields": ["name", "email", "company", "phone", "message"],
        "weight": 20,
        "label": "Perfil completo"
    },

    "message_quality": {
        "min_length": 10,
        "weight": 15,
        "label": "Mensaje detallado"
    },

    "audit_type_specified": {
        "weight": 15,
        "label": "Tipo de auditoría claro"
    },

    "industry_match": {
        "weight": 10,
        "label": "Industria conocida"
    },

    "historical_data": {
        "weight": 20,
        "label": "Datos históricos disponibles"
    }
}

# ============================================================================
# PERFORMANCE THRESHOLDS
# ============================================================================

PERFORMANCE = {
    "excellent_probability": 85,        # >= esto = Excelente
    "good_probability": 70,             # >= esto = Bueno
    "fair_probability": 50,             # >= esto = Regular
    "poor_probability": 30,             # < esto = Malo

    "excellent_confidence": 90,         # >= esto = Excelente
    "good_confidence": 75,              # >= esto = Bueno
    "fair_confidence": 60,              # >= esto = Regular
    "poor_confidence": 40               # < esto = Malo
}

# ============================================================================
# ML MODEL HYPERPARAMETERS (for future ML integration)
# ============================================================================

ML_CONFIG = {
    "feature_engineering": {
        "use_tfidf": True,                  # Usar TF-IDF para análisis de texto
        "tfidf_max_features": 100,
        "polynomial_features": False,
        "feature_scaling": "standard"       # standard, minmax, robust
    },

    "model_selection": {
        "algorithm": "logistic_regression", # logistic_regression, random_forest, svm, xgboost
        "random_state": 42,
        "n_jobs": -1                       # Usar todos los cores
    },

    "hyperparameters": {
        "logistic_regression": {
            "C": 1.0,
            "max_iter": 1000
        },
        "random_forest": {
            "n_estimators": 100,
            "max_depth": 10,
            "min_samples_split": 5
        }
    },

    "training": {
        "test_size": 0.2,
        "validation_split": 0.15,
        "cross_validation_folds": 5
    }
}

# ============================================================================
# NOTIFICATION SETTINGS
# ============================================================================

NOTIFICATIONS = {
    "enable_email": True,
    "enable_websocket": True,

    "triggers": {
        "high_probability": {
            "threshold": 85,
            "send_to": ["admin"],
            "message": "🎯 Lead de alta probabilidad capturado"
        },

        "anomaly_detected": {
            "threshold": "any",
            "send_to": ["admin"],
            "message": "⚠️ Anomalía detectada en predicción"
        },

        "stage_change": {
            "threshold": "any",
            "send_to": ["admin"],
            "message": "📈 Cliente movido a nueva etapa"
        }
    }
}

# ============================================================================
# UTILITIES
# ============================================================================

def get_probability_level(prob: float) -> str:
    """Clasificar probabilidad en nivel"""
    if prob >= PERFORMANCE["excellent_probability"]:
        return "EXCELENTE"
    elif prob >= PERFORMANCE["good_probability"]:
        return "BUENO"
    elif prob >= PERFORMANCE["fair_probability"]:
        return "REGULAR"
    else:
        return "MALO"


def get_confidence_level(conf: float) -> str:
    """Clasificar confianza en nivel"""
    if conf >= PERFORMANCE["excellent_confidence"]:
        return "MUY ALTA"
    elif conf >= PERFORMANCE["good_confidence"]:
        return "ALTA"
    elif conf >= PERFORMANCE["fair_confidence"]:
        return "MEDIA"
    else:
        return "BAJA"


def apply_recommendation(probability: float, stage: str, audit_type: str) -> dict:
    """Aplicar recomendación basada en reglas"""
    for rule in RECOMMENDATIONS["rules"]:
        if rule["condition"](probability, stage, audit_type):
            return {
                "action": rule["action"],
                "days": rule["timeline"],
                "reason": rule["reason"]
            }
    return {
        "action": "Seguimiento regular",
        "days": 3,
        "reason": "No hay regla específica"
    }


# ============================================================================
# DEBUG/TESTING
# ============================================================================

DEBUG = True

if DEBUG:
    print("""
    ✅ CONFIG LOADED

    Anomaly Thresholds: {}
    Positive Factors: {}
    Risk Factors: {}
    Recommendations: {}
    Performance Levels: {}
    """.format(
        len(ANOMALY_THRESHOLDS),
        len(POSITIVE_FACTORS),
        len(RISK_FACTORS),
        len(RECOMMENDATIONS["rules"]),
        len(PERFORMANCE)
    ))
