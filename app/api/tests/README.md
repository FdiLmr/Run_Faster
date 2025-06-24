# Testing Guide for Strava Running Analytics API

This directory contains comprehensive tests for all major functionalities of the Strava Running Analytics application.

## 📋 Test Structure

### Test Categories

1. **Database Operations** (`test_database_operations.py`)
   - Database connection and initialization
   - Data reading and writing operations
   - Database reset functionality
   - Data integrity and validation
   - Performance with large datasets

2. **Strava Integration** (`test_strava_integration.py`)
   - Strava API client functionality
   - Activity fetching and processing
   - Best efforts data processing
   - Rate limiting and error handling
   - Data transformation and storage

3. **Data Processing** (`test_data_processing.py`)
   - Athlete data transformation
   - Activity feature extraction
   - Week-based aggregations
   - Personal best calculations
   - Training block analysis

4. **Race Prediction** (`test_race_prediction.py`)
   - Riegel formula calculations
   - Personal best retrieval
   - Prediction engine functionality
   - Prediction storage and retrieval
   - Model validation and accuracy

5. **API Endpoints** (`test_api_endpoints.py`)
   - Authentication routes
   - Data fetching endpoints
   - Dashboard and visualization routes
   - JSON API responses
   - Error handling and security

## 🚀 Running Tests

### Quick Start

```bash
# Run all tests
python run_tests.py

# Run specific test categories
python run_tests.py --type database
python run_tests.py --type strava
python run_tests.py --type api

# Run specific test file
python run_tests.py --file test_database_operations.py

# Run with coverage report
python run_tests.py --cov-html
```

### Using pytest directly

```bash
# Run all tests
pytest

# Run specific test category
pytest -m database
pytest -m api
pytest -m integration

# Run specific test file
pytest tests/test_database_operations.py

# Run specific test function
pytest tests/test_database_operations.py::TestDatabaseConnection::test_database_connection

# Skip slow tests
pytest -m "not slow"

# Run with coverage
pytest --cov=. --cov-report=html
```

## 🏷️ Test Markers

Tests are organized using pytest markers:

- `@pytest.mark.unit` - Unit tests (fast, isolated)
- `@pytest.mark.integration` - Integration tests (slower, test component interaction)
- `@pytest.mark.api` - API endpoint tests
- `@pytest.mark.database` - Database-related tests
- `@pytest.mark.strava` - Strava API integration tests
- `@pytest.mark.slow` - Slow tests (can be skipped for quick runs)

## 📊 Coverage

The test suite aims for **70%+ code coverage**. Generate coverage reports with:

```bash
# Terminal coverage report
pytest --cov=. --cov-report=term-missing

# HTML coverage report
pytest --cov=. --cov-report=html:htmlcov
```

View the HTML report by opening `htmlcov/index.html` in your browser.

## 🧪 Test Environment Setup

### Prerequisites

```bash
# Install test dependencies
pip install pytest pytest-cov pytest-mock pytest-flask

# For parallel test execution (optional)
pip install pytest-xdist
```

### Environment Variables

The tests use a separate test environment with these variables:
- `FLASK_ENV=testing`
- `CLIENT_ID=test_client_id`
- `CLIENT_SECRET=test_client_secret`
- Database connections use in-memory SQLite for isolation

### Test Database

Tests use an in-memory SQLite database by default, ensuring:
- **Isolation**: Each test starts with a clean database
- **Speed**: In-memory database is faster than disk-based
- **Safety**: No risk of affecting production data

## 🏗️ Test Architecture

### Fixtures

Key fixtures available for all tests:

- `test_app` - Flask application instance for testing
- `test_client` - Flask test client for HTTP requests
- `test_db` - Clean database for each test
- `sample_athlete_data` - Sample athlete data for testing
- `sample_activity_data` - Sample activity data for testing
- `mock_strava_client` - Mocked Strava API client

### Mocking Strategy

Tests use mocking to:
- **Isolate units under test** - Mock external dependencies
- **Control test conditions** - Simulate different scenarios
- **Speed up tests** - Avoid real API calls and file I/O
- **Test error conditions** - Simulate failures and edge cases

Example:
```python
@patch('data.fetchers.strava_api.StravaAPIClient')
def test_fetch_activities(mock_client):
    # Test logic here
    pass
```

## 📝 Writing New Tests

### Test Organization

Follow this structure for new tests:

```python
class TestFeatureName:
    """Test the FeatureName functionality."""
    
    def test_basic_functionality(self):
        """Test basic functionality works correctly."""
        # Arrange
        # Act
        # Assert
        
    def test_error_handling(self):
        """Test error handling works correctly."""
        # Test error conditions
        
    def test_edge_cases(self):
        """Test edge cases and boundary conditions."""
        # Test edge cases
```

### Test Naming Convention

- Test files: `test_<module_name>.py`
- Test classes: `TestClassName`
- Test methods: `test_descriptive_name`

### Best Practices

1. **Arrange-Act-Assert**: Structure tests clearly
2. **One assertion per test**: Keep tests focused
3. **Descriptive names**: Make test purpose clear
4. **Independent tests**: Tests should not depend on each other
5. **Mock external dependencies**: Use mocks for API calls, file I/O
6. **Test edge cases**: Include error conditions and boundary cases

## 🔧 Debugging Tests

### Running Specific Tests

```bash
# Run a single test function
pytest tests/test_database_operations.py::TestDatabaseConnection::test_database_connection -v

# Run tests matching a pattern
pytest -k "test_database" -v

# Stop on first failure
pytest -x
```

### Debugging with Print Statements

```bash
# Show print statements in tests
pytest -s

# Show more verbose output
pytest -vv
```

### Using the Debugger

```python
import pdb; pdb.set_trace()  # Add this line in your test
```

Then run pytest with:
```bash
pytest -s  # -s flag is needed to see debugger
```

## 📈 Continuous Integration

### GitHub Actions

The repository includes GitHub Actions workflow for:
- Running tests on multiple Python versions
- Generating coverage reports
- Running tests on different operating systems

### Pre-commit Hooks

Consider setting up pre-commit hooks to run tests before commits:

```bash
pip install pre-commit
# Add .pre-commit-config.yaml with test hooks
pre-commit install
```

## 🐛 Common Issues and Solutions

### Test Discovery Issues

If pytest can't find your tests:
```bash
# Check test discovery
pytest --collect-only

# Ensure __init__.py files exist in test directories
touch tests/__init__.py
```

### Import Errors

If you get import errors:
```bash
# Check PYTHONPATH
export PYTHONPATH="${PYTHONPATH}:$(pwd)"

# Or use pytest.ini pythonpath setting
```

### Database Issues

If database tests fail:
- Ensure test database is properly isolated
- Check that database schema matches model definitions
- Verify that database cleanup happens between tests

### Slow Tests

If tests are running slowly:
```bash
# Skip slow tests during development
pytest -m "not slow"

# Run tests in parallel
pytest -n 4  # Use 4 workers
```

## 📚 Additional Resources

- [pytest documentation](https://docs.pytest.org/)
- [Flask testing documentation](https://flask.palletsprojects.com/en/2.0.x/testing/)
- [unittest.mock documentation](https://docs.python.org/3/library/unittest.mock.html)
- [Coverage.py documentation](https://coverage.readthedocs.io/)

## 🤝 Contributing

When adding new features:

1. **Write tests first** (TDD approach recommended)
2. **Ensure good coverage** (aim for 80%+ on new code)
3. **Test edge cases** and error conditions
4. **Update documentation** if test setup changes
5. **Run full test suite** before submitting PRs

Remember: **Good tests are documentation** - they show how the code is supposed to work! 