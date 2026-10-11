#!/usr/bin/env python3
"""
4-Bit CPU Cycle-Accurate Simulator & Datapath Visualizer
Simulates the exact digital logic architecture defined in CPU.dig (HNeemann Digital).
"""

import sys
import argparse
from typing import List, Tuple, Dict, Any

class CPU:
    def __init__(self, rom_data: List[int] = None):
        # Default ROM program from CPU.dig
        default_rom = [0x0280, 0x2AA0, 0x3260, 0x4280, 0x0280, 0x4A00]
        self.rom = [0] * 16
        if rom_data:
            for i, val in enumerate(rom_data[:16]):
                self.rom[i] = val & 0x7FFF
        else:
            for i, val in enumerate(default_rom):
                self.rom[i] = val & 0x7FFF

        # Architectural State
        self.pc = 0              # 4-bit Program Counter (0-15)
        self.registers = [0] * 4 # 4x 4-bit Registers (R0-R3)
        self.zf = 0              # Zero Flag (1 bit)
        self.cf = 0              # Carry Flag (1 bit)
        self.cycle = 0           # Clock cycle counter

    def decode(self, instr: int) -> Dict[str, Any]:
        """Decodes 15-bit instruction according to CPU.dig datapath."""
        opcode = (instr >> 11) & 0xF
        target_or_reg = (instr >> 7) & 0xF
        rd = (target_or_reg >> 2) & 0x3
        rs = target_or_reg & 0x3
        target_addr = target_or_reg

        # Immediate extraction (lower bits)
        imm_low = (instr >> 5) & 0x3
        imm_val = ((imm_low << 2) | rs) & 0xF

        # Control Unit signals
        op = opcode & 0x3
        imm_sel = 1 if ((opcode & 0x4) and not (opcode & 0x8)) else 0
        reg_en = 0 if (opcode & 0x8) else 1

        # Jump selection logic
        is_branch = ((opcode >> 2) & 0x3) == 0x2 # opcode[3:2] == 10 (8 or 9)
        if is_branch:
            cond_type = opcode & 0x3
            if cond_type == 0:   # 0x8: JMP unconditional
                jmp_sel = 1
            elif cond_type == 1: # 0x9: JNZ (Jump if Not Zero)
                jmp_sel = 1 if (self.zf == 0) else 0
            else:
                jmp_sel = 0
        else:
            jmp_sel = 0

        # Assembly mnemonic
        mnemonic_map = {
            0x0: f"XOR  R{rd}, R{rs}",
            0x1: f"ADD  R{rd}, R{rs}",
            0x2: f"ROR  R{rd}, R{rs}",
            0x4: f"XORI R{rd}, #{imm_val}",
            0x5: f"ADDI R{rd}, #{imm_val}",
            0x6: f"RORI R{rd}, #{imm_val}",
            0x8: f"JMP  {target_addr}",
            0x9: f"JNZ  {target_addr}",
        }
        mnemonic = mnemonic_map.get(opcode, f"UNKNOWN (0x{opcode:X})")

        return {
            "raw": instr,
            "opcode": opcode,
            "rd": rd,
            "rs": rs,
            "imm_val": imm_val,
            "target_addr": target_addr,
            "op": op,
            "imm_sel": imm_sel,
            "reg_en": reg_en,
            "jmp_sel": jmp_sel,
            "mnemonic": mnemonic
        }

    def alu(self, a: int, b: int, op: int) -> Tuple[int, int, int]:
        """4-bit ALU identical to ALU(4-bit).dig."""
        a = a & 0xF
        b = b & 0xF

        # Full Adder always computes sum & carry in hardware
        add_sum = a + b
        adder_res = add_sum & 0xF
        cf = 1 if add_sum >= 16 else 0

        # Rotate Right 4-bit by b[1:0]
        shift = b & 0x3
        ror_res = ((a >> shift) | (a << (4 - shift))) & 0xF if shift > 0 else a

        # XOR
        xor_res = (a ^ b) & 0xF

        # MUX controlled by op[1:0]
        if op == 0:
            result = xor_res
        elif op == 1:
            result = adder_res
        elif op == 2:
            result = ror_res
        else:
            result = 0

        zf = 1 if result == 0 else 0
        return result, zf, cf

    def step(self) -> Dict[str, Any]:
        """Executes a single clock cycle."""
        self.cycle += 1
        current_pc = self.pc
        instr = self.rom[current_pc]
        d = self.decode(instr)

        # Datapath Operands
        operand_a = self.registers[d["rd"]]
        reg_b = self.registers[d["rs"]]
        operand_b = d["imm_val"] if d["imm_sel"] else reg_b

        # ALU Computation
        alu_out, new_zf, new_cf = self.alu(operand_a, operand_b, d["op"])

        # Register Writeback (if REG_EN is active)
        prev_rd_val = self.registers[d["rd"]]
        if d["reg_en"]:
            self.registers[d["rd"]] = alu_out

        # Flag update
        prev_zf, prev_cf = self.zf, self.cf
        self.zf = new_zf
        self.cf = new_cf

        # PC Update (PC Adder vs Mux)
        next_pc = d["target_addr"] if d["jmp_sel"] else ((current_pc + 1) & 0xF)
        self.pc = next_pc

        return {
            "cycle": self.cycle,
            "pc": current_pc,
            "next_pc": next_pc,
            "instr": instr,
            "mnemonic": d["mnemonic"],
            "op_a": operand_a,
            "op_b": operand_b,
            "alu_out": alu_out,
            "reg_written": f"R{d['rd']} ({prev_rd_val} -> {alu_out})" if d["reg_en"] else "None",
            "zf": self.zf,
            "cf": self.cf,
            "jmp_sel": d["jmp_sel"],
            "imm_sel": d["imm_sel"],
            "reg_en": d["reg_en"]
        }

    def print_state_banner(self):
        print("=" * 86)
        print("  CYCLE | PC | INSTR  | MNEMONIC     | OP_A | OP_B | ALU | R0 R1 R2 R3 | ZF CF | NEXT_PC")
        print("=" * 86)

    def print_step(self, s: Dict[str, Any]):
        r_str = f"{self.registers[0]:2d} {self.registers[1]:2d} {self.registers[2]:2d} {self.registers[3]:2d}"
        print(f"  {s['cycle']:5d} | {s['pc']:2d} | 0x{s['instr']:04X} | {s['mnemonic']:12s} | {s['op_a']:4d} | {s['op_b']:4d} | {s['alu_out']:3d} | {r_str} |  {s['zf']}  {s['cf']} |   {s['next_pc']:2d}")


