"""
FASE 14 - Unit Tests for A/B Testing Routes
Testing A/B test API endpoints
"""

import pytest
from unittest.mock import Mock, patch
from datetime import datetime, timedelta


class MockABTestDatabase:
    """Mock A/B test database operations"""

    def __init__(self):
        self.tests = {}
        self.results = {}
        self.test_counter = 0

    def create_test(self, test_data):
        """Create new A/B test"""
        self.test_counter += 1
        test_id = self.test_counter

        test = {
            'id': test_id,
            'name': test_data.get('name'),
            'email_type': test_data.get('email_type'),
            'variant_a': test_data.get('variant_a'),
            'variant_b': test_data.get('variant_b'),
            'active': True,
            'created_at': datetime.now().isoformat(),
            'start_date': test_data.get('start_date', datetime.now().isoformat()),
            'end_date': test_data.get('end_date', (datetime.now() + timedelta(days=14)).isoformat()),
            'status': 'running'
        }

        self.tests[test_id] = test
        return test

    def get_test(self, test_id):
        """Retrieve test by ID"""
        return self.tests.get(test_id)

    def list_tests(self, active_only=False):
        """List all tests"""
        if active_only:
            return [t for t in self.tests.values() if t['active']]
        return list(self.tests.values())

    def update_test_status(self, test_id, status):
        """Update test status"""
        if test_id in self.tests:
            self.tests[test_id]['status'] = status
            if status == 'completed':
                self.tests[test_id]['active'] = False
            return self.tests[test_id]
        return None

    def pause_test(self, test_id):
        """Pause active test"""
        if test_id in self.tests:
            self.tests[test_id]['active'] = False
            self.tests[test_id]['status'] = 'paused'
            return {'paused': True}
        return None

    def resume_test(self, test_id):
        """Resume paused test"""
        if test_id in self.tests:
            self.tests[test_id]['active'] = True
            self.tests[test_id]['status'] = 'running'
            return {'resumed': True}
        return None

    def record_result(self, test_id, client_id, variant, sent=True, opened=False, clicked=False):
        """Record A/B test result"""
        if test_id not in self.results:
            self.results[test_id] = []

        result = {
            'test_id': test_id,
            'client_id': client_id,
            'variant': variant,
            'sent': sent,
            'opened': opened,
            'clicked': clicked,
            'timestamp': datetime.now().isoformat()
        }

        self.results[test_id].append(result)
        return result

    def get_test_results(self, test_id):
        """Get all results for a test"""
        return self.results.get(test_id, [])

    def calculate_test_stats(self, test_id):
        """Calculate statistics for test"""
        results = self.results.get(test_id, [])

        if not results:
            return {
                'test_id': test_id,
                'variant_a': {'sent': 0, 'opens': 0, 'clicks': 0, 'conversions': 0},
                'variant_b': {'sent': 0, 'opens': 0, 'clicks': 0, 'conversions': 0}
            }

        variant_a_results = [r for r in results if r['variant'] == 'A']
        variant_b_results = [r for r in results if r['variant'] == 'B']

        stats = {
            'test_id': test_id,
            'variant_a': {
                'sent': len(variant_a_results),
                'opens': sum(1 for r in variant_a_results if r['opened']),
                'clicks': sum(1 for r in variant_a_results if r['clicked']),
                'conversions': sum(1 for r in variant_a_results if r['clicked'])  # For demo
            },
            'variant_b': {
                'sent': len(variant_b_results),
                'opens': sum(1 for r in variant_b_results if r['opened']),
                'clicks': sum(1 for r in variant_b_results if r['clicked']),
                'conversions': sum(1 for r in variant_b_results if r['clicked'])
            }
        }

        return stats


