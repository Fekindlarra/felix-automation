#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PASO 14: Statistical Tester
Calculate statistical significance for A/B test results
"""

import logging
from typing import Dict, Tuple
from math import sqrt

logger = logging.getLogger(__name__)


class StatisticalTester:
    """Calculate statistical significance of A/B test results"""

    def __init__(self, significance_threshold: float = 0.05):
        """Initialize with significance threshold (p-value)"""
        self.significance_threshold = significance_threshold
        self.logger = logging.getLogger(__name__)

    def compare_variants(self, variant_a: Dict, variant_b: Dict) -> Dict:
        """
        Compare two variants and calculate statistical significance
        
        Args:
            variant_a: Dict with sent, opens, clicks, conversions
            variant_b: Dict with sent, opens, clicks, conversions
            
        Returns:
            Dict with rates, p-values, and winner determination
        """
        # Calculate conversion rates
        conv_rate_a = variant_a['conversions'] / variant_a['sent'] if variant_a['sent'] > 0 else 0
        conv_rate_b = variant_b['conversions'] / variant_b['sent'] if variant_b['sent'] > 0 else 0

        # Calculate open rates
        open_rate_a = variant_a['opens'] / variant_a['sent'] if variant_a['sent'] > 0 else 0
        open_rate_b = variant_b['opens'] / variant_b['sent'] if variant_b['sent'] > 0 else 0

        # Calculate click rates
        click_rate_a = variant_a['clicks'] / variant_a['sent'] if variant_a['sent'] > 0 else 0
        click_rate_b = variant_b['clicks'] / variant_b['sent'] if variant_b['sent'] > 0 else 0

        # Chi-square test for conversion rates
        p_value = self._chi_square_test(
            variant_a['conversions'],
            variant_a['sent'] - variant_a['conversions'],
            variant_b['conversions'],
            variant_b['sent'] - variant_b['conversions']
        )

        # Determine winner
        if p_value < self.significance_threshold:
            winner = 'B' if conv_rate_b > conv_rate_a else 'A'
            significance = 'Yes'
        else:
            winner = 'No significant difference'
            significance = 'No'

        # Calculate confidence interval
        ci_a = self._confidence_interval(conv_rate_a, variant_a['sent'])
        ci_b = self._confidence_interval(conv_rate_b, variant_b['sent'])

        return {
            'conversion_rate_a': conv_rate_a,
            'conversion_rate_b': conv_rate_b,
            'open_rate_a': open_rate_a,
            'open_rate_b': open_rate_b,
            'click_rate_a': click_rate_a,
            'click_rate_b': click_rate_b,
            'p_value': p_value,
            'significant': significance,
            'winner': winner,
            'confidence_interval_a': ci_a,
            'confidence_interval_b': ci_b,
            'improvement_percentage': ((conv_rate_b - conv_rate_a) / conv_rate_a * 100) if conv_rate_a > 0 else 0
        }

    def _chi_square_test(self, a1: int, a2: int, b1: int, b2: int) -> float:
        """Calculate chi-square test p-value (simplified)"""
        # Simplified chi-square calculation
        if (a1 + a2) * (b1 + b2) == 0:
            return 1.0

        total = a1 + a2 + b1 + b2
        expected_a1 = (a1 + b1) * (a1 + a2) / total
        expected_b1 = (a1 + b1) * (b1 + b2) / total

        if expected_a1 == 0 or expected_b1 == 0:
            return 1.0

        chi_square = ((a1 - expected_a1) ** 2 / expected_a1 + 
                      (b1 - expected_b1) ** 2 / expected_b1)

        # Rough approximation: chi_square > 3.84 ≈ p < 0.05
        return 0.05 if chi_square > 3.84 else 0.20

    def _confidence_interval(self, rate: float, n: int, 
                            confidence: float = 0.95) -> Tuple[float, float]:
        """Calculate 95% confidence interval for a rate"""
        if n == 0:
            return (0, 0)

        z = 1.96  # 95% confidence
        margin = z * sqrt(rate * (1 - rate) / n)

        return (
            max(0, rate - margin),
            min(1, rate + margin)
        )
