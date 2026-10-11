# 4-Bit Custom CPU Design

A custom 4-bit CPU micro-architecture built and simulated using **HNeemann's Digital** logic simulator. Features a 15-bit instruction word, dual-port RAM/ROM, 4 general-purpose registers, an integrated 4-bit ALU with flags, and a microcoded Control Unit supporting conditional branching.

---

## 🏛 Architecture Overview

- **Datapath Width:** 4-bit (Operands A & B, ALU, Registers, Program Counter)
- **Instruction Width:** 15-bit fixed-length
- **Instruction Memory:** 16-word 15-bit ROM / Dual-Port RAM (Addresses `0x0` to `0xF`)
- **Registers:** 4 General-Purpose Registers (`R0`, `R1`, `R2`, `R3`), 4 bits each
- **Program Counter (PC):** 4-bit synchronous preset counter with sequential increment (`PC + 1`) and branch target multiplexing
- **ALU Operations:** XOR, ADD (Full Adder with Carry-Out), and ROR (Rotate Right by 2-bit shift)
- **Status Flags:**
  - `ZF` (Zero Flag): Set when ALU result is zero (`NOR` of all 4 output bits)
  - `CF` (Carry Flag): Set on arithmetic overflow (`>= 16`) from the 4-bit adder

---

## 📜 15-Bit Instruction Word Format

```
 14        11 10       9 8        7 6                    0
+------------+----------+----------+----------------------+
|   OPCODE   |    Rd    |    Rs    |      Immediate /     |
|   [3:0]    |  (Dest)  |  (Src)   |     Unused bits      |
+------------+----------+----------+----------------------+
|   4 bits   |  2 bits  |  2 bits  |        7 bits        |
```

For Jump Instructions (`JMP`, `JNZ`):
```
 14        11 10                  7 6                    0
+------------+---------------------+----------------------+
|   OPCODE   |    Target Address   |     Unused bits      |
|   [3:0]    |        [3:0]        |                      |
+------------+---------------------+----------------------+
```

---

## 📋 Instruction Set Architecture (ISA)

| Opcode (Hex) | Binary | Mnemonic | Syntax | Operation | Description |
|:---:|:---:|:---|:---|:---|:---|
| `0x0` | `0000` | **XOR** | `XOR Rd, Rs` | `Rd = Rd ^ Rs` | Bitwise XOR of two registers |
| `0x1` | `0001` | **ADD** | `ADD Rd, Rs` | `Rd = Rd + Rs` | 4-bit addition with carry |
| `0x2` | `0010` | **ROR** | `ROR Rd, Rs` | `Rd = ROR(Rd, Rs[1:0])` | Rotate right Rd by Rs |
| `0x4` | `0100` | **XORI** | `XORI Rd, #imm` | `Rd = Rd ^ imm` | Immediate bitwise XOR |
| `0x5` | `0101` | **ADDI** | `ADDI Rd, #imm` | `Rd = Rd + imm` | Immediate addition |
| `0x6` | `0110` | **RORI** | `RORI Rd, #imm` | `Rd = ROR(Rd, imm[1:0])` | Immediate rotate right |
| `0x8` | `1000` | **JMP** | `JMP target` | `PC = target` | Unconditional jump |
| `0x9` | `1001` | **JNZ** | `JNZ target` | `if (ZF == 0) PC = target` | Jump if Not Zero |

### Pseudo-Instructions Supported by Assembler
- `CLR Rd` $\rightarrow$ `XOR Rd, Rd` (Clears register to 0, sets `ZF = 1`)
- `NOP` $\rightarrow$ `XOR R0, R0` (No operation)

---

## ⚙️ Control Unit Logic

