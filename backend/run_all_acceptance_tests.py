"""
Unified Test Runner for Aura Skincare Voice Agent.
Executes all test suites across all 6 phases and produces a consolidated pass/fail report.
"""
import subprocess
import sys
import os

TEST_FILES = [
    ("Phase 1: Customer Auth & Validation", "test_phase1_auth.py"),
    ("Phase 2: Customer & Order Ownership", "test_phase2_orders.py"),
    ("Phase 3: Active Call Memory & Isolation", "test_phase3_memory.py"),
    ("Phase 4: Selective Storage & Summary", "test_phase4_storage.py"),
    ("Phase 5: n8n Email Webhook Pipeline", "test_phase5_email_webhook.py"),
    ("Phase 6: E2E Frontend-Backend API Flow", "test_phase6_frontend_api.py"),
    ("Phase 7: Cloud Neural TTS Voice Synthesis", "test_tts_api.py"),
]

def main():
    print("=" * 70)
    print("      AURA SKINCARE AI VOICE AGENT - COMPLETE TEST SUITE")
    print("=" * 70)

    python_executable = sys.executable
    backend_dir = os.path.dirname(os.path.abspath(__file__))

    results = []

    for name, filename in TEST_FILES:
        filepath = os.path.join(backend_dir, filename)
        print(f"\n--> Running {name} ({filename})...")
        try:
            res = subprocess.run(
                [python_executable, filepath],
                cwd=backend_dir,
                capture_output=True,
                text=True,
                timeout=120
            )
            passed = res.returncode == 0
            results.append((name, filename, passed, res.stdout, res.stderr))
            if passed:
                print(f"[PASS] {name}")
            else:
                print(f"[FAIL] {name}")
                print(res.stdout)
                print(res.stderr)
        except Exception as e:
            results.append((name, filename, False, "", str(e)))
            print(f"[FAIL] {name} with exception: {e}")

    print("\n" + "=" * 70)
    print("                   CONSOLIDATED TEST RESULTS")
    print("=" * 70)
    all_passed = True
    for name, filename, passed, _, _ in results:
        status_tag = "[PASS 100%]" if passed else "[FAIL]"
        print(f" {status_tag:<14} | {name:<42} | {filename}")
        if not passed:
            all_passed = False

    print("=" * 70)
    if all_passed:
        print(">>> ALL ACCEPTANCE TEST CRITERIA SATISFIED SUCCESSFULLY! <<<")
    else:
        print(">>> SOME TESTS FAILED. CHECK LOGS ABOVE. <<<")
    print("=" * 70)

    sys.exit(0 if all_passed else 1)

if __name__ == "__main__":
    main()
