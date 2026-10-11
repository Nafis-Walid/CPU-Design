#!/usr/bin/env python3
"""
4-Bit Custom CPU Two-Pass Assembler
Compiles human-readable assembly language into 15-bit machine code for the Digital CPU.dig model.
"""

import sys
import re
import argparse
import xml.etree.ElementTree as ET
from typing import List, Dict, Tuple

OPCODES = {
    # Register-Register Operations (OPCODE[3:2] = 00)
    "XOR":  0x0,
    "ADD":  0x1,
    "ROR":  0x2,
    # Immediate Operations (OPCODE[3:2] = 01)
    "XORI": 0x4,
    "ADDI": 0x5,
    "RORI": 0x6,
    # Branch Operations (OPCODE[3:2] = 10)
    "JMP":  0x8,
    "JNZ":  0x9,
}

REGISTERS = {
    "R0": 0, "R1": 1, "R2": 2, "R3": 3,
    "r0": 0, "r1": 1, "r2": 2, "r3": 3
}

class Assembler:
    def __init__(self):
        self.labels = {}
        self.instructions = []

    def parse_reg(self, token: str) -> int:
        token = token.strip().rstrip(",")
        if token in REGISTERS:
            return REGISTERS[token]
        raise ValueError(f"Invalid register name: {token}. Must be R0, R1, R2, or R3.")

    def parse_immediate(self, token: str) -> int:
        token = token.strip().rstrip(",").lstrip("#")
        if token.startswith(("0x", "0X")):
            val = int(token, 16)
        else:
            val = int(token)
        if not (0 <= val <= 15):
            raise ValueError(f"Immediate value {val} out of range (0-15).")
        return val

    def parse_target(self, token: str) -> int:
        token = token.strip().rstrip(",")
        if token in self.labels:
            return self.labels[token]
        try:
            return int(token, 0)
        except ValueError:
            raise ValueError(f"Unknown jump target/label: '{token}'")

    def assemble(self, source_text: str) -> List[int]:
        lines = source_text.splitlines()
        clean_lines = []

        # Pass 1: Collect labels and clean statements
        pc = 0
        for line in lines:
            # Strip comments (semicolon only, so '#' can be used for immediates)
            line = re.sub(r";.*$", "", line).strip()
            if not line:
                continue

            # Check for label
            if ":" in line:
                label_part, rest = line.split(":", 1)
                label = label_part.strip()
                self.labels[label] = pc
                line = rest.strip()
                if not line:
                    continue

            clean_lines.append((pc, line))
            pc += 1

        if pc > 16:
            print(f"[!] Warning: Program has {pc} instructions, but CPU ROM has only 16 words.")

        # Pass 2: Generate machine code
        machine_code = []
        for current_pc, line in clean_lines:
            tokens = line.replace(",", " ").split()
            mnemonic = tokens[0].upper()

            # Handle Pseudo-instructions
            if mnemonic == "CLR":
                # CLR Rd -> XOR Rd, Rd
                rd = self.parse_reg(tokens[1])
                mnemonic = "XOR"
                tokens = ["XOR", f"R{rd}", f"R{rd}"]
            elif mnemonic == "NOP":
                # NOP -> XOR R0, R0
                mnemonic = "XOR"
                tokens = ["XOR", "R0", "R0"]

            if mnemonic not in OPCODES:
                raise ValueError(f"Unknown instruction: {mnemonic}")

            op = OPCODES[mnemonic]

            if mnemonic in ("JMP", "JNZ"):
                # Jump instructions: target is 4-bit address (bits 10:7)
                target = self.parse_target(tokens[1])
                target_4bit = target & 0xF
                # 15-bit instruction: [OPCODE (4b)] [TARGET (4b)] [UNUSED/0 (7b)]
                instr = (op << 11) | (target_4bit << 7)
            elif mnemonic in ("XORI", "ADDI", "RORI"):
                # Immediate instructions: Rd (2b), Imm (4b)
                rd = self.parse_reg(tokens[1])
                imm = self.parse_immediate(tokens[2])
                rs = imm & 0x3
                imm_high = (imm >> 2) & 0x3
                # Bits 10:9 = rd, Bits 8:7 = rs (lower 2 of imm), Bits 6:5 = imm_high
                target_or_reg = ((rd & 0x3) << 2) | rs
                imm_field = (imm_high << 5)
                instr = (op << 11) | (target_or_reg << 7) | imm_field
            else:
                # Register instructions: Rd (2b), Rs (2b)
                rd = self.parse_reg(tokens[1])
                rs = self.parse_reg(tokens[2])
                target_or_reg = ((rd & 0x3) << 2) | (rs & 0x3)
                instr = (op << 11) | (target_or_reg << 7)

            machine_code.append(instr & 0x7FFF)

        # Pad to 16 instructions if needed
        while len(machine_code) < 16:
            machine_code.append(0)

        return machine_code


