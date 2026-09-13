grammar MiniExpr;

program
    : statement* EOF
    ;

statement
    : KEEP Identifier SEMI
    | DROP Identifier SEMI
    ;

KEEP: 'keep';
DROP: 'drop';
SEMI: ';';
Identifier: [a-zA-Z_] [a-zA-Z_0-9]*;
WS: [ \t\r\n]+ -> skip;
