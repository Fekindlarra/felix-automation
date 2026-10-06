#!/usr/bin/env python3
"""
FASE 14 PASO 9: Statistical Tester
Chi-square test and confidence interval calculation for A/B test results
"""

import logging
import math
from typing import Optional, Dict
from sqlite3 import Connection
from datetime import datetime

logger = logging.getLogger(__name__)


class StatisticalTester:
    """
    Statistical significance testing for A/B email tests.
    Uses chi-square test (χ²) for independence of categorical variables.
    Calculates 95% confidence intervals for conversion rates.
    """

    # Significance threshold (p-value < 0.05 = 95% confidence)
    SIGNIFICANCE_THRESHOLD = 0.05

    # Chi-square critical value for df=1 at p=0.05 (3.841)
    CHI_SQUARE_CRITICAL = 3.841

    def __init__(self, db_connection: Connection):
        """
        Initialize statistical tester with database connection.

        Args:
            db_connection: SQLite database connection
        """
        self.db = db_connection
        self.cursor = self.db.cursor()

    def get_test_results(self, test_id: int) -> Optional[Dict]:
        """
        Fetch raw results for a test from database.

        Args:
            test_id: ID of A/B test

        Returns:
            Dict with variant_a and variant_b stats, or None
        """
        try:
            self.cursor.execute(
                """
                SELECT variant, SUM(sent_count), SUM(opens), SUM(clicks), SUM(conversions)
                FROM ab_test_results
                WHERE test_id = ?
                GROUP BY variant
                """,
                (test_id,)
            )
            results = self.cursor.fetchall()

            if len(results) < 2:
                logger.warning(f"⚠️ Test {test_id} doesn't have both variants yet")
                return None

            # Parse results (order may vary, so check variant)
            data = {}
            for row in results:
                variant = row[0]
                data[variant] = {
                    'sent': row[1] or 0,
                    'opens': row[2] or 0,
                    'clicks': row[3] or 0,
                    'conversions': row[4] or 0
                }

            logger.debug(f"📊 Test {test_id} results: {data}")
            return data

        except Exception as e:
            logger.error(f"❌ Error fetching test results: {e}")
            return None

    def calculate_conversion_rate(self, conversions: int, sent: int) -> float:
        """
        Calculate conversion rate (percentage).

        Args:
            conversions: Number of conversions
            sent: Number of emails sent

        Returns:
            Conversion rate as percentage (0-100)
        """
        if sent == 0:
            return 0.0
        return (conversions / sent) * 100

    def calculate_confidence_interval(self, successes: int, trials: int, confidence: float = 0.95) -> tuple:
        """
        Calculate confidence interval using Wilson score method.
        More accurate than simple binomial proportion for small samples.

        Args:
            successes: Number of successful events (e.g., conversions)
            trials: Number of total trials (e.g., emails sent)
            confidence: Confidence level (default 0.95 = 95%)

        Returns:
            Tuple (lower_bound, upper_bound) as percentages
        """
        if trials == 0:
            return 0.0, 100.0

        # Wilson score interval coefficients
        z = 1.96  # For 95% confidence
        p_hat = successes / trials
        denom = 1 + z * z / trials

        center = (p_hat + z * z / (2 * trials)) / denom
        spread = z * math.sqrt(p_hat * (1 - p_hat) / trials + z * z / (4 * trials * trials)) / denom

        lower = max(0, (center - spread) * 100)
        upper = min(100, (center + spread) * 100)

        return lower, upper

    def chi_square_test(self, variant_a: Dict, variant_b: Dict) -> Dict:
        """
        Perform chi-square test for independence.
        Tests if conversion rate difference is statistically significant.

        Null hypothesis: Variant A and B have same conversion rate
        Alternative hypothesis: Variant A and B have different conversion rates

        Args:
            variant_a: Dict with 'sent' and 'conversions'
            variant_b: Dict with 'sent' and 'conversions'

        Returns:
            Dict with chi_square, p_value, is_significant
        """
        try:
            # Contingency table
            a_converted = variant_a.get('conversions', 0)
            a_not_converted = variant_a.get('sent', 0) - a_converted
            b_converted = variant_b.get('conversions', 0)
            b_not_converted = variant_b.get('sent', 0) - b_converted

            # Chi-square statistic: χ² = n * (ad - bc)² / ((a+b)(c+d)(a+c)(b+d))
            n = a_converted + a_not_converted + b_converted + b_not_converted
            if n == 0:
                return {'chi_square': 0, 'p_value': 1.0, 'is_significant': False}

            numerator = n * ((a_converted * b_not_converted - a_not_converted * b_converted) ** 2)
            denominator = (
                (a_converted + a_not_converted) *
                (b_converted + b_not_converted) *
                (a_converted + b_converted) *
                (a_not_converted + b_not_converted)
            )

            if denominator == 0:
                return {'chi_square': 0, 'p_value': 1.0, 'is_significant': False}

            chi_square = numerator / denominator

            # Simplified p-value from chi-square critical value
            # For df=1, critical value at p=0.05 is 3.841
            p_value = 1.0 if chi_square < self.CHI_SQUARE_CRITICAL else 0.01

            is_significant = chi_square >= self.CHI_SQUARE_CRITICAL

            logger.debug(
                f"🔬 Chi-square: {chi_square:.4f}, p-value: {p_value}, significant: {is_significant}"
            )

            return {
                'chi_square': chi_square,
                'p_value': p_value,
                'is_significant': is_significant
            }

        except Exception as e:
            logger.error(f"❌ Error in chi-square test: {e}")
            return {'chi_square': 0, 'p_value': 1.0, 'is_significant': False}

    def compare_variants(self, test_id: int) -> Optional[Dict]:
        """
        Complete A/B test comparison with all metrics.
        Determines winner if statistically significant.

        Args:
            test_id: ID of A/B test

        Returns:
            Comprehensive comparison dict or None
        """
        try:
            # Fetch results
            results = self.get_test_results(test_id)
            if not results or 'A' not in results or 'B' not in results:
                logger.warning(f"⚠️ Cannot compare: incomplete data for test {test_id}")
                return None

            variant_a = results['A']
            variant_b = results['B']

            # Calculate rates
            conv_rate_a = self.calculate_conversion_rate(variant_a['conversions'], variant_a['sent'])
            conv_rate_b = self.calculate_conversion_rate(variant_b['conversions'], variant_b['sent'])

            # Calculate confidence intervals
            ci_a = self.calculate_confidence_interval(variant_a['conversions'], variant_a['sent'])
            ci_b = self.calculate_confidence_interval(variant_b['conversions'], variant_b['sent'])

            # Chi-square test
            chi_square_result = self.chi_square_test(variant_a, variant_b)

            # Determine winner
            winner = None
            winner_margin = 0
            if chi_square_result['is_significant']:
                if conv_rate_a > conv_rate_b:
                    winner = 'A'
                    winner_margin = conv_rate_a - conv_rate_b
                else:
                    winner = 'B'
                    winner_margin = conv_rate_b - conv_rate_a

            comparison = {
                'test_id': test_id,
                'variant_a': {
                    'sent': variant_a['sent'],
                    'conversions': variant_a['conversions'],
                    'conversion_rate': round(conv_rate_a, 2),
                    'confidence_interval': (round(ci_a[0], 2), round(ci_a[1], 2)),
                    'opens': variant_a['opens'],
                    'clicks': variant_a['clicks']
                },
                'variant_b': {
                    'sent': variant_b['sent'],
                    'conversions': variant_b['conversions'],
                    'conversion_rate': round(conv_rate_b, 2),
                    'confidence_interval': (round(ci_b[0], 2), round(ci_b[1], 2)),
                    'opens': variant_b['opens'],
                    'clicks': variant_b['clicks']
                },
                'statistics': {
                    'chi_square': round(chi_square_result['chi_square'], 4),
                    'p_value': chi_square_result['p_value'],
                    'is_significant': chi_square_result['is_significant'],
                    'confidence_level': '95%'
                },
                'winner': winner,
                'winner_margin_percentage': round(winner_margin, 2) if winner else 0,
                'recommendation': self._generate_recommendation(
                    winner, chi_square_result['is_significant'], winner_margin
                ),
                'calculated_at': datetime.utcnow().isoformat()
            }

            logger.info(f"✅ Test {test_id} analysis complete: winner={winner}")
            return comparison

        except Exception as e:
            logger.error(f"❌ Error comparing variants: {e}")
            return None

    def _generate_recommendation(self, winner: Optional[str], is_significant: bool, margin: float) -> str:
        """
        Generate actionable recommendation based on results.

        Args:
            winner: 'A', 'B', or None
            is_significant: Whether result is statistically significant
            margin: Winning margin percentage

        Returns:
            Recommendation string
        """
        if not is_significant:
            return "Recopilar más datos - diferencia no es estadísticamente significativa"
        
        if not winner:
            return "Ambas variantes tienen igual rendimiento"
        
        if margin < 5:
            return f"Variante {winner} es mejor, pero ganancia pequeña (<5%). Considerar A/B test adicional"
        elif margin < 15:
            return f"Variante {winner} es mejor ({margin:.1f}% ganancia). Implementar gradualmente"
        else:
            return f"Variante {winner} es significativamente mejor ({margin:.1f}% ganancia). ¡Implementar ahora!"

    def save_analysis(self, test_id: int, analysis: Dict) -> bool:
        """
        Save analysis results to database for audit trail.

        Args:
            test_id: ID of A/B test
            analysis: Comparison analysis dict

        Returns:
            True if successful
        """
        try:
            import json
            analysis_json = json.dumps(analysis, indent=2)

            self.cursor.execute(
                """
                UPDATE ab_tests
                SET analysis_results = ?, analyzed_at = ?
                WHERE id = ?
                """,
                (analysis_json, datetime.utcnow().isoformat(), test_id)
            )
            self.db.commit()

            logger.info(f"✅ Analysis saved for test {test_id}")
            return True

        except Exception as e:
            logger.error(f"❌ Error saving analysis: {e}")
            return False


if __name__ == "__main__":
    print("✅ StatisticalTester module loaded (import it in backend/routes/ab_testing_routes.py)")