class MockABTestingRoutes:
    """Mock A/B testing API routes"""

    def __init__(self, database=None):
        self.database = database or MockABTestDatabase()

    def post_create_test(self, request_data):
        """POST /api/tests - Create new A/B test"""
        required_fields = ['name', 'email_type', 'variant_a', 'variant_b']

        # Validate required fields
        for field in required_fields:
            if field not in request_data:
                return {
                    'error': f'Missing required field: {field}',
                    'status': 400
                }

        # Create test
        test = self.database.create_test(request_data)

        return {
            'test': test,
            'status': 201,
            'message': 'Test created successfully'
        }

    def get_list_tests(self, active_only=False):
        """GET /api/tests - List A/B tests"""
        tests = self.database.list_tests(active_only=active_only)

        return {
            'tests': tests,
            'count': len(tests),
            'status': 200
        }

    def get_test_details(self, test_id):
        """GET /api/tests/{id} - Get test details"""
        test = self.database.get_test(test_id)

        if not test:
            return {
                'error': f'Test {test_id} not found',
                'status': 404
            }

        return {
            'test': test,
            'status': 200
        }

    def get_test_results(self, test_id):
        """GET /api/tests/{id}/results - Get test results"""
        test = self.database.get_test(test_id)

        if not test:
            return {
                'error': f'Test {test_id} not found',
                'status': 404
            }

        stats = self.database.calculate_test_stats(test_id)
        results = self.database.get_test_results(test_id)

        return {
            'test_id': test_id,
            'stats': stats,
            'results_count': len(results),
            'status': 200
        }

    def post_record_result(self, test_id, result_data):
        """POST /api/tests/{id}/results - Record test result"""
        test = self.database.get_test(test_id)

        if not test:
            return {
                'error': f'Test {test_id} not found',
                'status': 404
            }

        required_fields = ['client_id', 'variant']

        for field in required_fields:
            if field not in result_data:
                return {
                    'error': f'Missing required field: {field}',
                    'status': 400
                }

        # Record result
        result = self.database.record_result(
            test_id,
            result_data.get('client_id'),
            result_data.get('variant'),
            sent=result_data.get('sent', True),
            opened=result_data.get('opened', False),
            clicked=result_data.get('clicked', False)
        )

        return {
            'result': result,
            'status': 201,
            'message': 'Result recorded'
        }

    def post_mark_winner(self, test_id, winner_data):
        """POST /api/tests/{id}/winner - Mark test winner"""
        test = self.database.get_test(test_id)

        if not test:
            return {
                'error': f'Test {test_id} not found',
                'status': 404
            }

        if 'winner' not in winner_data:
            return {
                'error': 'Missing winner field',
                'status': 400
            }

        winner = winner_data.get('winner')

        if winner not in ['A', 'B']:
            return {
                'error': 'Winner must be A or B',
                'status': 400
            }

        # Update test status
        self.database.update_test_status(test_id, 'completed')

        return {
            'test_id': test_id,
            'winner': winner,
            'status': 200,
            'message': f'Variant {winner} marked as winner'
        }

    def post_pause_test(self, test_id):
        """POST /api/tests/{id}/pause - Pause test"""
        test = self.database.get_test(test_id)

        if not test:
            return {
                'error': f'Test {test_id} not found',
                'status': 404
            }

        self.database.pause_test(test_id)

        return {
            'test_id': test_id,
            'status': 200,
            'message': 'Test paused'
        }

    def post_resume_test(self, test_id):
        """POST /api/tests/{id}/resume - Resume test"""
        test = self.database.get_test(test_id)

        if not test:
            return {
                'error': f'Test {test_id} not found',
                'status': 404
            }

        self.database.resume_test(test_id)

        return {
            'test_id': test_id,
            'status': 200,
            'message': 'Test resumed'
        }


# ============================================================================
# TESTS
# ============================================================================

class TestCreateTest:
    """Test A/B test creation"""

    def test_create_test_successful(self):
        """Should create new A/B test with valid data"""
        routes = MockABTestingRoutes()

        result = routes.post_create_test({
            'name': 'Email Subject Test',
            'email_type': 'followup',
            'variant_a': 'Subject A: Exclusive Offer',
            'variant_b': 'Subject B: Limited Time'
        })

        assert result['status'] == 201
        assert result['test']['name'] == 'Email Subject Test'
        assert result['test']['active'] == True

    def test_create_test_missing_required_field(self):
        """Should reject test without required fields"""
        routes = MockABTestingRoutes()

        result = routes.post_create_test({
            'name': 'Incomplete Test',
            'email_type': 'followup'
            # Missing variant_a and variant_b
        })

        assert result['status'] == 400
        assert 'error' in result

    def test_create_test_returns_test_id(self):
        """Should return test ID for created test"""
        routes = MockABTestingRoutes()

        result = routes.post_create_test({
            'name': 'Test 1',
            'email_type': 'followup',
            'variant_a': 'A',
            'variant_b': 'B'
        })

        assert result['test']['id'] > 0

    def test_create_multiple_tests_unique_ids(self):
        """Should assign unique IDs to each test"""
        routes = MockABTestingRoutes()

        result1 = routes.post_create_test({
            'name': 'Test 1',
            'email_type': 'followup',
            'variant_a': 'A',
            'variant_b': 'B'
        })

        result2 = routes.post_create_test({
            'name': 'Test 2',
            'email_type': 'promotion',
            'variant_a': 'C',
            'variant_b': 'D'
        })

        assert result1['test']['id'] != result2['test']['id']