| Opcode | Binary | OP[1:0] | IMM_SEL | REG_EN | JMP_SEL (ZF=0) | JMP_SEL (ZF=1) | Function |
|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---|
| 0x0 | 0000 | `00` | 0 | 1 | 0 | 0 | Register XOR |
| 0x1 | 0001 | `01` | 0 | 1 | 0 | 0 | Register ADD |
| 0x2 | 0010 | `10` | 0 | 1 | 0 | 0 | Register ROR |
| 0x4 | 0100 | `00` | 1 | 1 | 0 | 0 | Immediate XOR |
| 0x5 | 0101 | `01` | 1 | 1 | 0 | 0 | Immediate ADD |
| 0x6 | 0110 | `10` | 1 | 1 | 0 | 0 | Immediate ROR |
| 0x8 | 1000 | `00` | 0 | 0 | 1 | 1 | Unconditional Branch |
| 0x9 | 1001 | `01` | 0 | 0 | 1 | 0 | Conditional Branch (Not Zero) |

---

## 🚀 Running on macOS

### Option 1: Terminal CLI Launcher (Digital Simulator)
Open the top-level CPU schematic directly in HNeemann's Digital:
```bash
cd ~/AI-Work/CPU-Design
digital CPU.dig
```
Press **`F5`** (or green Play button) to run the simulation, or press **`C`** to single-step clock pulses.

### Option 2: Terminal Cycle-Accurate Simulator (No GUI Required)
Run the built-in cycle-accurate CPU simulator with formatted live datapath trace:
```bash
python3 cpu_simulator.py --steps 15
```
Interactive step-by-step mode:
```bash
python3 cpu_simulator.py --interactive
```

### Option 3: Two-Pass Assembler
Assemble custom programs into 15-bit machine code and run them immediately:
```bash
python3 assembler.py counter.asm --run
```
To automatically compile and flash the machine code directly into `CPU.dig`'s ROM:
```bash
python3 assembler.py counter.asm --patch
```

---

## 🧪 Automated Verification & Test Suite

Run the full automated test suite (Hardware circuits via Digital CLI + Software Toolchains):
```bash
python3 run_tests.py
```

Output:
```
=================================================================
      4-BIT CPU DESIGN - AUTOMATED HARDWARE & SOFTWARE TESTS
=================================================================

[*] 1. Hardware Circuit Test Benches (Digital Logic Simulator):
  [PASS] 4-bit Full Adder                       -> Passed
  [PASS] Control Unit Decoder                   -> Passed
  [PASS] 4-bit Arithmetic Logic Unit (ALU)      -> Passed

[*] 2. Software Architecture & Toolchain Tests:
  [PASS] Cycle-Accurate CPU Simulator           -> Passed
  [PASS] Two-Pass Assembler & Pipeline Runner   -> Passed

=================================================================
  TOTAL RESULTS: 5/5 Passed (100.0%)
=================================================================
```

---

## 📂 Circuit File Tree

- [`CPU.dig`](CPU.dig): Top-level micro-architecture connecting Datapath, Control Unit, and Memories.
- [`Control Unit.dig`](Control%20Unit.dig): Combinational instruction decoder and branch condition generator.
- [`ALU(4-bit).dig`](ALU(4-bit).dig): 4-bit ALU multiplexing Adder, XOR, and ROR operations with Zero & Carry detection.
- [`Full Adder(4 bit).dig`](Full%20Adder(4%20bit).dig): 4-bit ripple-carry adder.
- [`Full Adder(building Block).dig`](Full%20Adder(building%20Block).dig): 1-bit full adder cell.
- [`ROR(4-bit).dig`](ROR(4-bit).dig): 4-bit barrel rotator (right shift).
- [`XOR Circuit(4-bit).dig`](XOR%20Circuit(4-bit).dig): 4-bit bitwise XOR circuit.
- [`Register Set(4 4-bit Register).dig`](Register%20Set(4%204-bit%20Register).dig): 4-register dual-read/single-write register file (`R0`–`R3`).
- [`Register(4-bit).dig`](Register(4-bit).dig): 4-bit D-flip-flop register cell with enable.
- [`Program Counter.dig`](Program%20Counter.dig): 4-bit instruction pointer.
- [`PC Adder.dig`](PC%20Adder.dig): Incrementer circuit (`PC + 1`).
- [`Flag Register.dig`](Flag%20Register.dig): Status register latching `ZF` and `CF`.
- [`RAM(10x15).dig`](RAM(10x15).dig): Dual-port memory block.