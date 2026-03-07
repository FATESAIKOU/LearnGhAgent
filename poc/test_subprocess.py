#!/usr/bin/env python3
"""PoC-C: Test Python subprocess control of gh copilot"""

import subprocess
import time

print("=== Test 1: Normal execution ===")
start = time.time()
result = subprocess.run(
    ["gh", "copilot", "-p", "Reply with exactly: PoC subprocess test OK", "--yolo", "-s", "--no-ask-user"],
    capture_output=True,
    text=True,
    timeout=120,
)
elapsed = time.time() - start
print(f"Exit code: {result.returncode}")
print(f"Stdout: {repr(result.stdout.strip())}")
print(f"Stderr: {repr(result.stderr.strip()[:200])}")
print(f"Elapsed: {elapsed:.1f}s")

print("\n=== Test 2: Timeout (3s limit) ===")
try:
    result2 = subprocess.run(
        ["gh", "copilot", "-p", "Write a very long essay about the history of computing", "--yolo", "-s", "--no-ask-user"],
        capture_output=True,
        text=True,
        timeout=3,
    )
    print(f"Completed (unexpected): exit={result2.returncode}")
except subprocess.TimeoutExpired as e:
    print(f"TimeoutExpired caught as expected!")
    print(f"Partial stdout: {repr(e.stdout[:100] if e.stdout else 'None')}")

print("\n=== PoC-C Complete ===")
