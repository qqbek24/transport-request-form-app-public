#!/usr/bin/env powershell

Write-Host "🔧 Testing docs endpoints locally..." -ForegroundColor Yellow

$endpoints = @(
    "http://localhost:8010/docs",
    "http://localhost:8010/redoc", 
    "http://localhost:8010/openapi.json",
    "http://localhost:8010/api/debug/docs",
    "https://your-url-adress/docs",
    "https://your-url-adress/redoc",
    "https://your-url-adress/openapi.json",
    "https://your-url-adress/api/debug/docs"
)

foreach ($endpoint in $endpoints) {
    Write-Host "`n📍 Testing: $endpoint" -ForegroundColor Cyan
    try {
        if ($endpoint.StartsWith("https")) {
            $response = Invoke-WebRequest -Uri $endpoint -Method GET -TimeoutSec 5 -SkipCertificateCheck -ErrorAction Stop
        } else {
            $response = Invoke-WebRequest -Uri $endpoint -Method GET -TimeoutSec 5 -ErrorAction Stop
        }
        
        if ($response.StatusCode -eq 200) {
            Write-Host "✅ SUCCESS - Status: $($response.StatusCode)" -ForegroundColor Green
            if ($endpoint.Contains("debug")) {
                Write-Host "📋 Debug info:" -ForegroundColor Yellow
                $content = $response.Content | ConvertFrom-Json
                Write-Host "   docs_url: $($content.docs_url)" -ForegroundColor White
                Write-Host "   redoc_url: $($content.redoc_url)" -ForegroundColor White
                Write-Host "   openapi_url: $($content.openapi_url)" -ForegroundColor White
            }
        } else {
            Write-Host "⚠️  Unexpected status: $($response.StatusCode)" -ForegroundColor Yellow
        }
    }
    catch {
        Write-Host "❌ FAILED - Error: $($_.Exception.Message)" -ForegroundColor Red
    }
}

Write-Host "`n🏁 Test completed!" -ForegroundColor Green