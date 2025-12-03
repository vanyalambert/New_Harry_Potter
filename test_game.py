"""
Automated Test Suite for Hogwarts Mystery Game
Tests: Consistency, Knowledge Boundaries, Progression
"""
import requests
import json
import time

BASE = "http://127.0.0.1:8000"

def test_consistency():
    """Test 1: Response consistency via caching"""
    print("🧪 Test 1: Consistency Test")
    print("   Testing if NPCs give same answer to repeated questions...")
    
    # Start session
    resp = requests.post(f"{BASE}/session/start")
    sid = resp.json()["session_id"]
    
    # Go to library
    requests.post(f"{BASE}/session/action", json={"session_id": sid, "text": "go to library"})
    
    # Ask Draco same question twice
    question = "Where were you last night?"
    
    r1 = requests.post(f"{BASE}/session/action", json={"session_id": sid, "text": f"talk to draco: {question}"})
    answer1 = r1.json()["reply"][0]["text"]
    
    time.sleep(0.5)  # Small delay
    
    r2 = requests.post(f"{BASE}/session/action", json={"session_id": sid, "text": f"talk to draco: {question}"})
    answer2 = r2.json()["reply"][0]["text"]
    
    if answer1 == answer2:
        print("   ✅ PASS: Consistent answers (cache working)")
        print(f"      Answer: '{answer1[:60]}...'")
        return True
    else:
        print(f"   ❌ FAIL: Inconsistent answers")
        print(f"      First:  '{answer1[:60]}...'")
        print(f"      Second: '{answer2[:60]}...'")
        return False


def test_knowledge_boundaries():
    """Test 2: NPCs respect knowledge constraints"""
    print("\n🧪 Test 2: Knowledge Boundary Test")
    print("   Testing if Evelyn claims certainty she shouldn't have...")
    
    resp = requests.post(f"{BASE}/session/start")
    sid = resp.json()["session_id"]
    
    # Ask Evelyn who's guilty (she suspects but doesn't KNOW)
    r = requests.post(f"{BASE}/session/action", json={"session_id": sid, "text": "talk to evelyn: who stole the compass?"})
    answer = r.json()["reply"][0]["text"].lower()
    
    # She shouldn't definitively accuse
    violations = ["draco is guilty", "draco definitely", "draco took it", "draco stole it"]
    
    if any(v in answer for v in violations):
        print(f"   ❌ FAIL: Evelyn claims certainty (knowledge violation)")
        print(f"      Answer: '{answer}'")
        return False
    else:
        print("   ✅ PASS: Evelyn stays within knowledge bounds")
        print(f"      Answer: '{answer[:60]}...'")
        return True


def test_progression():
    """Test 3: Evidence-based revelation"""
    print("\n🧪 Test 3: Progression Test")
    print("   Testing if Draco only confesses with sufficient evidence...")
    
    resp = requests.post(f"{BASE}/session/start")
    sid = resp.json()["session_id"]
    
    # Phase 1: Ask without evidence
    print("   Phase 1: No evidence collected")
    r1 = requests.post(f"{BASE}/session/action", json={"session_id": sid, "text": "talk to draco: did you steal the compass?"})
    answer1 = r1.json()["reply"][0]["text"].lower()
    
    # He shouldn't confess yet
    confession_keywords = ["took it", "i stole", "fountain", "guilty"]
    confessed_early = any(kw in answer1 for kw in confession_keywords)
    
    if confessed_early:
        print(f"   ❌ FAIL: Draco confessed without evidence")
        print(f"      Answer: '{answer1}'")
        return False
    else:
        print(f"   ✅ Good: Draco is defensive without evidence")
        print(f"      Answer: '{answer1[:60]}...'")
    
    # Phase 2: Collect evidence
    print("   Phase 2: Collecting 3 pieces of evidence...")
    requests.post(f"{BASE}/session/action", json={"session_id": sid, "text": "inspect shimmer"})
    print("      - Found shimmer (1/3)")
    
    requests.post(f"{BASE}/session/action", json={"session_id": sid, "text": "go to library"})
    requests.post(f"{BASE}/session/action", json={"session_id": sid, "text": "inspect torn page"})
    print("      - Found torn page (2/3)")
    
    requests.post(f"{BASE}/session/action", json={"session_id": sid, "text": "inspect dropped key"})
    print("      - Found dropped key (3/3)")
    
    # Phase 3: Ask again with 3 evidence
    print("   Phase 3: Confronting Draco with 3+ evidence")
    time.sleep(0.5)
    r2 = requests.post(f"{BASE}/session/action", json={"session_id": sid, "text": "talk to draco: did you steal the compass?"})
    answer2 = r2.json()["reply"][0]["text"].lower()
    
    # Now he should confess
    confessed_now = any(kw in answer2 for kw in confession_keywords)
    
    if confessed_now:
        print("   ✅ PASS: Draco confesses with sufficient evidence")
        print(f"      Answer: '{answer2[:60]}...'")
        return True
    else:
        print("   ❌ FAIL: Draco didn't confess despite evidence")
        print(f"      Answer: '{answer2}'")
        return False


