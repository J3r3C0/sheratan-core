# Quick test for robust_parser and models
import sys
sys.path.insert(0, "core")

from sheratan_core_v2.robust_parser import extract_json_from_text, validate_lcp_response
from sheratan_core_v2.models import LoopState, LoopMetrics

# Test 1: Extract JSON from code block
text1 = '''Here is the response:
```json
{"ok": true, "action": "test", "new_jobs": []}
```
End of response'''

result1 = extract_json_from_text(text1)
print("Test 1 - Code block extraction:", "PASS" if result1 and result1.get("ok") else "FAIL")

# Test 2: Extract JSON by brace matching
text2 = 'Some text {"ok": true, "action": "create_followup_jobs"} more text'
result2 = extract_json_from_text(text2)
print("Test 2 - Brace matching:", "PASS" if result2 and result2.get("action") else "FAIL")

# Test 3: LCP Validation
is_valid, issues = validate_lcp_response({"ok": True, "action": "test"})
print("Test 3 - LCP validation:", "PASS" if is_valid else f"FAIL: {issues}")

# Test 4: LoopState model
state = LoopState(iteration=1, history_summary="Initial")
next_state = state.add_iteration("Test action", "Test result")
print("Test 4 - LoopState:", "PASS" if next_state.iteration == 2 else "FAIL")

# Test 5: LoopMetrics
metrics = LoopMetrics(tasks_completed=3, error_count=0)
print("Test 5 - LoopMetrics:", "PASS" if metrics.tasks_completed == 3 else "FAIL")

print("\n✅ All tests completed!")