def main():
    parser = argparse.ArgumentParser(description="4-Bit CPU Digital Simulator")
    parser.add_argument("--steps", type=int, default=15, help="Number of clock cycles to simulate (default: 15)")
    parser.add_argument("--rom", type=str, default=None, help="Path to hex/data file for ROM")
    parser.add_argument("--interactive", action="store_true", help="Step through cycles interactively")
    args = parser.parse_args()

    rom_data = None
    if args.rom:
        with open(args.rom, "r") as f:
            tokens = f.read().replace(",", " ").split()
            rom_data = [int(t, 16) if t.startswith(("0x", "0X")) else int(t) for t in tokens]

    cpu = CPU(rom_data)
    print("\n[+] 4-Bit Custom CPU Architecture Simulator")
    print(f"[+] ROM Loaded ({len([x for x in cpu.rom if x != 0])} instructions)")
    print(f"[+] Initial State: PC=0, R0=0, R1=0, R2=0, R3=0, ZF=0, CF=0\n")

    cpu.print_state_banner()

    for _ in range(args.steps):
        s = cpu.step()
        cpu.print_step(s)
        if args.interactive:
            input("Press Enter for next cycle...")

    print("=" * 86)
    print(f"\n[+] Simulation completed ({args.steps} cycles).")
    print(f"[+] Final State: PC={cpu.pc}, Registers: R0={cpu.registers[0]}, R1={cpu.registers[1]}, R2={cpu.registers[2]}, R3={cpu.registers[3]}, ZF={cpu.zf}, CF={cpu.cf}\n")

if __name__ == "__main__":
    main()
