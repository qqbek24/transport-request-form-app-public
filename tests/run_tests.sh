#!/bin/bash
# Test runner script for Transport Request Application
# Usage: ./run_tests.sh [backend|frontend|integration|all]

set -e  # Exit on any error

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

# Function to check if command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Function to run backend tests
run_backend_tests() {
    print_status "Running Backend Tests..."
    
    # Check if Python is available
    if ! command_exists python && ! command_exists python3; then
        print_error "Python not found. Please install Python 3.11+"
        return 1
    fi
    
    # Check if virtual environment exists
    if [ ! -d ".venv" ]; then
        print_warning "Virtual environment not found. Creating one..."
        python -m venv .venv
    fi
    
    # Activate virtual environment
    if [[ "$OSTYPE" == "msys" || "$OSTYPE" == "win32" ]]; then
        source .venv/Scripts/activate
    else
        source .venv/bin/activate
    fi
    
    # Install test dependencies
    print_status "Installing test dependencies..."
    pip install -r backend/requirements.txt
    pip install -r backend/requirements_test.txt
    
    # Run tests
    print_status "Executing backend unit tests..."
    if pytest backend/test_fastapi_app.py -v --cov=backend --cov-report=term-missing; then
        print_success "Backend tests passed!"
        return 0
    else
        print_error "Backend tests failed!"
        return 1
    fi
}

# Function to run frontend tests
run_frontend_tests() {
    print_status "Running Frontend Tests..."
    
    # Check if Node.js is available
    if ! command_exists node; then
        print_error "Node.js not found. Please install Node.js 18+"
        return 1
    fi
    
    if ! command_exists npm; then
        print_error "npm not found. Please install npm"
        return 1
    fi
    
    cd frontend
    
    # Check if package.json exists for testing
    if [ ! -f "package.json" ]; then
        print_warning "Standard package.json not found. Using test configuration..."
        if [ -f "package-test.json" ]; then
            cp package-test.json package.json
        else
            print_error "No package.json configuration found!"
            cd ..
            return 1
        fi
    fi
    
    # Install dependencies
    print_status "Installing frontend dependencies..."
    npm install
    
    # Run tests
    print_status "Executing frontend tests..."
    if npm test -- --watchAll=false --coverage; then
        print_success "Frontend tests passed!"
        cd ..
        return 0
    else
        print_error "Frontend tests failed!"
        cd ..
        return 1
    fi
}

# Function to run integration tests
run_integration_tests() {
    print_status "Running Integration Tests..."
    
    # Check if backend is running
    print_status "Checking if backend is running..."
    if curl -s "http://localhost:8000/" > /dev/null 2>&1; then
        print_success "Backend is running on localhost:8000"
    else
        print_warning "Backend not running. Starting backend..."
        
        # Start backend in background
        if [[ "$OSTYPE" == "msys" || "$OSTYPE" == "win32" ]]; then
            source .venv/Scripts/activate
        else
            source .venv/bin/activate
        fi
        
        cd backend
        python fastapi_app.py &
        BACKEND_PID=$!
        cd ..
        
        # Wait for backend to start
        print_status "Waiting for backend to start..."
        for i in {1..30}; do
            if curl -s "http://localhost:8000/" > /dev/null 2>&1; then
                print_success "Backend started successfully"
                break
            fi
            sleep 1
        done
        
        if [ $i -eq 30 ]; then
            print_error "Backend failed to start within 30 seconds"
            kill $BACKEND_PID 2>/dev/null || true
            return 1
        fi
    fi
    
    # Run integration tests
    print_status "Executing integration tests..."
    if pytest test_integration.py -v; then
        print_success "Integration tests passed!"
        
        # Clean up background process if we started it
        if [ ! -z "$BACKEND_PID" ]; then
            print_status "Stopping backend..."
            kill $BACKEND_PID 2>/dev/null || true
        fi
        
        return 0
    else
        print_error "Integration tests failed!"
        
        # Clean up background process if we started it
        if [ ! -z "$BACKEND_PID" ]; then
            print_status "Stopping backend..."
            kill $BACKEND_PID 2>/dev/null || true
        fi
        
        return 1
    fi
}

# Function to run all tests
run_all_tests() {
    print_status "Running All Tests..."
    
    local backend_result=0
    local frontend_result=0
    local integration_result=0
    
    # Run backend tests
    run_backend_tests || backend_result=$?
    
    # Run frontend tests
    run_frontend_tests || frontend_result=$?
    
    # Run integration tests
    run_integration_tests || integration_result=$?
    
    # Summary
    echo
    print_status "=== TEST SUMMARY ==="
    
    if [ $backend_result -eq 0 ]; then
        print_success "✓ Backend Tests: PASSED"
    else
        print_error "✗ Backend Tests: FAILED"
    fi
    
    if [ $frontend_result -eq 0 ]; then
        print_success "✓ Frontend Tests: PASSED"
    else
        print_error "✗ Frontend Tests: FAILED"
    fi
    
    if [ $integration_result -eq 0 ]; then
        print_success "✓ Integration Tests: PASSED"
    else
        print_error "✗ Integration Tests: FAILED"
    fi
    
    local total_failed=$((backend_result + frontend_result + integration_result))
    
    if [ $total_failed -eq 0 ]; then
        print_success "All tests passed! 🎉"
        return 0
    else
        print_error "$total_failed test suite(s) failed!"
        return 1
    fi
}

# Function to show usage
show_usage() {
    echo "Usage: $0 [backend|frontend|integration|all]"
    echo
    echo "Commands:"
    echo "  backend      Run backend unit tests only"
    echo "  frontend     Run frontend component tests only"
    echo "  integration  Run integration tests only"
    echo "  all          Run all tests (default)"
    echo
    echo "Examples:"
    echo "  $0 backend"
    echo "  $0 frontend"
    echo "  $0 all"
}

# Main script logic
case "${1:-all}" in
    "backend")
        run_backend_tests
        ;;
    "frontend")
        run_frontend_tests
        ;;
    "integration")
        run_integration_tests
        ;;
    "all")
        run_all_tests
        ;;
    "help"|"-h"|"--help")
        show_usage
        exit 0
        ;;
    *)
        print_error "Unknown command: $1"
        show_usage
        exit 1
        ;;
esac

exit $?