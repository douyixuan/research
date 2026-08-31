#!/usr/bin/env python3
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
out = ROOT / "rtl" / "logic_mutant.v"

# Boolean-equivalent expansion inspired by the paper's logic-operation
# metamorphosis: De Morgan rewrites plus a redundant conjunctive term.
text = r'''module logic_mutant(
    input  wire a,
    input  wire b,
    input  wire c,
    output wire y
);
    wire ab_via_nor = ~(~a | ~b);
    wire ac_via_nor = ~(~a | ~c);
    wire base_expr  = ~(~ab_via_nor & ~ac_via_nor);
    wire redundant  = a & b & c;
    assign y = ~(~base_expr & ~redundant);
endmodule
'''
out.write_text(text)
print(out)
