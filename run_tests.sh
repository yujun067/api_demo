#!/bin/bash

# Test execution script with recommended order
# Usage: ./run_tests.sh [option]

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Function to run tests with proper order
run_tests_in_order() {
    local test_files=(
        "app/tests/test_domain_logic.py"
        "app/tests/test_repositories.py"
        "app/tests/test_services.py"
        "app/tests/test_tasks.py"
        "app/tests/test_integration.py"
        "app/tests/test_api.py"
    )
    
    local total_tests=0
    local passed_tests=0
    local failed_tests=0
    
    print_status "Starting tests in recommended order..."
    echo
    
    for test_file in "${test_files[@]}"; do
        if [ -f "$test_file" ]; then
            print_status "Running: $test_file"
            
            # Run the test file
            if python -m pytest "$test_file" -v --tb=short; then
                print_success "✓ $test_file passed"
                ((passed_tests++))
            else
                print_error "✗ $test_file failed"
                ((failed_tests++))
            fi
            echo
        else
            print_warning "Test file not found: $test_file"
        fi
        ((total_tests++))
    done
    
    echo "=========================================="
    print_status "Test Summary:"
    echo "  Total test files: $total_tests"
    echo "  Passed: $passed_tests"
    echo "  Failed: $failed_tests"
    echo "=========================================="
    
    if [ $failed_tests -eq 0 ]; then
        print_success "All tests passed! 🎉"
        exit 0
    else
        print_error "Some tests failed! ❌"
        exit 1
    fi
}

# Function to run specific test category
run_category() {
    local category=$1
    case $category in
        "unit")
            print_status "Running unit tests (domain logic + repositories + services)..."
            python -m pytest app/tests/test_domain_logic.py app/tests/test_repositories.py app/tests/test_services.py -v
            ;;
        "tasks")
            print_status "Running task tests..."
            python -m pytest app/tests/test_tasks.py -v
            ;;
        "integration")
            print_status "Running integration tests..."
            python -m pytest app/tests/test_integration.py -v
            ;;
        "api")
            print_status "Running API tests..."
            python -m pytest app/tests/test_api.py -v
            ;;
        "fast")
            print_status "Running fast tests (unit tests only)..."
            python -m pytest app/tests/test_domain_logic.py app/tests/test_repositories.py app/tests/test_services.py -v --tb=short
            ;;
        *)
            print_error "Unknown category: $category"
            echo "Available categories: unit, tasks, integration, api, fast"
            exit 1
            ;;
    esac
}

# Function to run all tests
run_all() {
    print_status "Running all tests..."
    python -m pytest app/tests/ -v
}

# Function to run tests with coverage
run_with_coverage() {
    print_status "Running tests with coverage report..."
    python -m pytest app/tests/ -v --cov=app --cov-report=html --cov-report=term-missing
    print_success "Coverage report generated in htmlcov/"
}

# Function to show help
show_help() {
    echo "Test Execution Script"
    echo "===================="
    echo
    echo "Usage: $0 [option]"
    echo
    echo "Options:"
    echo "  (no args)    Run tests in recommended order"
    echo "  all          Run all tests at once"
    echo "  unit         Run unit tests only (domain + repos + services)"
    echo "  tasks        Run task tests only"
    echo "  integration  Run integration tests only"
    echo "  api          Run API tests only"
    echo "  fast         Run fast tests (unit tests with short output)"
    echo "  coverage     Run all tests with coverage report"
    echo "  help         Show this help message"
    echo
    echo "Recommended workflow:"
    echo "  1. Start with: $0 fast"
    echo "  2. Then run: $0"
    echo "  3. For coverage: $0 coverage"
}

# Main script logic
case "${1:-}" in
    "all")
        run_all
        ;;
    "unit"|"tasks"|"integration"|"api"|"fast")
        run_category "$1"
        ;;
    "coverage")
        run_with_coverage
        ;;
    "help"|"-h"|"--help")
        show_help
        ;;
    "")
        run_tests_in_order
        ;;
    *)
        print_error "Unknown option: $1"
        echo
        show_help
        exit 1
        ;;
esac