class TestListTests:
    """Test listing A/B tests"""

    def test_list_empty_tests(self):
        """Should return empty list when no tests"""
        routes = MockABTestingRoutes()

        result = routes.get_list_tests()

        assert result['status'] == 200
        assert result['count'] == 0
        assert result['tests'] == []

    def test_list_all_tests(self):
        """Should list all tests"""
        routes = MockABTestingRoutes()

        routes.post_create_test({
            'name': 'Test 1',
            'email_type': 'followup',
            'variant_a': 'A',
            'variant_b': 'B'
        })

        routes.post_create_test({
            'name': 'Test 2',
            'email_type': 'promotion',
            'variant_a': 'C',
            'variant_b': 'D'
        })

        result = routes.get_list_tests()

        assert result['count'] == 2
        assert len(result['tests']) == 2

    def test_list_active_tests_only(self):
        """Should filter active tests"""
        routes = MockABTestingRoutes()

        test1 = routes.post_create_test({
            'name': 'Test 1',
            'email_type': 'followup',
            'variant_a': 'A',
            'variant_b': 'B'
        })

        test2 = routes.post_create_test({
            'name': 'Test 2',
            'email_type': 'promotion',
            'variant_a': 'C',
            'variant_b': 'D'
        })

        # Pause one test
        routes.post_pause_test(test2['test']['id'])

        result = routes.get_list_tests(active_only=True)

        assert result['count'] == 1
        assert result['tests'][0]['name'] == 'Test 1'


class TestGetTestDetails:
    """Test retrieving test details"""

    def test_get_test_details_successful(self):
        """Should retrieve test details by ID"""
        routes = MockABTestingRoutes()

        created = routes.post_create_test({
            'name': 'Test Details',
            'email_type': 'followup',
            'variant_a': 'A',
            'variant_b': 'B'
        })

        test_id = created['test']['id']
        result = routes.get_test_details(test_id)

        assert result['status'] == 200
        assert result['test']['name'] == 'Test Details'

    def test_get_nonexistent_test(self):
        """Should return 404 for nonexistent test"""
        routes = MockABTestingRoutes()

        result = routes.get_test_details(999)

        assert result['status'] == 404
        assert 'error' in result


class TestRecordResults:
    """Test recording test results"""

    def test_record_result_successful(self):
        """Should record test result"""
        routes = MockABTestingRoutes()

        created = routes.post_create_test({
            'name': 'Test',
            'email_type': 'followup',
            'variant_a': 'A',
            'variant_b': 'B'
        })

        test_id = created['test']['id']

        result = routes.post_record_result(test_id, {
            'client_id': 123,
            'variant': 'A',
            'opened': True,
            'clicked': False
        })

        assert result['status'] == 201
        assert result['result']['variant'] == 'A'

    def test_record_result_missing_variant(self):
        """Should require variant field"""
        routes = MockABTestingRoutes()

        created = routes.post_create_test({
            'name': 'Test',
            'email_type': 'followup',
            'variant_a': 'A',
            'variant_b': 'B'
        })

        test_id = created['test']['id']

        result = routes.post_record_result(test_id, {
            'client_id': 123
            # Missing variant
        })

        assert result['status'] == 400

    def test_record_multiple_results(self):
        """Should record multiple results for same test"""
        routes = MockABTestingRoutes()

        created = routes.post_create_test({
            'name': 'Test',
            'email_type': 'followup',
            'variant_a': 'A',
            'variant_b': 'B'
        })

        test_id = created['test']['id']

        for i in range(5):
            variant = 'A' if i % 2 == 0 else 'B'
            routes.post_record_result(test_id, {
                'client_id': 100 + i,
                'variant': variant,
                'opened': i % 2 == 0
            })

        results = routes.get_test_results(test_id)
        assert results['results_count'] >= 5


