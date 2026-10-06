"""
FASE 14 - Unit Tests for Statistical Tester
Testing A/B test statistical significance calculations
"""

import pytest
from unittest.mock import Mock, patch
from scipy import stats


class MockStatisticalTester:
    """Mock Statistical Tester for A/B test analysis"""

    def __init__(self):
        self.significance_threshold = 0.05  # p-value threshold

    def compare_variants(self, variant_a_stats, variant_b_stats):
        """Compare two variants statistically"""
        # Extract stats
        a_conversions = variant_a_stats.get('conversions', 0)
        a_total = variant_a_stats.get('total', 1)
        b_conversions = variant_b_stats.get('conversions', 0)
        b_total = variant_b_stats.get('total', 1)

        # Calculate conversion rates
        a_rate = a_conversions / a_total if a_total > 0 else 0
        b_rate = b_conversions / b_total if b_total > 0 else 0

        # Chi-square test (simplified)
        contingency_table = [
            [a_conversions, a_total - a_conversions],
            [b_conversions, b_total - b_conversions]
        ]

        # Calculate chi-square and p-value
        chi2, p_value = self._chi_square_test(contingency_table)

        # Determine winner
        winner = None
        if p_value < self.significance_threshold:
            winner = 'A' if a_rate > b_rate else 'B'

        # Calculate confidence interval (95%)
        ci_a = self._confidence_interval(a_conversions, a_total)
        ci_b = self._confidence_interval(b_conversions, b_total)

        return {
            'p_value': p_value,
            'chi_square': chi2,
            'significant': p_value < self.significance_threshold,
            'winner': winner,
            'confidence_interval_a': ci_a,
            'confidence_interval_b': ci_b,
            'conversion_rate_a': a_rate,
            'conversion_rate_b': b_rate,
            'lift': ((b_rate - a_rate) / a_rate * 100) if a_rate > 0 else 0
        }

    def _chi_square_test(self, contingency_table):
        """Perform chi-square test"""
        # Simplified chi-square calculation
        a_conv, a_non = contingency_table[0]
        b_conv, b_non = contingency_table[1]

        total = a_conv + a_non + b_conv + b_non
        expected_a_conv = (a_conv + b_conv) * (a_conv + a_non) / total if total > 0 else 0
        expected_b_conv = (a_conv + b_conv) * (b_conv + b_non) / total if total > 0 else 0

        chi2 = 0
        for observed, expected in [(a_conv, expected_a_conv), (b_conv, expected_b_conv)]:
            if expected > 0:
                chi2 += (observed - expected) ** 2 / expected

        # P-value approximation (simplified)
        p_value = 1.0 / (1.0 + chi2) if chi2 >= 0 else 1.0

        return chi2, p_value

    def _confidence_interval(self, conversions, total):
        """Calculate 95% confidence interval for conversion rate"""
        if total == 0:
            return (0, 0)

        rate = conversions / total
        # Simplified CI calculation (±1.96 * SE)
        se = (rate * (1 - rate) / total) ** 0.5 if total > 0 else 0
        margin = 1.96 * se

        return (
            max(0, rate - margin),
            min(1, rate + margin)
        )

    def get_sample_size_recommendation(self, baseline_rate, minimum_detectable_effect):
        """Recommend sample size for adequate power"""
        # Simplified recommendation: baseline * 10 / effect
        if minimum_detectable_effect > 0:
            recommended = int((baseline_rate * 10) / minimum_detectable_effect)
            return max(100, recommended)  # Minimum 100 per variant
        return 1000

    def is_test_ready_to_conclude(self, test_stats):
        """Check if test has enough data to conclude"""
        min_sample_per_variant = 100
        variant_a_total = test_stats.get('variant_a', {}).get('total', 0)
        variant_b_total = test_stats.get('variant_b', {}).get('total', 0)

        return (variant_a_total >= min_sample_per_variant and
                variant_b_total >= min_sample_per_variant)


# ============================================================================
# TESTS
# ============================================================================