def patch_cpu_dig(dig_path: str, rom_words: List[int]):
    """Directly updates the ROM component Data attribute in CPU.dig."""
    tree = ET.parse(dig_path)
    root = tree.getroot()

    hex_str = ",".join(f"{x:x}" for x in rom_words)
    patched = False

    for elem in root.findall(".//visualElement"):
        name = elem.find("elementName").text
        if name and "ROM" in name.upper():
            for entry in elem.findall(".//elementAttributes/entry"):
                if entry.find("string").text == "Data":
                    d = entry.find("data")
                    if d is not None:
                        d.text = hex_str
                        patched = True
                    break

    if patched:
        tree.write(dig_path, encoding="utf-8", xml_declaration=True)
        print(f"[+] Successfully patched ROM in {dig_path}")
    else:
        print(f"[-] Could not find ROM Data node in {dig_path}")


def main():
    parser = argparse.ArgumentParser(description="4-Bit CPU Assembler")
    parser.add_argument("source", nargs="?", default=None, help="Input assembly file (.asm)")
    parser.add_argument("--patch", action="store_true", help="Directly patch CPU.dig ROM data")
    parser.add_argument("--run", action="store_true", help="Run simulated CPU after assembling")
    args = parser.parse_args()

    # Default sample program if no file provided
    default_source = """
    ; 4-Bit CPU Demo Program:
    ; Counts R1 up from 0 to 5, then halts in loop
    START:
        CLR  R1          ; R1 = 0
        ADDI R2, #1      ; R2 = 1 (step)
    LOOP:
        ADD  R1, R2      ; R1 = R1 + 1
        XORI R3, #5      ; Compare R1 against 5 (via XOR)
        XOR  R3, R1
        JNZ  LOOP        ; If R1 != 5, continue loop
    DONE:
        JMP  DONE        ; Halt loop
    """

    if args.source:
        with open(args.source, "r") as f:
            source = f.read()
    else:
        print("[*] No source file specified, using built-in demo program.")
        source = default_source

    asm = Assembler()
    binary_words = asm.assemble(source)

    print("\n" + "=" * 60)
    print("  PC | HEX    | BINARY          | ASSEMBLY")
    print("=" * 60)
    for i, word in enumerate(binary_words[:16]):
        print(f"  {i:2d} | 0x{word:04X} | {word:015b} |")
    print("=" * 60)

    rom_hex_list = ",".join(f"{w:x}" for w in binary_words)
    print(f"\n[+] Digital ROM Data string:\n    {rom_hex_list}\n")

    if args.patch:
        patch_cpu_dig("/Users/shajninhaqueaishy/AI-Work/CPU-Design/CPU.dig", binary_words)

    if args.run:
        from cpu_simulator import CPU
        cpu = CPU(binary_words)
        print("\n[+] Running Assembled Program in Simulator:")
        cpu.print_state_banner()
        for _ in range(16):
            s = cpu.step()
            cpu.print_step(s)


if __name__ == "__main__":
    main()
