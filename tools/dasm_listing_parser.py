import re
import csv

# 6502 Mnemonics & standard dasm pseudo-ops
OPCODES = {
    'ADC', 'AND', 'ASL', 'BCC', 'BCS', 'BEQ', 'BIT', 'BMI', 'BNE', 'BPL',
    'BRK', 'BVC', 'BVS', 'CLC', 'CLD', 'CLI', 'CLV', 'CMP', 'CPX', 'CPY',
    'DEC', 'DEX', 'DEY', 'EOR', 'INC', 'INX', 'INY', 'JMP', 'JSR', 'LDA',
    'LDX', 'LDY', 'LSR', 'NOP', 'ORA', 'PHA', 'PHP', 'PLA', 'PLP', 'ROL',
    'ROR', 'RTI', 'RTS', 'SBC', 'SEC', 'SED', 'SEI', 'STA', 'STX', 'STY',
    'TAX', 'TAY', 'TSX', 'TXA', 'TXS', 'TYA',
    # Pseudo-ops / Directives
    'EQU', 'ORG', 'HEX', 'BYTE', 'BYTE.B', 'WORD', 'WORD.W', 'PROCESSOR',
    'SUBROUTINE', 'INCLUDE', 'DS', 'DC', 'DC.B', 'DC.W', 'MAC', 'MACRO',
    'ENDM', 'ALIGN', 'REND', 'ECHO', 'IF', 'ELSE', 'ENDIF', 'SEG', 'SEG.U'
}


def clean_dasm_listing(input_file, output_file):
    with open(input_file, 'r') as f_in, open(output_file, 'w', newline='') as f_out:
        writer = csv.writer(f_out, delimiter='\t')
        writer.writerow(['Line', 'Address', 'Hex Dump', 'Label', 'Instruction', 'Operand', 'Comment'])

        for line in f_in:
            # Skip dasm file boundary headers or empty lines
            if line.startswith('-------') or not line.strip():
                continue

            # Peel off the comment first to protect internal spacing
            comment = ""
            if ';' in line:
                code_part, comment_part = line.split(';', 1)
                comment = ';' + comment_part
            else:
                code_part = line

            expanded = code_part.expandtabs(8)

            # Find all tokens and their positional data.
            # \S+(?:\s\S+)* captures contiguous text block separated by single spaces
            # (which keeps normal hex dumps like "f0 1f" cleanly together).
            tokens = list(re.finditer(r'\S+(?:\s\S+)*', expanded))

            if not tokens:
                continue

            line_num, address, hex_dump, label, instr, operand = "", "", "", "", "", ""

            # 1. Line Number
            if tokens and tokens[0].group().isdigit():
                line_num = tokens.pop(0).group()

            # 2. Address
            if tokens and re.fullmatch(r'[0-9a-fA-F]{4}', tokens[0].group()):
                address = tokens.pop(0).group()

            # 3. Hex Dump
            # Must be valid hex pairs AND start before column 36 to avoid matching 2-char labels like "A0"
            if tokens and re.fullmatch(r'(?:[0-9a-fA-F]{2}\s*)+\*?', tokens[0].group()) and tokens[0].start() < 36:
                hex_dump = tokens.pop(0).group()

            # 4. Label
            # If the next token isn't a known 6502 opcode, it's a label.
            if tokens and tokens[0].group().upper() not in OPCODES:
                label = tokens.pop(0).group()

            # 5. Instruction
            if tokens:
                instr = tokens.pop(0).group()

            # 6. Operand
            if tokens:
                operand = " ".join([t.group() for t in tokens])

            writer.writerow([line_num, address, hex_dump, label, instr, operand, comment])


clean_dasm_listing('reference/lode_runner_reveng/main.lst', 'reference/lode_runner_reveng/listing_clean.tsv')
