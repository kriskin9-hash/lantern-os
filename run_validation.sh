#!/bin/bash
# Lantern Deployment Validation Script
# Tests all key endpoints and saves results

BASE_URL="http://127.0.0.1:5000"
TIMESTAMP=$(date -u +"%Y-%m-%dT%H:%M:%SZ")
REPORT_FILE="/tmp/lantern_validation_final_report.json"

echo "========================================"
echo "LANTERN DEPLOYMENT VALIDATION"
echo "========================================"
echo ""
echo "Timestamp: $TIMESTAMP"
echo "Base URL: $BASE_URL"
echo ""

# Test 1: Root interface
echo "[TEST 1] Root interface..."
RESPONSE=$(curl -s -w "\n%{http_code}" "$BASE_URL/")
STATUS_CODE=$(echo "$RESPONSE" | tail -1)
CONTENT_LENGTH=$(echo "$RESPONSE" | head -1 | wc -c)

if [ "$STATUS_CODE" = "200" ] && [ "$CONTENT_LENGTH" -gt 1000 ]; then
    echo "[PASS] Root interface loads (Status: $STATUS_CODE, Size: $CONTENT_LENGTH bytes)"
    TEST1="PASS"
else
    echo "[FAIL] Root interface failed (Status: $STATUS_CODE)"
    TEST1="FAIL"
fi

# Test 2: Chat API GET
echo "[TEST 2] Chat API (GET)..."
RESPONSE=$(curl -s -w "\n%{http_code}" "$BASE_URL/api/chat")
STATUS_CODE=$(echo "$RESPONSE" | tail -1)
BODY=$(echo "$RESPONSE" | head -1)

if [ "$STATUS_CODE" = "200" ]; then
    MSG_COUNT=$(echo "$BODY" | grep -o "user\|assistant" | wc -l)
    echo "[PASS] Chat API returns messages (Status: $STATUS_CODE, Messages: $MSG_COUNT)"
    TEST2="PASS"
else
    echo "[FAIL] Chat API failed (Status: $STATUS_CODE)"
    TEST2="FAIL"
fi

# Test 3: Chat API POST
echo "[TEST 3] Chat API (POST)..."
RESPONSE=$(curl -s -w "\n%{http_code}" -X POST \
    -H "Content-Type: application/json" \
    -d '{"content":"Automated validation message"}' \
    "$BASE_URL/api/chat")
STATUS_CODE=$(echo "$RESPONSE" | tail -1)

if [ "$STATUS_CODE" = "200" ] || [ "$STATUS_CODE" = "201" ]; then
    echo "[PASS] Chat message posted (Status: $STATUS_CODE)"
    TEST3="PASS"
else
    echo "[FAIL] Chat message failed (Status: $STATUS_CODE)"
    TEST3="FAIL"
fi

# Test 4: Audio API
echo "[TEST 4] Audio API (GET)..."
RESPONSE=$(curl -s -w "\n%{http_code}" "$BASE_URL/api/audio")
STATUS_CODE=$(echo "$RESPONSE" | tail -1)
BODY=$(echo "$RESPONSE" | head -1)

if [ "$STATUS_CODE" = "200" ]; then
    FILE_COUNT=$(echo "$BODY" | grep -o "\"" | wc -l)
    echo "[PASS] Audio API responds (Status: $STATUS_CODE)"
    TEST4="PASS"
else
    echo "[FAIL] Audio API failed (Status: $STATUS_CODE)"
    TEST4="FAIL"
fi

# Summary
echo ""
echo "========================================"
echo "VALIDATION SUMMARY"
echo "========================================"

PASSED=0
TOTAL=4

[ "$TEST1" = "PASS" ] && ((PASSED++))
[ "$TEST2" = "PASS" ] && ((PASSED++))
[ "$TEST3" = "PASS" ] && ((PASSED++))
[ "$TEST4" = "PASS" ] && ((PASSED++))

echo "Tests Passed: $PASSED/$TOTAL"
echo "Success Rate: $((PASSED * 100 / TOTAL))%"

if [ "$PASSED" = "$TOTAL" ]; then
    CONCLUSION="DEPLOYMENT VALIDATED: All endpoints operational"
else
    CONCLUSION="DEPLOYMENT PARTIAL: Some endpoints need attention"
fi

echo "Conclusion: $CONCLUSION"
echo ""

# Generate JSON report
cat > "$REPORT_FILE" << EOF
{
  "deployment_validation_final": {
    "timestamp": "$TIMESTAMP",
    "summary": {
      "total_tests": $TOTAL,
      "passed": $PASSED,
      "failed": $((TOTAL - PASSED)),
      "success_rate": "$((PASSED * 100 / TOTAL))%",
      "conclusion": "$CONCLUSION"
    },
    "tests": [
      {
        "name": "Root Interface",
        "endpoint": "GET /",
        "status": "$TEST1"
      },
      {
        "name": "Chat API (GET)",
        "endpoint": "GET /api/chat",
        "status": "$TEST2"
      },
      {
        "name": "Chat API (POST)",
        "endpoint": "POST /api/chat",
        "status": "$TEST3"
      },
      {
        "name": "Audio API",
        "endpoint": "GET /api/audio",
        "status": "$TEST4"
      }
    ],
    "deployment_info": {
      "base_url": "$BASE_URL",
      "services": [
        "Lantern Flask App (port 5000)",
        "Browser Interface",
        "Chat API",
        "Audio Library API"
      ]
    }
  }
}
EOF

echo "[OK] Report saved to: $REPORT_FILE"