class TestGetResults:
    """Test retrieving test results"""

    def test_get_results_successful(self):
        """Should retrieve test results"""
        routes = MockABTestingRoutes()

        created = routes.post_create_test({
            'name': 'Test',
            'email_type': 'followup',
            'variant_a': 'A',
            'variant_b': 'B'
        })

        test_id = created['test']['id']

        # Record some results
        routes.post_record_result(test_id, {
            'client_id': 1,
            'variant': 'A',
            'opened': True
        })

        result = routes.get_test_results(test_id)

        assert result['status'] == 200
        assert 'stats' in result
        assert result['stats']['variant_a']['sent'] == 1

    def test_get_results_calculates_stats(self):
        """Should calculate test statistics"""
        routes = MockABTestingRoutes()

        created = routes.post_create_test({
            'name': 'Test',
            'email_type': 'followup',
            'variant_a': 'A',
            'variant_b': 'B'
        })

        test_id = created['test']['id']

        # Variant A: 100 sent, 50 opened
        for i in range(100):
            routes.post_record_result(test_id, {
                'client_id': i,
                'variant': 'A',
                'opened': i < 50
            })

        # Variant B: 100 sent, 60 opened
        for i in range(100, 200):
            routes.post_record_result(test_id, {
                'client_id': i,
                'variant': 'B',
                'opened': i < 160
            })

        result = routes.get_test_results(test_id)

        assert result['stats']['variant_a']['sent'] == 100
        assert result['stats']['variant_a']['opens'] == 50
        assert result['stats']['variant_b']['sent'] == 100
        assert result['stats']['variant_b']['opens'] == 60


class TestMarkWinner:
    """Test marking test winner"""

    def test_mark_winner_successful(self):
        """Should mark test winner"""
        routes = MockABTestingRoutes()

        created = routes.post_create_test({
            'name': 'Test',
            'email_type': 'followup',
            'variant_a': 'A',
            'variant_b': 'B'
        })

        test_id = created['test']['id']

        result = routes.post_mark_winner(test_id, {'winner': 'A'})

        assert result['status'] == 200
        assert result['winner'] == 'A'

    def test_mark_winner_invalid_variant(self):
        """Should reject invalid winner variant"""
        routes = MockABTestingRoutes()

        created = routes.post_create_test({
            'name': 'Test',
            'email_type': 'followup',
            'variant_a': 'A',
            'variant_b': 'B'
        })

        test_id = created['test']['id']

        result = routes.post_mark_winner(test_id, {'winner': 'C'})

        assert result['status'] == 400
        assert 'error' in result

    def test_mark_winner_completes_test(self):
        """Should mark test as completed when winner declared"""
        routes = MockABTestingRoutes()

        created = routes.post_create_test({
            'name': 'Test',
            'email_type': 'followup',
            'variant_a': 'A',
            'variant_b': 'B'
        })

        test_id = created['test']['id']

        routes.post_mark_winner(test_id, {'winner': 'B'})

        test = routes.get_test_details(test_id)
        assert test['test']['status'] == 'completed'
        assert test['test']['active'] == False


class TestPauseResume:
    """Test pausing and resuming tests"""

    def test_pause_test_successful(self):
        """Should pause active test"""
        routes = MockABTestingRoutes()

        created = routes.post_create_test({
            'name': 'Test',
            'email_type': 'followup',
            'variant_a': 'A',
            'variant_b': 'B'
        })

        test_id = created['test']['id']

        result = routes.post_pause_test(test_id)

        assert result['status'] == 200

        test = routes.get_test_details(test_id)
        assert test['test']['active'] == False

    def test_resume_test_successful(self):
        """Should resume paused test"""
        routes = MockABTestingRoutes()

        created = routes.post_create_test({
            'name': 'Test',
            'email_type': 'followup',
            'variant_a': 'A',
            'variant_b': 'B'
        })

        test_id = created['test']['id']

        routes.post_pause_test(test_id)
        result = routes.post_resume_test(test_id)

        assert result['status'] == 200

        test = routes.get_test_details(test_id)
        assert test['test']['active'] == True


class TestEdgeCases:
    """Test edge cases and boundary conditions"""

    def test_empty_variant_names_handled(self):
        """Should handle empty variant names"""
        routes = MockABTestingRoutes()

        result = routes.post_create_test({
            'name': 'Test',
            'email_type': 'followup',
            'variant_a': '',
            'variant_b': ''
        })

        assert result['status'] == 201

    def test_very_long_test_name(self):
        """Should handle very long test names"""
        routes = MockABTestingRoutes()

        long_name = 'A' * 500

        result = routes.post_create_test({
            'name': long_name,
            'email_type': 'followup',
            'variant_a': 'A',
            'variant_b': 'B'
        })

        assert result['status'] == 201

    def test_special_characters_in_variants(self):
        """Should handle special characters"""
        routes = MockABTestingRoutes()

        result = routes.post_create_test({
            'name': 'Test',
            'email_type': 'followup',
            'variant_a': 'Subject with !@#$%^&*()',
            'variant_b': 'Subject with <html> tags'
        })

        assert result['status'] == 201


if __name__ == '__main__':
    pytest.main([__file__, '-v', '--tb=short'])
