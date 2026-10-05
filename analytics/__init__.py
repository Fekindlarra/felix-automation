#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Analytics Module - FASE 10 Advanced Analytics
Análisis predictivo, detección de anomalías, recomendaciones inteligentes
"""

from .predictor import ConversionPredictor
from .anomaly_detector import AnomalyDetector
from .recommender import RecommendationEngine

__all__ = [
    'ConversionPredictor',
    'AnomalyDetector',
    'RecommendationEngine'
]