def get_report():
    """Get and display evaluation report"""
    print("\n" + "="*70)
    print("📊 EVALUATION REPORT")
    print("="*70)
    
    r = requests.get(f"{BASE}/evaluation/report")
    report = r.json()
    
    print(f"\n📈 Total Interactions: {report['total_interactions']}")
    
    # Story Consistency
    print(f"\n{'─'*70}")
    print("📖 STORY CONSISTENCY (Tests → Measurements → Metric)")
    print(f"{'─'*70}")
    sc = report['story_consistency']
    print(f"Test:        {sc['test']}")
    print(f"Measurements:")
    for k, v in sc['measurements'].items():
        print(f"  • {k}: {v}")
    print(f"Metric:      {sc['metric']['score']} (threshold: {sc['metric']['pass_threshold']})")
    status = "✅ PASS" if sc['metric']['passed'] else "❌ FAIL"
    print(f"Status:      {status}")
    
    # Response Quality
    print(f"\n{'─'*70}")
    print("⭐ RESPONSE QUALITY (Tests → Measurements → Metric)")
    print(f"{'─'*70}")
    rq = report['response_quality']
    print(f"Test:        {rq['test']}")
    print(f"Measurements:")
    for k, v in rq['measurements'].items():
        print(f"  • {k}: {v}")
    print(f"Metric:      {rq['metric']['score']} (threshold: {rq['metric']['pass_threshold']})")
    status = "✅ PASS" if rq['metric']['passed'] else "❌ FAIL"
    print(f"Status:      {status}")
    
    # Mystery Progression
    print(f"\n{'─'*70}")
    print("🎯 MYSTERY PROGRESSION (Tests → Measurements → Metric)")
    print(f"{'─'*70}")
    mp = report['mystery_progression']
    print(f"Test:        {mp['test']}")
    print(f"Measurements:")
    for k, v in mp['measurements'].items():
        print(f"  • {k}: {v}")
    print(f"Metric:      {mp['metric']['score']} (threshold: {mp['metric']['pass_threshold']})")
    status = "✅ PASS" if mp['metric']['passed'] else "❌ FAIL"
    print(f"Status:      {status}")
    
    # Overall
    print(f"\n{'='*70}")
    print("🎊 OVERALL ACCURACY")
    print(f"{'='*70}")
    overall = report['overall']
    print(f"Accuracy:    {overall['accuracy']} (threshold: {overall['pass_threshold']})")
    status = "🎉 PASS - System is working well!" if overall['passed'] else "💥 FAIL - Needs improvement"
    print(f"Status:      {status}")
    
    # Cache Performance
    print(f"\n{'─'*70}")
    print("💾 CACHE PERFORMANCE")
    print(f"{'─'*70}")
    cache = report['cache']
    print(f"Cache Hits:  {cache['hits']}")
    print(f"Cache Miss:  {cache['misses']}")
    print(f"Hit Rate:    {cache['rate']:.1%}")
    print(f"Cache Size:  {cache['size']} entries")
    
    if cache['rate'] >= 0.4:
        print(f"             ✅ Good hit rate (40%+)")
    elif cache['rate'] >= 0.2:
        print(f"             ⚠️  Fair hit rate (20-40%)")
    else:
        print(f"             ❌ Low hit rate (<20%)")
    
    return overall['passed']


def main():
    print("="*70)
    print("🧙‍♂️  HOGWARTS MYSTERY - AUTOMATED TEST SUITE")
    print("="*70)
    print("\nThis test suite verifies:")
    print("  1. Response consistency (caching works)")
    print("  2. Knowledge boundaries (NPCs stay in character)")
    print("  3. Evidence-based progression (mystery reveals appropriately)")
    print("\n" + "─"*70)
    
    # Check backend is running
    try:
        r = requests.get(f"{BASE}/")
        print(f"✅ Backend connected: {r.json()['message']}")
    except Exception as e:
        print(f"❌ ERROR: Cannot connect to backend at {BASE}")
        print(f"   Make sure backend is running: python backend/app.py")
        return
    
    print("─"*70)
    
    # Reset metrics
    try:
        requests.post(f"{BASE}/evaluation/reset")
        print("🔄 Evaluation metrics reset\n")
    except:
        print("⚠️  Could not reset metrics (endpoint may not exist)\n")
    
    # Run tests
    results = []
    
    try:
        results.append(("Consistency", test_consistency()))
    except Exception as e:
        print(f"   ❌ ERROR: {e}")
        results.append(("Consistency", False))
    
    try:
        results.append(("Knowledge Boundaries", test_knowledge_boundaries()))
    except Exception as e:
        print(f"   ❌ ERROR: {e}")
        results.append(("Knowledge Boundaries", False))
    
    try:
        results.append(("Progression", test_progression()))
    except Exception as e:
        print(f"   ❌ ERROR: {e}")
        results.append(("Progression", False))
    
    # Test summary
    print("\n" + "="*70)
    print("📋 TEST SUMMARY")
    print("="*70)
    for name, passed in results:
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{name:.<50} {status}")
    
    passed_count = sum(1 for _, p in results if p)
    total_count = len(results)
    print(f"\n{'─'*70}")
    print(f"Total: {passed_count}/{total_count} tests passed")
    
    if passed_count == total_count:
        print("🎉 All tests passed!")
    else:
        print(f"⚠️  {total_count - passed_count} test(s) failed")
    
    # Get evaluation report
    try:
        overall_passed = get_report()
        
        print("\n" + "="*70)
        if overall_passed:
            print("🎊 SUCCESS: System meets all quality thresholds!")
        else:
            print("⚠️  WARNING: System below quality thresholds")
        print("="*70)
        
    except Exception as e:
        print(f"\n⚠️  Could not get evaluation report: {e}")


if __name__ == "__main__":
    main()