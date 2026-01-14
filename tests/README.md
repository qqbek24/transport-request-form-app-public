# 🧪 Tests Directory

This directory contains all test files for the UIT RO Transport Request application.

## 📂 Structure

```
tests/
├── test_api_submit.py           # API endpoint tests (Docker/live)
├── test_docker_submit.py        # Docker container tests
├── test_integration.py          # End-to-end integration tests
├── test_local_submit_sharepoint.py  # SharePoint integration tests
├── quick_test.py                # Quick smoke tests
├── test_data.json               # Test data fixtures
├── pytest.ini                   # Pytest configuration
├── run_tests.ps1                # Windows test runner
└── run_tests.sh                 # Linux/Mac test runner
```

## 🚀 Running Tests

### Quick Start (from project root)
```powershell
# Run all integration tests
python -m pytest tests/ -v

# Run specific test file
python -m pytest tests/test_api_submit.py -v

# Run with coverage
python -m pytest tests/ --cov=backend --cov-report=html
```

### Using Test Runner (from tests/ directory)
```powershell
# Windows
cd tests
.\run_tests.ps1 all

# Linux/Mac
cd tests
./run_tests.sh all
```

## 📋 Test Types

### 1. API Tests (`test_api_submit.py`)
- Tests REST API endpoints
- Validates request/response formats
- Checks error handling
- **Requires**: Running backend (Docker or local)

### 2. Docker Tests (`test_docker_submit.py`)
- Tests Docker container functionality
- Validates inter-container communication
- **Requires**: Docker containers running

### 3. Integration Tests (`test_integration.py`)
- End-to-end workflow testing
- Tests frontend → backend → SharePoint flow
- **Requires**: Full stack running

### 4. SharePoint Tests (`test_local_submit_sharepoint.py`)
- Tests SharePoint Excel synchronization
- Validates Token Manager
- **Requires**: Valid SharePoint token

### 5. Quick Tests (`quick_test.py`)
- Fast smoke tests
- Basic functionality checks
- Can run without external dependencies

## ⚙️ Configuration

### pytest.ini
```ini
[tool:pytest]
testpaths = . ../backend
python_files = test_*.py *_test.py
```

### Test Data
- `test_data.json` - Sample transport requests for testing

## 🔧 Troubleshooting

**Issue**: `ModuleNotFoundError: No module named 'pytest'`
```powershell
pip install pytest pytest-cov
```

**Issue**: Tests can't find backend modules
```powershell
# Run from project root, not tests/ directory
cd ..
python -m pytest tests/
```

**Issue**: API tests failing with connection error
```powershell
# Ensure backend is running
docker compose up -d backend
# OR
python backend/fastapi_app.py
```

## 📊 Coverage

Current coverage targets:
- **Backend**: 91% (target: 80%+)
- **Integration**: Core workflows 100% covered

Generate coverage report:
```powershell
python -m pytest tests/ --cov=backend --cov-report=html
# Open htmlcov/index.html
```

## ✅ CI/CD

These tests are automatically run by Jenkins pipeline:
- Location: `jenkins/jenkins-pipeline-complete.groovy`
- Runs on: Every commit to `dev` branch
- Reports: Published to Jenkins workspace
