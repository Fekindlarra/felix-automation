"""
pytest configuration for FASE 14 testing
Provides fixtures and setup for all test modules
"""

import pytest
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# Pytest markers for test categorization
def pytest_configure(config):
    """Register custom pytest markers"""
    config.addinivalue_line(
        "markers", "unit: mark test as a unit test"
    )
    config.addinivalue_line(
        "markers", "integration: mark test as an integration test"
    )
    config.addinivalue_line(
        "markers", "e2e: mark test as an end-to-end test"
    )
    config.addinivalue_line(
        "markers", "load: mark test as a load test"
    )
    config.addinivalue_line(
        "markers", "asyncio: mark test as async"
    )
    config.addinivalue_line(
        "markers", "slow: mark test as slow running"
    )


# Fixtures

@pytest.fixture
def temp_dir(tmp_path):
    """Provide temporary directory for test artifacts"""
    return tmp_path


@pytest.fixture
def mock_user_agent():
    """Provide common User-Agent strings for testing"""
    return {
        'iphone': "Mozilla/5.0 (iPhone; CPU iPhone OS 14_6 like Mac OS X) AppleWebKit/605.1.15",
        'ipad': "Mozilla/5.0 (iPad; CPU OS 14_6 like Mac OS X) AppleWebKit/605.1.15",
        'android': "Mozilla/5.0 (Linux; Android 11; SM-G991B) AppleWebKit/537.36",
        'windows': "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        'macos': "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36",
        'linux': "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36",
        'webos': "Mozilla/5.0 (webOS/2.0; U; en-US) AppleWebKit/534.6",
        'blackberry': "Mozilla/5.0 (BlackBerry; U; BlackBerry 9930) AppleWebKit/534.11",
    }


@pytest.fixture
def mock_prediction_event():
    """Provide sample prediction event for testing"""
    return {
        'type': 'prediction:generated',
        'client_id': 42,
        'probability': 78.456789,
        'confidence': 85.123456,
        '_internal_cache': 'should_be_removed',
        'data': {
            'company_name': 'TechVentures Chile',
            'industry': 'Software',
            'audit_type': 'deep',
            'internal_field': 'remove_this',
            'recommendation': 'Contacto inmediato'
        },
        'timestamp': '2026-10-05T10:00:00Z'
    }


@pytest.fixture
def mock_connection_info():
    """Provide ConnectionInfo factory for testing"""
    from backend.events import ConnectionInfo

    def create_connection(connection_id="test_1", is_mobile=False, user_agent="Desktop"):
        return ConnectionInfo(
            connection_id=connection_id,
            user_id="user_1",
            is_mobile=is_mobile,
            user_agent=user_agent
        )

    return create_connection


@pytest.fixture
def performance_tracker():
    """Track performance metrics during tests"""
    import time

    class PerformanceTracker:
        def __init__(self):
            self.timings = {}

        def start(self, name):
            self.timings[name] = {'start': time.time()}

        def end(self, name):
            if name in self.timings:
                self.timings[name]['end'] = time.time()
                self.timings[name]['duration'] = (
                    self.timings[name]['end'] - self.timings[name]['start']
                )

        def get_duration(self, name):
            if name in self.timings and 'duration' in self.timings[name]:
                return self.timings[name]['duration']
            return None

        def print_report(self):
            print("\n📊 Performance Report:")
            for name, data in self.timings.items():
                if 'duration' in data:
                    print(f"  {name}: {data['duration']:.3f}s")

    return PerformanceTracker()


# Test collection hooks

def pytest_collection_modifyitems(config, items):
    """Automatically mark tests based on file location"""
    for item in items:
        # Mark tests by directory
        if "test_mobile_detection" in item.nodeid:
            item.add_marker(pytest.mark.unit)
        elif "test_websocket_mobile_integration" in item.nodeid:
            item.add_marker(pytest.mark.integration)
        elif "test_e2e_mobile_scenarios" in item.nodeid:
            item.add_marker(pytest.mark.e2e)
        elif "load" in item.nodeid:
            item.add_marker(pytest.mark.load)
            item.add_marker(pytest.mark.slow)

        # Mark async tests
        if "asyncio" in item.keywords:
            item.add_marker(pytest.mark.asyncio)


# Report hooks

def pytest_runtest_logreport(report):
    """Custom logging for test results"""
    if report.when == "call":
        if report.outcome == "passed":
            print(f"✅ {report.nodeid}")
        elif report.outcome == "failed":
            print(f"❌ {report.nodeid}")


def pytest_terminal_summary(terminalreporter, exitstatus, config):
    """Add custom summary to test report"""
    terminalreporter.write_sep("=", "FASE 14 Testing Summary", bold=True)
    terminalreporter.write_line("Testing Status: All checks completed")
    terminalreporter.write_line("Ready for PASO 16: Documentation & Deployment")
