# Test runner script for Transport Request Application (Windows PowerShell)
# Usage: .\run_tests.ps1 [backend|frontend|integration|all]

param(
    [Parameter(Position=0)]
    [ValidateSet("backend", "frontend", "integration", "all", "help")]
    [string]$Command = "all"
)

# Function to print colored output
function Write-Status {
    param([string]$Message)
    Write-Host "[INFO] $Message" -ForegroundColor Blue
}

function Write-Success {
    param([string]$Message)
    Write-Host "[SUCCESS] $Message" -ForegroundColor Green
}

function Write-Warning {
    param([string]$Message)
    Write-Host "[WARNING] $Message" -ForegroundColor Yellow
}

function Write-Error {
    param([string]$Message)
    Write-Host "[ERROR] $Message" -ForegroundColor Red
}

# Function to check if command exists
function Test-Command {
    param([string]$CommandName)
    return Get-Command $CommandName -ErrorAction SilentlyContinue
}

# Function to run backend tests
function Invoke-BackendTests {
    Write-Status "Running Backend Tests..."
    
    # Check if Python is available
    if (-not (Test-Command "python")) {
        Write-Error "Python not found. Please install Python 3.11+"
        return $false
    }
    
    # Check if virtual environment exists
    if (-not (Test-Path ".venv")) {
        Write-Warning "Virtual environment not found. Creating one..."
        python -m venv .venv
    }
    
    # Activate virtual environment
    Write-Status "Activating virtual environment..."
    & ".venv\Scripts\Activate.ps1"
    
    # Install test dependencies
    Write-Status "Installing test dependencies..."
    pip install -r ..\backend\requirements.txt
    pip install -r ..\backend\requirements_test.txt
    
    # Run tests
    Write-Status "Executing backend unit tests..."
    $result = pytest ..\backend\test_fastapi_app.py -v --cov=..\backend --cov-report=term-missing
    
    if ($LASTEXITCODE -eq 0) {
        Write-Success "Backend tests passed!"
        return $true
    } else {
        Write-Error "Backend tests failed!"
        return $false
    }
}

# Function to run frontend tests
function Invoke-FrontendTests {
    Write-Status "Running Frontend Tests..."
    
    # Check if Node.js is available
    if (-not (Test-Command "node")) {
        Write-Error "Node.js not found. Please install Node.js 18+"
        return $false
    }
    
    if (-not (Test-Command "npm")) {
        Write-Error "npm not found. Please install npm"
        return $false
    }
    
    Push-Location ..\frontend
    
    try {
        # Check if package.json exists for testing
        if (-not (Test-Path "package.json")) {
            Write-Warning "Standard package.json not found. Using test configuration..."
            if (Test-Path "package-test.json") {
                Copy-Item "package-test.json" "package.json"
            } else {
                Write-Error "No package.json configuration found!"
                return $false
            }
        }
        
        # Install dependencies
        Write-Status "Installing frontend dependencies..."
        npm install
        
        # Run tests
        Write-Status "Executing frontend tests..."
        npm test -- --watchAll=false --coverage
        
        if ($LASTEXITCODE -eq 0) {
            Write-Success "Frontend tests passed!"
            return $true
        } else {
            Write-Error "Frontend tests failed!"
            return $false
        }
    }
    finally {
        Pop-Location
    }
}

