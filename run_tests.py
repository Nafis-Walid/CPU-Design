#!/usr/bin/env python3
"""
Automated Test Runner for 4-Bit CPU Design Project
Runs Digital CLI test benches on hardware circuits and executes software simulation tests.
"""

import subprocess
import sys
import os

DIGITAL_JAR = "/Applications/Digital/Digital.jar"
PROJECT_DIR = "/Users/shajninhaqueaishy/AI-Work/CPU-Design"

CIRCUIT_TESTS = [
    ("4-bit Full Adder", "test_full_adder.dig"),
    ("Control Unit Decoder", "test_control_unit.dig"),
    ("4-bit Arithmetic Logic Unit (ALU)", "test_alu.dig")
]

def run_digital_test(circuit_name: str, file_name: str) -> bool:
    path = os.path.join(PROJECT_DIR, file_name)
    cmd = ["java", "-cp", DIGITAL_JAR, "CLI", "test", "-circ", path]
    try:
        proc = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, timeout=10)
        output = proc.stdout.strip() + " " + proc.stderr.strip()
        if "passed" in output.lower():
            print(f"  [PASS] {circuit_name:<38} -> Passed")
            return True
        else:
            print(f"  [FAIL] {circuit_name:<38} -> Failed\n         {output}")
            return False
    except Exception as e:
        print(f"  [ERR]  {circuit_name:<38} -> {e}")
        return False

def run_simulator_test() -> bool:
    cmd = [sys.executable, os.path.join(PROJECT_DIR, "cpu_simulator.py"), "--steps", "6"]
    try:
        proc = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, timeout=5)
        if proc.returncode == 0 and "Simulation completed" in proc.stdout:
            print(f"  [PASS] {'Cycle-Accurate CPU Simulator':<38} -> Passed")
            return True
        else:
            print(f"  [FAIL] {'Cycle-Accurate CPU Simulator':<38} -> Failed")
            return False
    except Exception as e:
        print(f"  [ERR]  {'Cycle-Accurate CPU Simulator':<38} -> {e}")
        return False

def run_assembler_test() -> bool:
    cmd = [sys.executable, os.path.join(PROJECT_DIR, "assembler.py"), "--run"]
    try:
        proc = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, timeout=5)
        if proc.returncode == 0 and "Digital ROM Data string" in proc.stdout:
            print(f"  [PASS] {'Two-Pass Assembler & Pipeline Runner':<38} -> Passed")
            return True
        else:
            print(f"  [FAIL] {'Two-Pass Assembler & Pipeline Runner':<38} -> Failed")
            return False
    except Exception as e:
        print(f"  [ERR]  {'Two-Pass Assembler & Pipeline Runner':<38} -> {e}")
        return False

def main():
    print("\n" + "=" * 65)
    print("      4-BIT CPU DESIGN - AUTOMATED HARDWARE & SOFTWARE TESTS")
    print("=" * 65)

    passed = 0
    total = len(CIRCUIT_TESTS) + 2

    print("\n[*] 1. Hardware Circuit Test Benches (Digital Logic Simulator):")
    for name, f in CIRCUIT_TESTS:
        if run_digital_test(name, f):
            passed += 1

    print("\n[*] 2. Software Architecture & Toolchain Tests:")
    if run_simulator_test():
        passed += 1
    if run_assembler_test():
        passed += 1

    print("\n" + "=" * 65)
    print(f"  TOTAL RESULTS: {passed}/{total} Passed ({(passed/total)*100:.1f}%)")
    print("=" * 65 + "\n")

    if passed == total:
        print("[+] All hardware circuits and software toolchains verified successfully!\n")
        sys.exit(0)
    else:
        print("[-] Some tests failed. Please inspect logs.\n")
        sys.exit(1)

if __name__ == "__main__":
    main()
