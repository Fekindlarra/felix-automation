#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test consolidation script for BLOQUE 4
Moves all test files to standardized pytest directory structure
BLOQUE 4: Consolidate Tests to Pytest Framework

Directory structure after consolidation:
tests/
├── unit/                           (existing unit tests)
├── integration/                    (existing integration tests)
├── legacy_fase/                    (NEW: legacy FASE test files)
├── conftest.py                     (pytest configuration - will create if needed)
└── pytest.ini                      (pytest config - will create if needed)
"""

import os
import shutil
import sys
from pathlib import Path
import re

def main():
    print("\n" + "="*70)
    print("TEST CONSOLIDATION SCRIPT - BLOQUE 4")
    print("Moving all tests to pytest framework")
    print("="*70)

    project_root = Path("/home/claude/felix-automation")
    tests_dir = project_root / "tests"
    legacy_fase_dir = tests_dir / "legacy_fase"

    # Create legacy_fase directory if it doesn't exist
    legacy_fase_dir.mkdir(parents=True, exist_ok=True)
    print(f"\n✅ Created directory: {legacy_fase_dir}")

    # 1. Move root-level test_fase*.py files
    print("\n" + "-"*70)
    print("STEP 1: Moving root-level test files")
    print("-"*70)

    root_test_files = list(project_root.glob("test_fase*.py")) + \
                      list(project_root.glob("test_analytics*.py")) + \
                      list(project_root.glob("test_end_to_end*.py")) + \
                      list(project_root.glob("test_websocket*.py")) + \
                      list(project_root.glob("test_dashboard*.py"))

    moved_count = 0
    for test_file in root_test_files:
        dest = legacy_fase_dir / test_file.name
        try:
            shutil.move(str(test_file), str(dest))
            print(f"  ✓ Moved: {test_file.name} → legacy_fase/")
            moved_count += 1
        except Exception as e:
            print(f"  ✗ Error moving {test_file.name}: {e}")

    print(f"\n✅ Moved {moved_count} root-level test files")

    # 2. Move backend/api/tests files to tests/backend/api
    print("\n" + "-"*70)
    print("STEP 2: Reorganizing backend/api/tests")
    print("-"*70)

    backend_api_tests = project_root / "backend" / "api" / "tests"
    if backend_api_tests.exists():
        backend_tests_dir = tests_dir / "backend" / "api"
        backend_tests_dir.mkdir(parents=True, exist_ok=True)

        for test_file in backend_api_tests.glob("test_*.py"):
            dest = backend_tests_dir / test_file.name
            try:
                shutil.move(str(test_file), str(dest))
                print(f"  ✓ Moved: {test_file.name} → tests/backend/api/")
                moved_count += 1
            except Exception as e:
                print(f"  ✗ Error moving {test_file.name}: {e}")

        # Remove empty backend/api/tests directory
        try:
            backend_api_tests.rmdir()
            print(f"  ✓ Removed empty directory: backend/api/tests")
        except:
            pass

        print(f"\n✅ Reorganized backend/api/tests")

    # 3. Move backend/tests files to tests/backend
    print("\n" + "-"*70)
    print("STEP 3: Reorganizing backend/tests")
    print("-"*70)

    backend_tests = project_root / "backend" / "tests"
    if backend_tests.exists():
        backend_root_dir = tests_dir / "backend"
        backend_root_dir.mkdir(parents=True, exist_ok=True)

        for test_file in backend_tests.glob("test_*.py"):
            dest = backend_root_dir / test_file.name
            try:
                shutil.move(str(test_file), str(dest))
                print(f"  ✓ Moved: {test_file.name} → tests/backend/")
                moved_count += 1
            except Exception as e:
                print(f"  ✗ Error moving {test_file.name}: {e}")

        # Remove empty backend/tests directory
        try:
            backend_tests.rmdir()
            print(f"  ✓ Removed empty directory: backend/tests")
        except:
            pass

        print(f"\n✅ Reorganized backend/tests")

    # 4. Move scripts/test_*.py files
    print("\n" + "-"*70)
    print("STEP 4: Moving test files from scripts")
    print("-"*70)

    scripts_dir = project_root / "scripts"
    if scripts_dir.exists():
        scripts_test_files = list(scripts_dir.glob("test_*.py"))

        for test_file in scripts_test_files:
            dest = tests_dir / f"{test_file.stem}_script.py"
            try:
                shutil.move(str(test_file), str(dest))
                print(f"  ✓ Moved: {test_file.name} → tests/")
                moved_count += 1
            except Exception as e:
                print(f"  ✗ Error moving {test_file.name}: {e}")

        print(f"\n✅ Moved test files from scripts/")

    # 5. Create/update conftest.py if needed
    print("\n" + "-"*70)
    print("STEP 5: Creating conftest.py")
    print("-"*70)

    conftest_path = tests_dir / "conftest.py"
    if not conftest_path.exists():
        conftest_content = '''"""
Pytest configuration and shared fixtures for FASE 15 tests
"""
import sys
import os
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

import pytest

@pytest.fixture
def project_root_fixture():
    """Provide project root path"""
    return Path(__file__).parent.parent

@pytest.fixture
def test_db(tmp_path):
    """Provide temporary test database"""
    db_path = tmp_path / "test.db"
    return str(db_path)

@pytest.fixture
def mock_settings():
    """Provide mock settings for testing"""
    return {
        "DATABASE_URL": "sqlite:///./test.db",
        "SECRET_KEY": "test-secret-key",
        "DEBUG": True,
    }
'''
        with open(conftest_path, 'w') as f:
            f.write(conftest_content)
        print(f"  ✓ Created: {conftest_path}")
    else:
        print(f"  ✓ conftest.py already exists")

    # 6. Create/update pytest.ini
    print("\n" + "-"*70)
    print("STEP 6: Creating pytest.ini")
    print("-"*70)

    pytest_ini = project_root / "pytest.ini"
    if not pytest_ini.exists():
        pytest_content = '''[pytest]
# Pytest configuration for FASE 15
minversion = 7.0
testpaths = tests
python_files = test_*.py
python_classes = Test*
python_functions = test_*
addopts =
    -v
    --strict-markers
    --tb=short
    --disable-warnings
    -p no:cacheprovider
markers =
    unit: Unit tests
    integration: Integration tests
    slow: Slow running tests
    fase_legacy: Legacy FASE phase tests
    phase3: Phase 3 specific tests
'''
        with open(pytest_ini, 'w') as f:
            f.write(pytest_content)
        print(f"  ✓ Created: {pytest_ini}")
    else:
        print(f"  ✓ pytest.ini already exists")

    # Summary
    print("\n" + "="*70)
    print("CONSOLIDATION SUMMARY")
    print("="*70)

    print(f"\n✅ Total files moved: {moved_count}")
    print(f"✅ New test directory structure:")
    print(f"""
    tests/
    ├── unit/                      (existing unit tests)
    ├── integration/               (existing integration tests)
    ├── backend/
    │   ├── api/                   (from backend/api/tests/)
    │   └── *.py                   (from backend/tests/)
    ├── legacy_fase/               (NEW: from root level)
    ├── conftest.py                (pytest fixtures)
    └── pytest.ini                 (pytest config)
    """)

    print("\n🎯 Next step: Run pytest to verify all tests pass")
    print("   Command: pytest -v tests/")
    print("\n" + "="*70)

    return 0

if __name__ == "__main__":
    sys.exit(main())