# Function to run integration tests
function Invoke-IntegrationTests {
    Write-Status "Running Integration Tests..."
    
    # Check if backend is running
    Write-Status "Checking if backend is running..."
    try {
        $response = Invoke-WebRequest -Uri "http://localhost:8000/" -UseBasicParsing -TimeoutSec 5
        Write-Success "Backend is running on localhost:8000"
        $backendRunning = $true
    }
    catch {
        Write-Warning "Backend not running. Starting backend..."
        $backendRunning = $false
        
        # Start backend in background
        & ".venv\Scripts\Activate.ps1"
        
        Push-Location ..\backend
        $backendProcess = Start-Process -FilePath "python" -ArgumentList "fastapi_app.py" -PassThru -NoNewWindow
        Pop-Location
        
        # Wait for backend to start
        Write-Status "Waiting for backend to start..."
        $timeout = 30
        $elapsed = 0
        
        do {
            Start-Sleep -Seconds 1
            $elapsed++
            try {
                $response = Invoke-WebRequest -Uri "http://localhost:8000/" -UseBasicParsing -TimeoutSec 1
                Write-Success "Backend started successfully"
                $backendStarted = $true
                break
            }
            catch {
                $backendStarted = $false
            }
        } while ($elapsed -lt $timeout)
        
        if (-not $backendStarted) {
            Write-Error "Backend failed to start within 30 seconds"
            if ($backendProcess) {
                Stop-Process -Id $backendProcess.Id -Force -ErrorAction SilentlyContinue
            }
            return $false
        }
    }
    
    # Run integration tests
    Write-Status "Executing integration tests..."
    pytest test_integration.py -v
    
    $testResult = ($LASTEXITCODE -eq 0)
    
    # Clean up background process if we started it
    if (-not $backendRunning -and $backendProcess) {
        Write-Status "Stopping backend..."
        Stop-Process -Id $backendProcess.Id -Force -ErrorAction SilentlyContinue
    }
    
    if ($testResult) {
        Write-Success "Integration tests passed!"
        return $true
    } else {
        Write-Error "Integration tests failed!"
        return $false
    }
}

# Function to run all tests
function Invoke-AllTests {
    Write-Status "Running All Tests..."
    
    $backendResult = Invoke-BackendTests
    $frontendResult = Invoke-FrontendTests
    $integrationResult = Invoke-IntegrationTests
    
    # Summary
    Write-Host ""
    Write-Status "=== TEST SUMMARY ==="
    
    if ($backendResult) {
        Write-Success "✓ Backend Tests: PASSED"
    } else {
        Write-Error "✗ Backend Tests: FAILED"
    }
    
    if ($frontendResult) {
        Write-Success "✓ Frontend Tests: PASSED"
    } else {
        Write-Error "✗ Frontend Tests: FAILED"
    }
    
    if ($integrationResult) {
        Write-Success "✓ Integration Tests: PASSED"
    } else {
        Write-Error "✗ Integration Tests: FAILED"
    }
    
    $allPassed = $backendResult -and $frontendResult -and $integrationResult
    
    if ($allPassed) {
        Write-Success "All tests passed! 🎉"
        return $true
    } else {
        $failedCount = @($backendResult, $frontendResult, $integrationResult) | Where-Object { -not $_ } | Measure-Object | Select-Object -ExpandProperty Count
        Write-Error "$failedCount test suite(s) failed!"
        return $false
    }
}

# Function to show usage
function Show-Usage {
    Write-Host "Usage: .\run_tests.ps1 [backend|frontend|integration|all]"
    Write-Host ""
    Write-Host "Commands:"
    Write-Host "  backend      Run backend unit tests only"
    Write-Host "  frontend     Run frontend component tests only"
    Write-Host "  integration  Run integration tests only"
    Write-Host "  all          Run all tests (default)"
    Write-Host ""
    Write-Host "Examples:"
    Write-Host "  .\run_tests.ps1 backend"
    Write-Host "  .\run_tests.ps1 frontend"
    Write-Host "  .\run_tests.ps1 all"
}

# Main script logic
try {
    switch ($Command) {
        "backend" {
            $result = Invoke-BackendTests
        }
        "frontend" {
            $result = Invoke-FrontendTests
        }
        "integration" {
            $result = Invoke-IntegrationTests
        }
        "all" {
            $result = Invoke-AllTests
        }
        "help" {
            Show-Usage
            exit 0
        }
        default {
            Write-Error "Unknown command: $Command"
            Show-Usage
            exit 1
        }
    }
    
    if ($result) {
        exit 0
    } else {
        exit 1
    }
}
catch {
    Write-Error "An error occurred: $($_.Exception.Message)"
    exit 1
}