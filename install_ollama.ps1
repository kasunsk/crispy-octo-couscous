# Ollama Installation and Setup Script for Windows

Write-Host "=== Ollama Installation Helper ===" -ForegroundColor Cyan
Write-Host ""

# Check if Ollama is already installed
$ollamaInstalled = $false
try {
    $version = ollama --version 2>$null
    if ($version) {
        Write-Host "✓ Ollama is already installed: $version" -ForegroundColor Green
        $ollamaInstalled = $true
    }
} catch {
    Write-Host "✗ Ollama is not installed" -ForegroundColor Yellow
}

# Check if Ollama is running
$ollamaRunning = $false
try {
    $response = Invoke-WebRequest -Uri "http://localhost:11434/api/tags" -UseBasicParsing -TimeoutSec 2 -ErrorAction Stop
    if ($response.StatusCode -eq 200) {
        Write-Host "✓ Ollama is running" -ForegroundColor Green
        $ollamaRunning = $true
    }
} catch {
    Write-Host "✗ Ollama is not running or not accessible" -ForegroundColor Red
}

if (-not $ollamaInstalled) {
    Write-Host ""
    Write-Host "To install Ollama:" -ForegroundColor Yellow
    Write-Host "1. Download from: https://ollama.ai/download/windows" -ForegroundColor White
    Write-Host "2. Run the installer" -ForegroundColor White
    Write-Host "3. Run this script again to set up models" -ForegroundColor White
    Write-Host ""
    $install = Read-Host "Would you like to open the download page? (y/n)"
    if ($install -eq "y" -or $install -eq "Y") {
        Start-Process "https://ollama.ai/download/windows"
    }
    exit
}

if (-not $ollamaRunning) {
    Write-Host ""
    Write-Host "Starting Ollama..." -ForegroundColor Yellow
    try {
        Start-Process "ollama" -ArgumentList "serve" -WindowStyle Hidden
        Start-Sleep -Seconds 3
        
        # Check again
        $response = Invoke-WebRequest -Uri "http://localhost:11434/api/tags" -UseBasicParsing -TimeoutSec 5 -ErrorAction Stop
        if ($response.StatusCode -eq 200) {
            Write-Host "✓ Ollama started successfully" -ForegroundColor Green
            $ollamaRunning = $true
        }
    } catch {
        Write-Host "✗ Could not start Ollama automatically" -ForegroundColor Red
        Write-Host "Please start Ollama manually or check Windows Services" -ForegroundColor Yellow
    }
}

if ($ollamaRunning) {
    Write-Host ""
    Write-Host "Checking available models..." -ForegroundColor Cyan
    try {
        $models = (Invoke-WebRequest -Uri "http://localhost:11434/api/tags" -UseBasicParsing).Content | ConvertFrom-Json
        if ($models.models.Count -eq 0) {
            Write-Host "✗ No models found" -ForegroundColor Yellow
            Write-Host ""
            Write-Host "Pulling recommended model (llama3:8b)..." -ForegroundColor Cyan
            Write-Host "This may take several minutes depending on your internet speed..." -ForegroundColor Yellow
            ollama pull llama3:8b
            Write-Host "✓ Model pulled successfully" -ForegroundColor Green
        } else {
            Write-Host "✓ Available models:" -ForegroundColor Green
            foreach ($model in $models.models) {
                Write-Host "  - $($model.name)" -ForegroundColor White
            }
        }
    } catch {
        Write-Host "✗ Could not check models" -ForegroundColor Red
    }
    
    Write-Host ""
    Write-Host "=== Setup Complete ===" -ForegroundColor Green
    Write-Host "Ollama is ready to use!" -ForegroundColor Green
    Write-Host ""
    Write-Host "You can now:" -ForegroundColor Cyan
    Write-Host "1. Refresh your browser at http://localhost:5173" -ForegroundColor White
    Write-Host "2. The connection status should show 'Connected'" -ForegroundColor White
    Write-Host "3. Start asking questions!" -ForegroundColor White
} else {
    Write-Host ""
    Write-Host "=== Setup Incomplete ===" -ForegroundColor Red
    Write-Host "Please ensure Ollama is running before using the application." -ForegroundColor Yellow
}
