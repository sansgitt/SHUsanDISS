#!/bin/bash

# Install test dependencies
pip install -r requirements-test.txt

# Run unit tests
echo "Running unit tests..."
python -m unittest test_unit.py

# Run integration tests
echo "Running integration tests..."
python -m unittest test_integration.py

# Run game feature tests
echo "Running game feature tests..."
python -m unittest test_game.py

# Run pytest tests
echo "Running pytest tests..."
pytest test_pytest.py -v

# Run tests with coverage
echo "Running tests with coverage..."
coverage run -m pytest
coverage report
coverage html

# Run E2E tests (only if specified)
if [ "$1" == "--e2e" ]; then
    echo "Running E2E tests..."
    python -m unittest test_e2e.py
fi

echo "All tests completed!"