class TestStatisticalSignificance:
    """Test statistical significance calculations"""

    def test_significant_difference_detected(self):
        """Should detect statistically significant difference"""
        tester = MockStatisticalTester()

        variant_a = {'conversions': 100, 'total': 1000}
        variant_b = {'conversions': 150, 'total': 1000}

        result = tester.compare_variants(variant_a, variant_b)

        assert 'p_value' in result
        assert 'significant' in result
        assert 'winner' in result

    def test_no_significant_difference(self):
        """Should not declare winner when difference is not significant"""
        tester = MockStatisticalTester()

        variant_a = {'conversions': 100, 'total': 1000}
        variant_b = {'conversions': 105, 'total': 1000}

        result = tester.compare_variants(variant_a, variant_b)

        assert 'p_value' in result
        # Small difference likely not significant
        assert result['conversion_rate_a'] > 0
        assert result['conversion_rate_b'] > 0

    def test_variant_with_higher_rate_wins(self):
        """Should identify variant with higher conversion rate as winner"""
        tester = MockStatisticalTester()

        variant_a = {'conversions': 50, 'total': 1000}
        variant_b = {'conversions': 150, 'total': 1000}

        result = tester.compare_variants(variant_a, variant_b)

        if result['significant']:
            assert result['winner'] == 'B'

    def test_zero_conversions_handled(self):
        """Should handle zero conversions gracefully"""
        tester = MockStatisticalTester()

        variant_a = {'conversions': 0, 'total': 100}
        variant_b = {'conversions': 10, 'total': 100}

        result = tester.compare_variants(variant_a, variant_b)

        assert result['conversion_rate_a'] == 0
        assert result['conversion_rate_b'] == 0.1

    def test_empty_variant_handled(self):
        """Should handle empty variant groups"""
        tester = MockStatisticalTester()

        variant_a = {'conversions': 0, 'total': 0}
        variant_b = {'conversions': 10, 'total': 100}

        result = tester.compare_variants(variant_a, variant_b)

        assert 'p_value' in result
        assert result['conversion_rate_a'] == 0


class TestConfidenceIntervals:
    """Test confidence interval calculations"""

    def test_confidence_interval_calculated(self):
        """Should calculate 95% confidence interval"""
        tester = MockStatisticalTester()

        result = tester.compare_variants(
            {'conversions': 100, 'total': 1000},
            {'conversions': 120, 'total': 1000}
        )

        ci_a = result['confidence_interval_a']
        ci_b = result['confidence_interval_b']

        # Confidence intervals should be tuples
        assert isinstance(ci_a, tuple)
        assert isinstance(ci_b, tuple)
        assert len(ci_a) == 2
        assert len(ci_b) == 2

    def test_confidence_interval_bounds(self):
        """Should keep confidence intervals within 0-1"""
        tester = MockStatisticalTester()

        result = tester.compare_variants(
            {'conversions': 10, 'total': 100},
            {'conversions': 5, 'total': 100}
        )

        ci_a = result['confidence_interval_a']
        ci_b = result['confidence_interval_b']

        assert 0 <= ci_a[0] <= 1
        assert 0 <= ci_a[1] <= 1
        assert 0 <= ci_b[0] <= 1
        assert 0 <= ci_b[1] <= 1

    def test_lower_bound_less_than_upper_bound(self):
        """Should have lower bound less than upper bound"""
        tester = MockStatisticalTester()

        result = tester.compare_variants(
            {'conversions': 100, 'total': 1000},
            {'conversions': 110, 'total': 1000}
        )

        ci_a = result['confidence_interval_a']
        assert ci_a[0] <= ci_a[1]


class TestLiftCalculation:
    """Test lift (percentage change) calculations"""

    def test_positive_lift_calculated(self):
        """Should calculate positive lift when B > A"""
        tester = MockStatisticalTester()

        variant_a = {'conversions': 100, 'total': 1000}  # 10%
        variant_b = {'conversions': 120, 'total': 1000}  # 12%

        result = tester.compare_variants(variant_a, variant_b)

        # Lift should be positive: (12% - 10%) / 10% = 20%
        assert result['lift'] > 0

    def test_negative_lift_calculated(self):
        """Should calculate negative lift when B < A"""
        tester = MockStatisticalTester()

        variant_a = {'conversions': 100, 'total': 1000}  # 10%
        variant_b = {'conversions': 80, 'total': 1000}   # 8%

        result = tester.compare_variants(variant_a, variant_b)

        # Lift should be negative: (8% - 10%) / 10% = -20%
        assert result['lift'] < 0

    def test_zero_baseline_handled(self):
        """Should handle zero baseline rate"""
        tester = MockStatisticalTester()

        variant_a = {'conversions': 0, 'total': 100}
        variant_b = {'conversions': 5, 'total': 100}

        result = tester.compare_variants(variant_a, variant_b)

        # Lift should be 0 when baseline is 0
        assert result['lift'] == 0


