; ============================================================
; 4-Bit CPU Sample Program: Up-Counter with Loop (0 to 5)
; ============================================================
START:
    CLR  R1          ; R1 = 0 (Accumulator)
    ADDI R2, #1      ; R2 = 1 (Step increment)

LOOP:
    ADD  R1, R2      ; R1 = R1 + R2 (Increment counter)
    XORI R3, #5      ; Prepare target value 5
    XOR  R3, R1      ; Compare R1 with 5 (R3 = R3 ^ R1)
    JNZ  LOOP        ; If R3 != 0 (i.e. R1 != 5), jump back to LOOP

HALT:
    JMP  HALT        ; Infinite loop to stop execution
