# GlassBite Testing Script
# Run comprehensive tests to verify all features work

Write-Host "====================================" -ForegroundColor Cyan
Write-Host "GlassBite AI Chatbot - Test Suite" -ForegroundColor Cyan
Write-Host "====================================" -ForegroundColor Cyan
Write-Host ""

$baseUrl = "http://localhost:5000"
$testPhone = "whatsapp:+1234567890"

# Function to make HTTP requests
function Invoke-Test {
    param (
        [string]$Name,
        [string]$Method,
        [string]$Endpoint,
        [hashtable]$Body = @{}
    )
    
    Write-Host "Testing: $Name" -ForegroundColor Yellow
    
    try {
        if ($Method -eq "GET") {
            $response = Invoke-RestMethod -Uri "$baseUrl$Endpoint" -Method Get
        } else {
            $jsonBody = $Body | ConvertTo-Json
            $response = Invoke-RestMethod -Uri "$baseUrl$Endpoint" -Method Post -Body $jsonBody -ContentType "application/json"
        }
        
        Write-Host "✓ PASS" -ForegroundColor Green
        Write-Host "Response: $($response | ConvertTo-Json -Compress)" -ForegroundColor Gray
        Write-Host ""
        return $true
    }
    catch {
        Write-Host "✗ FAIL: $($_.Exception.Message)" -ForegroundColor Red
        Write-Host ""
        return $false
    }
}

# Test 1: Health Check
$test1 = Invoke-Test -Name "Health Check" -Method "GET" -Endpoint "/"

# Test 2: Statistics Endpoint
$test2 = Invoke-Test -Name "Statistics" -Method "GET" -Endpoint "/stats"

# Test 3: Chatbot - Daily Summary
$test3 = Invoke-Test -Name "Chatbot: Daily Summary" -Method "POST" -Endpoint "/test/question" -Body @{
    phone_number = $testPhone
    question = "How am I doing today?"
}

# Test 4: Chatbot - Goal Setting
$test4 = Invoke-Test -Name "Chatbot: Goal Setting" -Method "POST" -Endpoint "/test/question" -Body @{
    phone_number = $testPhone
    question = "My goal is 2000 calories"
}

# Test 5: Chatbot - Goal Progress
$test5 = Invoke-Test -Name "Chatbot: Goal Progress" -Method "POST" -Endpoint "/test/question" -Body @{
    phone_number = $testPhone
    question = "Am I meeting my goal?"
}

# Test 6: Chatbot - Nutrient Query
$test6 = Invoke-Test -Name "Chatbot: Nutrient Query" -Method "POST" -Endpoint "/test/question" -Body @{
    phone_number = $testPhone
    question = "What's my protein intake?"
}

# Test 7: Chatbot - Comparison
$test7 = Invoke-Test -Name "Chatbot: Comparison" -Method "POST" -Endpoint "/test/question" -Body @{
    phone_number = $testPhone
    question = "Compare today to yesterday"
}

# Test 8: Chatbot - Pattern Analysis
$test8 = Invoke-Test -Name "Chatbot: Pattern Analysis" -Method "POST" -Endpoint "/test/question" -Body @{
    phone_number = $testPhone
    question = "Show me patterns"
}

# Test 9: Chatbot - Recommendations
$test9 = Invoke-Test -Name "Chatbot: Recommendations" -Method "POST" -Endpoint "/test/question" -Body @{
    phone_number = $testPhone
    question = "What should I eat next?"
}

# Test 10: Chatbot - Help
$test10 = Invoke-Test -Name "Chatbot: Help" -Method "POST" -Endpoint "/test/question" -Body @{
    phone_number = $testPhone
    question = "help"
}

# Summary
Write-Host "====================================" -ForegroundColor Cyan
Write-Host "Test Summary" -ForegroundColor Cyan
Write-Host "====================================" -ForegroundColor Cyan

$tests = @($test1, $test2, $test3, $test4, $test5, $test6, $test7, $test8, $test9, $test10)
$passed = ($tests | Where-Object { $_ -eq $true }).Count
$failed = ($tests | Where-Object { $_ -eq $false }).Count

Write-Host "Total Tests: $($tests.Count)" -ForegroundColor White
Write-Host "Passed: $passed" -ForegroundColor Green
Write-Host "Failed: $failed" -ForegroundColor Red
Write-Host ""

if ($failed -eq 0) {
    Write-Host "All tests passed! ✓" -ForegroundColor Green
} else {
    Write-Host "Some tests failed. Check the output above." -ForegroundColor Red
}

Write-Host ""
Write-Host "Note: To test meal logging with photos, send a food image via WhatsApp" -ForegroundColor Cyan
Write-Host "      to your Twilio sandbox number." -ForegroundColor Cyan