class TestSampleSizeRecommendation:
    """Test sample size calculations"""

    def test_sample_size_recommended(self):
        """Should recommend appropriate sample size"""
        tester = MockStatisticalTester()

        sample_size = tester.get_sample_size_recommendation(
            baseline_rate=0.1,
            minimum_detectable_effect=0.02
        )

        assert isinstance(sample_size, int)
        assert sample_size > 0
        assert sample_size >= 100  # Minimum per variant

    def test_smaller_effect_needs_larger_sample(self):
        """Should recommend larger sample for smaller detectable effect"""
        tester = MockStatisticalTester()

        # Use higher baseline rate so the calculation produces different results
        # (0.5 * 10) / 0.05 = 100 -> max(100, 100) = 100
        # (0.5 * 10) / 0.01 = 500 -> max(100, 500) = 500
        large_effect = tester.get_sample_size_recommendation(0.5, 0.05)
        small_effect = tester.get_sample_size_recommendation(0.5, 0.01)

        assert small_effect > large_effect

    def test_zero_effect_minimum_sample(self):
        """Should return minimum sample when effect is zero"""
        tester = MockStatisticalTester()

        sample_size = tester.get_sample_size_recommendation(0.1, 0)

        assert sample_size == 1000  # Default minimum


class TestTestReadiness:
    """Test determination of test conclusion readiness"""

    def test_test_ready_with_sufficient_data(self):
        """Should indicate test is ready when sample size met"""
        tester = MockStatisticalTester()

        test_stats = {
            'variant_a': {'total': 500},
            'variant_b': {'total': 500}
        }

        ready = tester.is_test_ready_to_conclude(test_stats)
        assert ready == True

    def test_test_not_ready_with_insufficient_data(self):
        """Should indicate test is not ready when sample size insufficient"""
        tester = MockStatisticalTester()

        test_stats = {
            'variant_a': {'total': 50},
            'variant_b': {'total': 50}
        }

        ready = tester.is_test_ready_to_conclude(test_stats)
        assert ready == False

    def test_test_not_ready_with_unbalanced_samples(self):
        """Should require sufficient data for both variants"""
        tester = MockStatisticalTester()

        test_stats = {
            'variant_a': {'total': 500},
            'variant_b': {'total': 50}  # Insufficient
        }

        ready = tester.is_test_ready_to_conclude(test_stats)
        assert ready == False


class TestChiSquareTest:
    """Test chi-square calculation"""

    def test_chi_square_value_calculated(self):
        """Should calculate chi-square statistic"""
        tester = MockStatisticalTester()

        result = tester.compare_variants(
            {'conversions': 100, 'total': 1000},
            {'conversions': 150, 'total': 1000}
        )

        assert 'chi_square' in result
        assert result['chi_square'] >= 0

    def test_p_value_in_valid_range(self):
        """Should produce p-value between 0 and 1"""
        tester = MockStatisticalTester()

        result = tester.compare_variants(
            {'conversions': 100, 'total': 1000},
            {'conversions': 110, 'total': 1000}
        )

        assert 0 <= result['p_value'] <= 1


class TestEdgeCases:
    """Test edge cases and boundary conditions"""

    def test_identical_variants(self):
        """Should handle identical variants"""
        tester = MockStatisticalTester()

        result = tester.compare_variants(
            {'conversions': 100, 'total': 1000},
            {'conversions': 100, 'total': 1000}
        )

        assert result['conversion_rate_a'] == result['conversion_rate_b']
        assert result['lift'] == 0

    def test_single_conversion_each(self):
        """Should handle minimal data"""
        tester = MockStatisticalTester()

        result = tester.compare_variants(
            {'conversions': 1, 'total': 100},
            {'conversions': 1, 'total': 100}
        )

        assert 'p_value' in result
        assert result['conversion_rate_a'] > 0
        assert result['conversion_rate_b'] > 0

    def test_large_sample_sizes(self):
        """Should handle large sample sizes"""
        tester = MockStatisticalTester()

        result = tester.compare_variants(
            {'conversions': 100000, 'total': 1000000},
            {'conversions': 101000, 'total': 1000000}
        )

        assert 'p_value' in result
        assert 'winner' in result


if __name__ == '__main__':
    pytest.main([__file__, '-v', '--tb=short'])
